import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable
from app.config import settings

class EventBus:
    def __init__(self):
        self.kafka_producer = None
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self.recent_events: List[Dict[str, Any]] = []

    async def connect(self):
        if settings.USE_KAFKA:
            try:
                from aiokafka import AIOKafkaProducer
                self.kafka_producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.kafka_producer.start()
                print("Kafka Producer connected successfully.")
            except Exception as e:
                print(f"Kafka connection failed ({e}). Operating with local event bus.")
                self.kafka_producer = None

    async def publish(self, event_type: str, aggregate_id: str, payload: Dict[str, Any]):
        event = {
            "event_id": payload.get("event_id"),
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in recent memory log for UI monitoring
        self.recent_events.append(event)
        if len(self.recent_events) > 100:
            self.recent_events.pop(0)

        # Notify subscribers
        for sub in list(self.subscribers):
            try:
                if asyncio.iscoroutinefunction(sub):
                    await sub(event)
                else:
                    sub(event)
            except Exception as e:
                print(f"Error notifying event subscriber: {e}")

        # Publish to Kafka if available
        if self.kafka_producer:
            try:
                await self.kafka_producer.send_and_wait("salestorm-events", event)
            except Exception as e:
                print(f"Failed to produce Kafka message: {e}")

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        self.subscribers.append(callback)

    def get_recent_events(self) -> List[Dict[str, Any]]:
        return list(reversed(self.recent_events))

event_bus = EventBus()
