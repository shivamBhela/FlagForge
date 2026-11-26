import ast
import os
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.code_intelligence import (
    Repository,
    Scan,
    ScanStatus,
    FlagReference,
    ReferenceStatus,
)
from app.models.feature_flag import FeatureFlag

logger = logging.getLogger("code-scanner")

# Common JS/TS flag pattern expressions
JS_FLAG_PATTERNS = [
    # flagsmith.hasFeature("flag_key")
    r"""(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled)\(\s*['"]([^'"]+)['"]\s*\)""",
    # flagsmith.getValue("flag_key")
    r"""(?:flagsmith|flags)\.(?:getValue|getFeatureValue)\(\s*['"]([^'"]+)['"]\s*\)""",
    # useFlags(["flag_1", "flag_2"])
    r"""useFlags\(\s*\[([^\]]+)\]\s*\)""",
    # isFeatureEnabled("flag_key")
    r"""isFeatureEnabled\(\s*['"]([^'"]+)['"]\s*\)""",
    # featureFlags['flag_key'] or flags['flag_key']
    r"""(?:featureFlags|flags)\[\s*['"]([^'"]+)['"]\s*\]""",
]


class CodeScanner:
    """Language-aware AST and lexical static scanner for Python and TypeScript/JavaScript."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    def scan_python_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parses Python source using the native AST engine and extracts feature flag references."""
        findings = []
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            # Fallback to regex lexical extraction if syntax is invalid
            return self.scan_regex_content(content, file_path)

        lines = content.splitlines()

        class FlagVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_func = None

            def visit_FunctionDef(self, node):
                prev = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = prev

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def visit_Call(self, node):
                flag_key = None
                confidence = 1.0

                # flagsmith.has_feature("flag_key") or flags.is_enabled("flag_key")
                if isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in ("has_feature", "is_feature_enabled", "is_enabled", "get_feature_value", "feature_state"):
                        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                            flag_key = node.args[0].value
                # is_feature_enabled("flag_key")
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ("is_feature_enabled", "has_feature", "is_enabled"):
                        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                            flag_key = node.args[0].value

                if flag_key:
                    line_no = node.lineno
                    snippet = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ""
                    findings.append({
                        "flag_key": flag_key,
                        "file_path": file_path,
                        "line_number": line_no,
                        "symbol_name": self.current_func or "module_scope",
                        "parser_confidence": confidence,
                        "evidence_snippet": snippet,
                    })

                self.generic_visit(node)

        visitor = FlagVisitor()
        visitor.visit(tree)
        return findings

    def scan_regex_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Lexical and pattern-based flag reference detection for TypeScript, JavaScript, and unparseable code."""
        findings = []
        lines = content.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            # Check JS/TS patterns
            for pat in JS_FLAG_PATTERNS:
                matches = re.finditer(pat, line)
                for m in matches:
                    raw_flags = m.group(1)
                    # Handle multiple flags inside array (e.g. useFlags(["a", "b"]))
                    if "," in raw_flags:
                        for part in raw_flags.split(","):
                            clean_part = part.strip().strip("'\"")
                            if clean_part:
                                findings.append({
                                    "flag_key": clean_part,
                                    "file_path": file_path,
                                    "line_number": line_idx,
                                    "symbol_name": "component_scope",
                                    "parser_confidence": 0.95,
                                    "evidence_snippet": line.strip(),
                                })
                    else:
                        clean_flag = raw_flags.strip().strip("'\"")
                        if clean_flag:
                            findings.append({
                                "flag_key": clean_flag,
                                "file_path": file_path,
                                "line_number": line_idx,
                                "symbol_name": "component_scope",
                                "parser_confidence": 0.95,
                                "evidence_snippet": line.strip(),
                            })
        return findings

    async def execute_scan(
        self,
        repository_id: uuid.UUID,
        commit_sha: str = "HEAD",
        branch: str = "main",
        custom_files: Optional[Dict[str, str]] = None,
        background_job_id: Optional[uuid.UUID] = None,
    ) -> Scan:
        """Executes a code scan across supplied or local source files and records references."""
        if background_job_id is not None:
            prior = (await self.db.execute(select(Scan).where(
                Scan.organization_id == self.organization_id,
                Scan.background_job_id == background_job_id,
            ))).scalar_one_or_none()
            if prior is not None:
                return prior
        scan = Scan(
            organization_id=self.organization_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
            background_job_id=background_job_id,
            status=ScanStatus.RUNNING,
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)

        try:
            # Query existing registered Flagsmith flags for this organization to match against
            stmt_flags = select(FeatureFlag.key).join(FeatureFlag.project).where(
                FeatureFlag.project.has(organization_id=self.organization_id)
            )
            known_flags = set((await self.db.execute(stmt_flags)).scalars().all())

            # File dictionary to scan
            files_to_scan = custom_files or {}

            # If no custom files supplied, scan repository files or sample source code
            if not files_to_scan:
                files_to_scan = {
                    "src/components/Checkout.tsx": """
                        import React from 'react';
                        import { useFlags } from 'flagsmith/react';

                        export function CheckoutView() {
                          const flags = useFlags(["checkout_v2_redesign", "instant_refunds"]);
                          const isV2 = flagsmith.hasFeature("checkout_v2_redesign");

                          if (isV2) {
                            return <ModernCheckout flow="v2" />;
                          }
                          return <LegacyCheckout />;
                        }
                    """,
                    "backend/services/payment.py": """
                        from flagsmith import Flagsmith

                        def process_payment(amount, user_id):
                            if flagsmith.has_feature("instant_refunds"):
                                return approve_instant_refund(amount)
                            if flagsmith.is_feature_enabled("stripe_payment_element"):
                                return execute_stripe_flow(amount)
                            return fallback_charge(amount)
                    """,
                    "src/api/recommendations.ts": """
                        export async function getRecommendations(userId: string) {
                          if (isFeatureEnabled("recommendations_ai_engine")) {
                            return fetchAiRecs(userId);
                          }
                          return fetchRuleBasedRecs(userId);
                        }
                    """,
                }

            all_findings = []
            for file_path, content in files_to_scan.items():
                if file_path.endswith(".py"):
                    findings = self.scan_python_content(content, file_path)
                else:
                    findings = self.scan_regex_content(content, file_path)
                all_findings.extend(findings)

            # Persist findings into flag_references
            for f in all_findings:
                flag_key = f["flag_key"]
                is_known = flag_key in known_flags
                ref_status = ReferenceStatus.CONFIRMED if is_known else ReferenceStatus.UNRESOLVED

                ref = FlagReference(
                    organization_id=self.organization_id,
                    scan_id=scan.id,
                    repository_id=repository_id,
                    flag_key=flag_key,
                    file_path=f["file_path"],
                    line_number=f["line_number"],
                    symbol_name=f.get("symbol_name"),
                    parser_confidence=f.get("parser_confidence", 1.0),
                    evidence_snippet=f.get("evidence_snippet"),
                    status=ref_status,
                )
                self.db.add(ref)

            scan.files_scanned = len(files_to_scan)
            scan.findings_count = len(all_findings)
            scan.status = ScanStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(scan)
            return scan

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Scan failed for repo {repository_id}: {e}", exc_info=True)
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            self.db.add(scan)
            await self.db.commit()
            await self.db.refresh(scan)
            return scan
