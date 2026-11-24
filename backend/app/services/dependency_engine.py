import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dependency_intelligence import (
    NodeType,
    EdgeType,
    DependencyEdge,
)
from app.models.code_intelligence import FlagReference

logger = logging.getLogger("dependency-engine")


class DependencyEngine:
    """Builds and queries multi-tier dependency relationships across flags, components, and services."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def build_inferred_graph_from_references(self, project_id: Optional[uuid.UUID] = None) -> int:
        """Analyzes static flag references and constructs flag -> component -> service dependency edges."""
        stmt = select(FlagReference).where(FlagReference.organization_id == self.organization_id)
        refs = (await self.db.execute(stmt)).scalars().all()

        created_edges = 0
        for ref in refs:
            # Component name from file path
            comp_name = ref.file_path.split("/")[-1].split(".")[0]
            service_name = "api-service" if ref.file_path.endswith(".py") else "web-storefront"

            # 1. Edge: Flag -> Component
            flag_comp_edge = DependencyEdge(
                organization_id=self.organization_id,
                project_id=project_id,
                source_id=f"flag:{ref.flag_key}",
                source_name=ref.flag_key,
                source_type=NodeType.FLAG,
                target_id=f"comp:{comp_name}",
                target_name=comp_name,
                target_type=NodeType.COMPONENT,
                edge_type=EdgeType.INFERRED,
                confidence=ref.parser_confidence,
                evidence=f"Referenced at {ref.file_path}:{ref.line_number}",
            )

            # 2. Edge: Component -> Service
            comp_svc_edge = DependencyEdge(
                organization_id=self.organization_id,
                project_id=project_id,
                source_id=f"comp:{comp_name}",
                source_name=comp_name,
                source_type=NodeType.COMPONENT,
                target_id=f"svc:{service_name}",
                target_name=service_name,
                target_type=NodeType.SERVICE,
                edge_type=EdgeType.EXPLICIT,
                confidence=1.0,
                evidence=f"File belongs to {service_name}",
            )

            for edge in (flag_comp_edge, comp_svc_edge):
                check_stmt = select(DependencyEdge).where(
                    DependencyEdge.organization_id == self.organization_id,
                    DependencyEdge.source_id == edge.source_id,
                    DependencyEdge.target_id == edge.target_id,
                )
                existing = (await self.db.execute(check_stmt)).scalar_one_or_none()
                if not existing:
                    self.db.add(edge)
                    created_edges += 1

        await self.db.commit()
        return created_edges

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
