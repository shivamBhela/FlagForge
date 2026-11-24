import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.flagsmith import FlagsmithConnection
from app.services.webhook_receiver import WebhookHandler

router = APIRouter()


@router.post("/flagsmith/{connection_id}")
async def receive_flagsmith_webhook(
    connection_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_flagsmith_signature: Optional[str] = Header(None, alias="X-Flagsmith-Signature"),
    x_flagsmith_signature_256: Optional[str] = Header(None, alias="X-Flagsmith-Signature-256"),
):
    """Receives and verifies Flagsmith webhook events, scheduling targeted state synchronization."""
    stmt = select(FlagsmithConnection).where(FlagsmithConnection.id == connection_id)
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flagsmith connection not found",
        )

    signature = x_flagsmith_signature or x_flagsmith_signature_256
    body_bytes = await request.body()

    handler = WebhookHandler(db=db)
    success, message = await handler.handle_flagsmith_webhook(
        connection=connection,
        payload_bytes=body_bytes,
        signature_header=signature,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"ok": True, "message": message}
