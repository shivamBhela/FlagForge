import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cleanup import CleanupPatch, PatchStatus
from app.models.code_intelligence import FlagReference

logger = logging.getLogger("cleanup-studio")


class CleanupStudioEngine:
    """Identifies stale/dead feature flags and generates AST-safe clean-up patch previews."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def list_stale_candidates(self) -> List[Dict[str, Any]]:
        """Identifies flags that have static references but are candidates for elimination."""
        stmt = select(FlagReference).where(FlagReference.organization_id == self.organization_id)
        refs = (await self.db.execute(stmt)).scalars().all()

        stale_map = {}
        for r in refs:
            if r.flag_key not in stale_map:
                stale_map[r.flag_key] = {
                    "flag_key": r.flag_key,
                    "references_count": 0,
                    "files": set(),
                    "reason": "Static references detected. Verify rollout, ownership, and age before cleanup.",
                }
            stale_map[r.flag_key]["references_count"] += 1
            stale_map[r.flag_key]["files"].add(r.file_path)

        return [
            {
                "flag_key": k,
                "references_count": v["references_count"],
                "files_count": len(v["files"]),
                "files": sorted(v["files"]),
                "reason": v["reason"],
            }
            for k, v in stale_map.items()
        ]

    async def generate_patch_preview(self, flag_key: str, file_path: str) -> CleanupPatch:
        """Creates a draft proposal; a real remote diff must be prepared and reviewed before PR creation."""
        patch = CleanupPatch(
            organization_id=self.organization_id,
            flag_key=flag_key,
            file_path=file_path,
            rationale=f"Candidate cleanup for '{flag_key}'. Verify the current flag rollout and review actual source changes before authorizing a PR.",
            diff_preview="No source patch is generated from a synthetic template. Connect an authorized GitHub repository and prepare a diff from the current file.",
            status=PatchStatus.DRAFT,
        )
        self.db.add(patch)
        await self.db.commit()
        await self.db.refresh(patch)
        return patch
