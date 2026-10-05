import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import OutboxEvent
from app.event_bus import event_bus

class OutboxService:
    @staticmethod
    async def create_event(
        db: AsyncSession,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> OutboxEvent:
        event_id = str(uuid.uuid4())
        payload_with_meta = {
            **payload,
            "event_id": event_id,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": event_type
        }
        
        event = OutboxEvent(
            event_id=event_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=json.dumps(payload_with_meta),
            published=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        return event

    @staticmethod
    async def publish_pending_events(db: AsyncSession):
        stmt = select(OutboxEvent).where(OutboxEvent.published == False).order_by(OutboxEvent.created_at)
        res = await db.execute(stmt)
        pending = res.scalars().all()
        
        for event in pending:
            payload_data = json.loads(event.payload)
            await event_bus.publish(
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                payload=payload_data
            )
            event.published = True
            event.published_at = datetime.now(timezone.utc)
            
        if pending:
            await db.commit()

outbox_service = OutboxService()
