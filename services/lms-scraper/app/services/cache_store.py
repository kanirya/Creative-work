import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None  # type: ignore

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheStore:
    def __init__(self) -> None:
        self._conn = None
        self._redis: Optional[Redis] = None
        self._db_ready = False

    def _get_conn(self):
        if psycopg2 is None or not settings.database_url:
            return None
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(
                    settings.database_url,
                    cursor_factory=psycopg2.extras.RealDictCursor,
                )
            except Exception:
                logger.exception("PostgreSQL cache connection failed. Continuing without PostgreSQL cache.")
                self._conn = None
        return self._conn

    async def _get_redis(self) -> Optional[Redis]:
        if Redis is None or not settings.redis_url:
            return None
        if self._redis is None:
            try:
                normalized_url = settings.redis_url.strip()
                parsed = urlparse(normalized_url)

                if parsed.scheme and parsed.scheme.startswith("redis"):
                    host = (parsed.hostname or "localhost").strip()
                    port = parsed.port or 6379
                    db = int((parsed.path or "/0").strip("/ ") or "0")
                    password = parsed.password
                    self._redis = Redis(
                        host=host,
                        port=port,
                        db=db,
                        password=password,
                        decode_responses=True,
                    )
                else:
                    host_port = normalized_url.replace("redis://", "").strip().strip("/")
                    host, _, port_str = host_port.partition(":")
                    port = int((port_str or "6379").strip())
                    self._redis = Redis(
                        host=(host or "localhost").strip(),
                        port=port,
                        decode_responses=True,
                    )
            except Exception:
                logger.exception("Redis configuration is invalid. Falling back to PostgreSQL cache only.")
                self._redis = None
        return self._redis

    def _ensure_db(self) -> None:
        if self._db_ready:
            return

        conn = self._get_conn()
        if conn is None:
            return

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS lms_response_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMPTZ NOT NULL,
                    source TEXT NOT NULL DEFAULT 'lms'
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_lms_response_cache_expires_at
                ON lms_response_cache (expires_at)
                """
            )
            conn.commit()
            self._db_ready = True
        except Exception:
            conn.rollback()
            logger.exception("Failed to initialize lms_response_cache table")
        finally:
            cursor.close()

    async def get_json(self, cache_key: str) -> Optional[Any]:
        redis = await self._get_redis()
        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                logger.exception("Redis read failed for cache key %s", cache_key)
                self._redis = None

        conn = self._get_conn()
        if conn is None:
            return None

        self._ensure_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT payload
                FROM lms_response_cache
                WHERE cache_key = %s AND expires_at > NOW()
                """,
                (cache_key,),
            )
            row = cursor.fetchone()
            return row["payload"] if row else None
        except Exception:
            logger.exception("PostgreSQL cache read failed for key %s", cache_key)
            return None
        finally:
            cursor.close()

    async def set_json(self, cache_key: str, payload: Any, source: str = "lms") -> None:
        ttl_seconds = max(settings.cache_ttl_seconds, 60)
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.set(cache_key, json.dumps(payload, default=self._json_default), ex=ttl_seconds)
            except Exception:
                logger.exception("Redis write failed for cache key %s", cache_key)
                self._redis = None

        conn = self._get_conn()
        if conn is None:
            return

        self._ensure_db()
        cursor = conn.cursor()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        try:
            cursor.execute(
                """
                INSERT INTO lms_response_cache (cache_key, payload, expires_at, source)
                VALUES (%s, %s::jsonb, %s, %s)
                ON CONFLICT (cache_key) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = CURRENT_TIMESTAMP,
                    expires_at = EXCLUDED.expires_at,
                    source = EXCLUDED.source
                """,
                (cache_key, json.dumps(payload, default=self._json_default), expires_at, source),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("PostgreSQL cache write failed for key %s", cache_key)
        finally:
            cursor.close()

    async def invalidate_prefix(self, prefix: str) -> None:
        redis = await self._get_redis()
        if redis is not None:
            try:
                keys = await redis.keys(f"{prefix}*")
                if keys:
                    await redis.delete(*keys)
            except Exception:
                logger.exception("Redis cache invalidation failed for prefix %s", prefix)
                self._redis = None

        conn = self._get_conn()
        if conn is None:
            return

        self._ensure_db()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM lms_response_cache WHERE cache_key LIKE %s", (f"{prefix}%",))
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("PostgreSQL cache invalidation failed for prefix %s", prefix)
        finally:
            cursor.close()

    @staticmethod
    def _json_default(value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


_instance: Optional[CacheStore] = None


def get_cache_store() -> CacheStore:
    global _instance
    if _instance is None:
        _instance = CacheStore()
    return _instance
