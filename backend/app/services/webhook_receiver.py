import hashlib
import hmac
import json
import logging
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.flagsmith import FlagsmithConnection, WebhookEvent, WebhookStatus, SyncTrigger
from app.services.flagsmith_sync import FlagsmithSyncEngine

logger = logging.getLogger("webhook-receiver")


def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str], secret: Optional[str]) -> bool:
    """Verifies HMAC-SHA256 signature of a webhook payload against a shared secret."""
    if not secret:
        # If no secret was configured for this connection, allow or check if signature not required
        return True

    if not signature_header:
        return False

    # Extract hex digest if prefixed (e.g. "sha256=...")
    sig = signature_header.strip()
    if sig.startswith("sha256="):
        sig = sig[len("sha256="):]

    expected = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(sig, expected)


class WebhookHandler:
    """Processes incoming Flagsmith webhook notifications and schedules reconciliation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_flagsmith_webhook(
        self,
        connection: FlagsmithConnection,
        payload_bytes: bytes,
        signature_header: Optional[str],
    ) -> Tuple[bool, str]:
        """Validates signature, records the webhook event, and reconciles state."""
        # 1. Verify signature
        is_valid = verify_webhook_signature(
            payload_bytes=payload_bytes,
            signature_header=signature_header,
            secret=connection.webhook_secret,
        )

        try:
            payload_json = json.loads(payload_bytes.decode("utf-8"))
            event_type = payload_json.get("event_type") or payload_json.get("type") or "FLAG_UPDATED"
        except Exception:
            payload_json = {}
            event_type = "UNKNOWN"

        event = WebhookEvent(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            event_type=event_type,
            signature=signature_header,
            payload=json.dumps(payload_json),
            status=WebhookStatus.PROCESSED if is_valid else WebhookStatus.FAILED,
        )
        self.db.add(event)
        await self.db.commit()

        if not is_valid:
            logger.warning(f"Invalid webhook signature for connection {connection.id}")
            return False, "Invalid webhook signature"

        # 2. Trigger targeted synchronization in background
        logger.info(f"Verified webhook event {event_type} received for connection {connection.id}. Initiating sync.")
        sync_engine = FlagsmithSyncEngine(db=self.db, connection=connection)
        await sync_engine.run_sync(trigger=SyncTrigger.WEBHOOK)

        return True, "Webhook processed and synchronization triggered"
