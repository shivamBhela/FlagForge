import logging
import re
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.crypto import decrypt_secret
from app.models.base import utc_now
from app.models.organization import Organization
from app.models.project import Project
from app.models.environment import Environment
from app.models.flagsmith import (
    FlagsmithConnection,
    FlagsmithConnectionStatus,
    SyncHistory,
    SyncStatus,
    SyncTrigger,
)
from app.models.feature_flag import (
    FeatureFlag,
    FeatureFlagType,
    FeatureFlagState,
)
from app.services.flagsmith_client import FlagsmithClient, FlagsmithApiError

logger = logging.getLogger("flagsmith-sync")


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)


class FlagsmithSyncEngine:
    """Orchestrates reliable, idempotent synchronization between remote Flagsmith and FlagForge."""

    def __init__(self, db: AsyncSession, connection: FlagsmithConnection):
        self.db = db
        self.connection = connection
        self.conn_id = connection.id
        self.org_id = connection.organization_id
        self.api_url = connection.api_url
        self.encrypted_token = connection.encrypted_token

    async def run_sync(self, trigger: SyncTrigger = SyncTrigger.MANUAL, client: Optional[FlagsmithClient] = None) -> SyncHistory:
        """Executes a full synchronization run, tracking differences and updating history."""
        # 1. Prevent overlapping runs for the same connection
        stmt_active = select(SyncHistory).where(
            SyncHistory.connection_id == self.conn_id,
            SyncHistory.status == SyncStatus.RUNNING,
        )
        active_job = (await self.db.execute(stmt_active)).scalar_one_or_none()
        if active_job:
            logger.warning(f"Sync already running for connection {self.conn_id}")
            return active_job

        # 2. Initialize sync history record
        history = SyncHistory(
            organization_id=self.org_id,
            connection_id=self.conn_id,
            status=SyncStatus.RUNNING,
            trigger=trigger,
            started_at=utc_now(),
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        deleted_count = 0

        try:
            # 3. Setup API Client
            if not client:
                token = decrypt_secret(self.encrypted_token)
                client = FlagsmithClient(base_url=self.api_url, token=token)

            # 4. Fetch remote projects
            remote_projects = await client.get_projects()
            logger.info(f"Discovered {len(remote_projects)} remote projects for org {self.org_id}")

            for rp in remote_projects:
                remote_proj_id = str(rp.get("id"))
                remote_proj_name = rp.get("name", "Unnamed Project")

                # Find or create local Project under this organization
                stmt_proj = select(Project).where(
                    Project.organization_id == self.org_id,
                    (Project.flagsmith_project_id == remote_proj_id) | (Project.name == remote_proj_name),
                )
                local_proj = (await self.db.execute(stmt_proj)).scalar_one_or_none()

                if not local_proj:
                    proj_slug = slugify(remote_proj_name)
                    # Deduplicate slug if necessary
                    cnt = 1
                    base_slug = proj_slug
                    while True:
                        s_check = select(Project).where(
                            Project.organization_id == self.org_id,
                            Project.slug == proj_slug,
                        )
                        if not (await self.db.execute(s_check)).scalar_one_or_none():
                            break
                        proj_slug = f"{base_slug}-{cnt}"
                        cnt += 1

                    local_proj = Project(
                        organization_id=self.org_id,
                        name=remote_proj_name,
                        slug=proj_slug,
                        description=f"Imported from Flagsmith Project {remote_proj_id}",
                        flagsmith_project_id=remote_proj_id,
                    )
                    self.db.add(local_proj)
                    await self.db.flush()
                    created_count += 1
                else:
                    if local_proj.flagsmith_project_id != remote_proj_id:
                        local_proj.flagsmith_project_id = remote_proj_id
                        updated_count += 1
                    else:
                        unchanged_count += 1

                # 5. Fetch and synchronize remote environments for this project
                remote_envs = await client.get_project_environments(remote_proj_id)
                env_map = {}  # remote_api_key -> local Environment

                for re_env in remote_envs:
                    env_api_key = re_env.get("api_key")
                    env_name = re_env.get("name", "Environment")
                    is_prod = "prod" in env_name.lower()

                    stmt_env = select(Environment).where(
                        Environment.project_id == local_proj.id,
                        (Environment.flagsmith_environment_key == env_api_key) | (Environment.name == env_name),
                    )
                    local_env = (await self.db.execute(stmt_env)).scalar_one_or_none()

                    if not local_env:
                        local_env = Environment(
                            project_id=local_proj.id,
                            name=env_name,
                            slug=slugify(env_name),
                            is_production=is_prod,
                            flagsmith_environment_key=env_api_key,
                        )
                        self.db.add(local_env)
                        await self.db.flush()
                        created_count += 1
                    else:
                        if local_env.flagsmith_environment_key != env_api_key:
                            local_env.flagsmith_environment_key = env_api_key
                            updated_count += 1
                        else:
                            unchanged_count += 1

                    env_map[env_api_key] = local_env

                # 6. Fetch and synchronize features for this project
                remote_features = await client.get_project_features(remote_proj_id)
                logger.info(f"Synchronizing {len(remote_features)} features for project {local_proj.name}")

                for rf in remote_features:
                    feature_id = str(rf.get("id"))
                    feature_name = rf.get("name")
                    feature_type_str = rf.get("type", "FLAG")
                    feature_desc = rf.get("description") or ""
                    default_enabled = bool(rf.get("default_enabled", False))

                    flag_type = FeatureFlagType.FLAG
                    if feature_type_str == "CONFIG":
                        flag_type = FeatureFlagType.CONFIG
                    elif feature_type_str == "MULTIVARIATE":
                        flag_type = FeatureFlagType.MULTIVARIATE

                    stmt_flag = select(FeatureFlag).where(
                        FeatureFlag.project_id == local_proj.id,
                        FeatureFlag.key == feature_name,
                    )
                    local_flag = (await self.db.execute(stmt_flag)).scalar_one_or_none()

                    if not local_flag:
                        local_flag = FeatureFlag(
                            project_id=local_proj.id,
                            flagsmith_feature_id=feature_id,
                            name=feature_name,
                            key=feature_name,
                            description=feature_desc,
                            type=flag_type,
                            default_enabled=default_enabled,
                        )
                        self.db.add(local_flag)
                        await self.db.flush()
                        created_count += 1
                    else:
                        # Check for updates
                        changed = False
                        if local_flag.flagsmith_feature_id != feature_id:
                            local_flag.flagsmith_feature_id = feature_id
                            changed = True
                        if local_flag.description != feature_desc:
                            local_flag.description = feature_desc
                            changed = True
                        if local_flag.default_enabled != default_enabled:
                            local_flag.default_enabled = default_enabled
                            changed = True
                        if changed:
                            updated_count += 1
                        else:
                            unchanged_count += 1

                # 7. Synchronize environment feature states
                for env_api_key, local_env in env_map.items():
                    if not env_api_key:
                        continue
                    try:
                        remote_states = await client.get_environment_feature_states(env_api_key)
                    except Exception as e:
                        logger.warning(f"Could not fetch feature states for env {local_env.name}: {e}")
                        continue

                    # Index remote states by feature ID
                    state_by_feature = {s.get("feature"): s for s in remote_states if isinstance(s, dict)}

                    # Query all local flags for this project
                    stmt_all_flags = select(FeatureFlag).where(FeatureFlag.project_id == local_proj.id)
                    all_flags = (await self.db.execute(stmt_all_flags)).scalars().all()

                    for flag in all_flags:
                        rf_id_int = int(flag.flagsmith_feature_id) if flag.flagsmith_feature_id and flag.flagsmith_feature_id.isdigit() else None
                        r_state = state_by_feature.get(rf_id_int)

                        is_enabled = r_state.get("enabled", flag.default_enabled) if r_state else flag.default_enabled
                        val_raw = r_state.get("feature_state_value") if r_state else None
                        val_str = str(val_raw) if val_raw is not None else None
                        fs_id = str(r_state.get("id")) if r_state and r_state.get("id") else None

                        stmt_st = select(FeatureFlagState).where(
                            FeatureFlagState.feature_flag_id == flag.id,
                            FeatureFlagState.environment_id == local_env.id,
                        )
                        local_state = (await self.db.execute(stmt_st)).scalar_one_or_none()

                        if not local_state:
                            local_state = FeatureFlagState(
                                feature_flag_id=flag.id,
                                environment_id=local_env.id,
                                flagsmith_feature_state_id=fs_id,
                                enabled=is_enabled,
                                value=val_str,
                            )
                            self.db.add(local_state)
                            created_count += 1
                        else:
                            if local_state.enabled != is_enabled or local_state.value != val_str:
                                local_state.enabled = is_enabled
                                local_state.value = val_str
                                local_state.flagsmith_feature_state_id = fs_id
                                updated_count += 1
                            else:
                                unchanged_count += 1

            # 8. Mark successful completion
            stmt_conn = select(FlagsmithConnection).where(FlagsmithConnection.id == self.conn_id)
            conn = (await self.db.execute(stmt_conn)).scalar_one_or_none()
            if conn:
                conn.status = FlagsmithConnectionStatus.CONNECTED
                conn.last_synced_at = utc_now()
                conn.last_error = None
                self.db.add(conn)

            history.status = SyncStatus.COMPLETED
            history.records_created = created_count
            history.records_updated = updated_count
            history.records_unchanged = unchanged_count
            history.records_deleted = deleted_count
            history.completed_at = utc_now()

            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(history)
            return history

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Sync failed for connection {self.conn_id}: {str(e)}", exc_info=True)

            stmt_conn = select(FlagsmithConnection).where(FlagsmithConnection.id == self.conn_id)
            conn = (await self.db.execute(stmt_conn)).scalar_one_or_none()
            if conn:
                conn.status = FlagsmithConnectionStatus.ERROR
                conn.last_error = str(e)
                self.db.add(conn)

            stmt_hist = select(SyncHistory).where(SyncHistory.id == history.id)
            hist = (await self.db.execute(stmt_hist)).scalar_one_or_none()
            if hist:
                hist.status = SyncStatus.FAILED
                hist.error_details = str(e)
                hist.completed_at = utc_now()
                self.db.add(hist)

            await self.db.commit()
            if hist:
                await self.db.refresh(hist)
                return hist
            return history
