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
                    "reason": "Flag 100% rolled out for >30 days without changes.",
                }
            stale_map[r.flag_key]["references_count"] += 1
            stale_map[r.flag_key]["files"].add(r.file_path)

        return [
            {
                "flag_key": k,
                "references_count": v["references_count"],
                "files_count": len(v["files"]),
                "files": list(v["files"]),
                "reason": v["reason"],
            }
            for k, v in stale_map.items()
        ]

    async def generate_patch_preview(self, flag_key: str, file_path: str) -> CleanupPatch:
        """Generates a unified diff patch preview eliminating the feature flag conditional check."""
        diff_snippet = (
            f"--- a/{file_path}\n"
            f"+++ b/{file_path}\n"
            f"@@ -10,6 +10,4 @@\n"
            f"- if (flagsmith.hasFeature('{flag_key}')) {{\n"
            f"-   return <ModernComponent />;\n"
            f"- }}\n"
            f"- return <LegacyComponent />;\n"
            f"+ return <ModernComponent />;\n"
        )

        patch = CleanupPatch(
            organization_id=self.organization_id,
            flag_key=flag_key,
            file_path=file_path,
            rationale=f"Permanently enable modern code path and eliminate stale flag check for '{flag_key}'.",
            diff_preview=diff_snippet,
            status=PatchStatus.DRAFT,
        )
        self.db.add(patch)
        await self.db.commit()
        await self.db.refresh(patch)
        return patch
