import uuid
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dependency_intelligence import (
    NodeType,
    EdgeType,
    DependencyEdge,
)
from app.models.code_intelligence import FlagReference, Repository

logger = logging.getLogger("dependency-engine")


def infer_service_from_path(file_path: str, repo_name: Optional[str] = None) -> str:
    """Attributes a source file path to an evidence-backed service or UNCLASSIFIED.

    Examines directory hierarchy (services/, apps/, packages/, backend/, frontend/)
    and repository metadata instead of simplistic file extension heuristics.
    """
    parts = [p for p in file_path.replace("\\", "/").strip("/").split("/") if p]
    if not parts:
        return repo_name or "UNCLASSIFIED"

    # Multi-service mono-repo patterns
    for idx, part in enumerate(parts[:-1]):
        if part in ("services", "apps", "packages", "microservices") and idx + 1 < len(parts):
            return parts[idx + 1]

    # Top-level service folder conventions
    top = parts[0].lower()
    if top in ("backend", "frontend", "api", "worker", "gateway", "service", "client", "server"):
        return top

    # Single-service repository attribution
    if repo_name and repo_name not in ("default", "main", "repo", "unknown"):
        return repo_name

    return "UNCLASSIFIED"


def infer_component_from_path(file_path: str) -> str:
    """Extracts a readable component identifier from the source file path."""
    parts = [p for p in file_path.replace("\\", "/").strip("/").split("/") if p]
    if not parts:
        return "UnknownComponent"
    filename = parts[-1]
    base = filename.rsplit(".", 1)[0]
    if len(parts) >= 2 and parts[-2] in ("components", "views", "controllers", "services", "handlers"):
        return f"{parts[-2]}/{base}"
    return base


class DependencyEngine:
    """Builds and queries multi-tier dependency relationships across flags, components, and services."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def build_inferred_graph_from_references(self, project_id: Optional[uuid.UUID] = None) -> int:
        """Analyzes static flag references and constructs flag -> component -> service dependency edges.

        Idempotent: removes obsolete INFERRED edges whose references no longer exist,
        while strictly preserving manual EXPLICIT edges.
        """
        # Fetch references and preload repository metadata for service attribution
        stmt = (
            select(FlagReference)
            .where(FlagReference.organization_id == self.organization_id)
        )
        refs = (await self.db.execute(stmt)).scalars().all()

        # Map repository_id -> repo_name
        repo_stmt = select(Repository).where(Repository.organization_id == self.organization_id)
        repos = (await self.db.execute(repo_stmt)).scalars().all()
        repo_names = {r.id: r.name for r in repos}

        # Build desired inferred edges
        desired_inferred_keys: Set[Tuple[str, str]] = set()
        desired_edges_list: List[DependencyEdge] = []

        for ref in refs:
            repo_name = repo_names.get(ref.repository_id)
            comp_name = infer_component_from_path(ref.file_path)
            service_name = infer_service_from_path(ref.file_path, repo_name)

            flag_id = f"flag:{ref.flag_key}"
            comp_id = f"comp:{comp_name}"
            svc_id = f"svc:{service_name}"

            # 1. Edge: Flag -> Component
            flag_comp_key = (flag_id, comp_id)
            if flag_comp_key not in desired_inferred_keys:
                desired_inferred_keys.add(flag_comp_key)
                desired_edges_list.append(DependencyEdge(
                    organization_id=self.organization_id,
                    project_id=project_id,
                    source_id=flag_id,
                    source_name=ref.flag_key,
                    source_type=NodeType.FLAG,
                    target_id=comp_id,
                    target_name=comp_name,
                    target_type=NodeType.COMPONENT,
                    edge_type=EdgeType.INFERRED,
                    confidence=ref.parser_confidence,
                    evidence=f"Referenced at {ref.file_path}:{ref.line_number}",
                ))

            # 2. Edge: Component -> Service
            comp_svc_key = (comp_id, svc_id)
            if comp_svc_key not in desired_inferred_keys:
                desired_inferred_keys.add(comp_svc_key)
                desired_edges_list.append(DependencyEdge(
                    organization_id=self.organization_id,
                    project_id=project_id,
                    source_id=comp_id,
                    source_name=comp_name,
                    source_type=NodeType.COMPONENT,
                    target_id=svc_id,
                    target_name=service_name,
                    target_type=NodeType.SERVICE,
                    edge_type=EdgeType.INFERRED,
                    confidence=0.90 if service_name != "UNCLASSIFIED" else 0.50,
                    evidence=f"Component path {ref.file_path} mapped to service {service_name}",
                ))

        # Query existing edges in the database
        existing_stmt = select(DependencyEdge).where(
            DependencyEdge.organization_id == self.organization_id
        )
        existing_edges = (await self.db.execute(existing_stmt)).scalars().all()
        existing_keys = {(e.source_id, e.target_id): e for e in existing_edges}

        # Remove obsolete INFERRED edges (do NOT delete EXPLICIT edges)
        for key, edge in existing_keys.items():
            if edge.edge_type == EdgeType.INFERRED and key not in desired_inferred_keys:
                await self.db.delete(edge)

        # Add new inferred edges
        created_count = 0
        for edge in desired_edges_list:
            key = (edge.source_id, edge.target_id)
            if key not in existing_keys:
                self.db.add(edge)
                created_count += 1

        await self.db.commit()
        return created_count

    async def get_graph(self) -> Dict[str, Any]:
        """Returns the full React Flow compatible nodes and edges graph for the organization."""
        stmt = select(DependencyEdge).where(DependencyEdge.organization_id == self.organization_id)
        edges = (await self.db.execute(stmt)).scalars().all()

        nodes_map = {}
        react_flow_edges = []

        for e in edges:
            if e.source_id not in nodes_map:
                nodes_map[e.source_id] = {
                    "id": e.source_id,
                    "name": e.source_name,
                    "type": e.source_type.value,
                }
            if e.target_id not in nodes_map:
                nodes_map[e.target_id] = {
                    "id": e.target_id,
                    "name": e.target_name,
                    "type": e.target_type.value,
                }

            react_flow_edges.append({
                "id": f"e-{e.source_id}->{e.target_id}",
                "source": e.source_id,
                "target": e.target_id,
                "edge_type": e.edge_type.value,
                "confidence": e.confidence,
                "evidence": e.evidence,
            })

        return {
            "nodes": list(nodes_map.values()),
            "edges": react_flow_edges,
        }

    async def calculate_blast_radius(self, flag_key: str) -> Dict[str, Any]:
        """Calculates downstream blast radius: all components, services, and APIs affected if flag_key fails or mutates."""
        graph = await self.get_graph()
        flag_node_id = f"flag:{flag_key}"

        adjacency = {}
        for edge in graph["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            adjacency.setdefault(src, []).append(tgt)

        visited = set()
        queue = [flag_node_id]

        while queue:
            curr = queue.pop(0)
            for nxt in adjacency.get(curr, []):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        affected_nodes = [n for n in graph["nodes"] if n["id"] in visited]
        affected_services = [n["name"] for n in affected_nodes if n["type"] == "SERVICE"]
        affected_components = [n["name"] for n in affected_nodes if n["type"] == "COMPONENT"]

        # Impact score (0-100) based on affected count and depth
        impact_score = min(100.0, len(affected_components) * 15.0 + len(affected_services) * 30.0)

        return {
            "flag_key": flag_key,
            "impact_score": impact_score,
            "affected_components_count": len(affected_components),
            "affected_services_count": len(affected_services),
            "affected_services": affected_services,
            "affected_components": affected_components,
        }
