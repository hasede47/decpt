"""
DECEPTR - Step 1: collection.

Primary flow: Logstash pushes parsed Cowrie JSON events to Redis.
Fallback flow: read recent Cowrie events from Elasticsearch when Redis is empty.
"""
import json
import logging
from pathlib import Path

from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis

from config import (
    COWRIE_INDEX,
    ELASTIC_HOST,
    ELASTIC_PASSWORD,
    ELASTIC_USER,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_QUEUE,
)

log = logging.getLogger("deceptr.collector")

CURSOR_FILE = Path("/app/data/collector_cursor.json")


class Collector:
    def __init__(self):
        self._es = AsyncElasticsearch(
            hosts=[ELASTIC_HOST],
            basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            verify_certs=False,
        )
        self._redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
            socket_timeout=10,
        )
        self._last_ts = self._load_cursor()

    def _load_cursor(self) -> str:
        try:
            if CURSOR_FILE.exists():
                data = json.loads(CURSOR_FILE.read_text())
                return data.get("last_ts", "now-1h")
        except Exception:
            pass
        return "now-1h"

    def _save_cursor(self, ts: str) -> None:
        try:
            CURSOR_FILE.parent.mkdir(parents=True, exist_ok=True)
            CURSOR_FILE.write_text(json.dumps({"last_ts": ts}))
        except Exception as e:
            log.warning(f"Unable to save collector cursor: {e}")

    async def collect(self) -> list[dict]:
        events = await self._collect_redis()
        if events:
            return events
        return await self._collect_elasticsearch()

    async def _collect_redis(self) -> list[dict]:
        events: list[dict] = []
        try:
            for _ in range(500):
                raw = await self._redis.lpop(REDIS_QUEUE)
                if raw is None:
                    break
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    log.warning("Ignored invalid JSON event from Redis")
        except Exception as e:
            log.warning(f"Redis unavailable, falling back to Elasticsearch: {e}")
            return []

        if events:
            log.info(f"[Collecte] {len(events)} events from Redis queue {REDIS_QUEUE}")
        return events

    async def _collect_elasticsearch(self) -> list[dict]:
        try:
            resp = await self._es.search(
                index=COWRIE_INDEX,
                body={
                    "size": 500,
                    "sort": [{"@timestamp": {"order": "asc"}}],
                    "query": {"range": {"@timestamp": {"gt": self._last_ts}}},
                },
            )
        except Exception as e:
            log.error(f"Elasticsearch collection error: {e}")
            return []

        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return []

        last_event_ts = hits[-1]["_source"].get("@timestamp") or hits[-1].get("sort", [self._last_ts])[0]
        self._save_cursor(str(last_event_ts))
        self._last_ts = str(last_event_ts)

        log.info(f"[Collecte] {len(hits)} events from Elasticsearch since {self._last_ts}")
        return [h["_source"] for h in hits]
