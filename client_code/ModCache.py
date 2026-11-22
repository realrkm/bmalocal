"""Shared client-side data cache with TTL and WebSocket topic invalidation."""
import time
import anvil.js

_CACHE = {}           # key -> {"value": any, "expires_at": float, "topic": str|None}
_TOPIC_KEYS = {}      # topic -> set(key)
_RT_TOKEN = None


def _ensure_realtime_hook():
    """Subscribe ModCache to window.bmaRealtime wildcard events for automatic invalidation."""
    global _RT_TOKEN
    if _RT_TOKEN is not None:
        return
    try:
        rt = getattr(anvil.js.window, "bmaRealtime", None)
        if rt:
            _RT_TOKEN = rt.subscribe("*", _on_realtime_invalidation)
    except Exception:
        pass


def _on_realtime_invalidation(evt):
    if not isinstance(evt, dict):
        return
    topic = evt.get("topic")
    if topic:
        invalidate_topic(topic)


def get_cached(key):
    """Return cached value if present and unexpired, else None."""
    entry = _CACHE.get(key)
    if not entry:
        return None
    if entry["expires_at"] is not None and time.time() > entry["expires_at"]:
        _CACHE.pop(key, None)
        return None
    return entry["value"]


def set_cached(key, value, topic=None, ttl_seconds=300):
    """Store a value in client cache, optionally bound to a WebSocket invalidation topic."""
    _ensure_realtime_hook()
    expires_at = (time.time() + ttl_seconds) if ttl_seconds else None
    _CACHE[key] = {"value": value, "expires_at": expires_at, "topic": topic}
    if topic:
        _TOPIC_KEYS.setdefault(topic, set()).add(key)
    return value


def get_or_fetch(key, fetcher, topic=None, ttl_seconds=300, force_refresh=False):
    """Return fresh cached value or invoke fetcher() and cache the result."""
    if not force_refresh:
        cached = get_cached(key)
        if cached is not None:
            return cached
    value = fetcher()
    return set_cached(key, value, topic=topic, ttl_seconds=ttl_seconds)


def invalidate_key(key):
    """Remove a single cache key."""
    entry = _CACHE.pop(key, None)
    if entry and entry.get("topic"):
        keys = _TOPIC_KEYS.get(entry["topic"])
        if keys:
            keys.discard(key)


def invalidate_topic(topic):
    """Invalidate all cache entries associated with a WebSocket topic."""
    keys = _TOPIC_KEYS.pop(topic, None)
    if not keys:
        return
    for key in keys:
        _CACHE.pop(key, None)


def clear():
    """Clear all cached entries (called on logout)."""
    _CACHE.clear()
    _TOPIC_KEYS.clear()
