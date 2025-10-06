"""Event bus abstraction supporting Redis and in-process fallbacks."""
from __future__ import annotations

import json
import os
import queue
import threading
from typing import Iterable, Optional, Tuple

import redis
from flask import Response


class EventBus:
    def publish(self, payload: dict, event_type: str) -> None:
        raise NotImplementedError


class RedisEventBus(EventBus):
    def __init__(self, blueprint):
        self._blueprint = blueprint

    def init_app(self, app) -> None:
        app.register_blueprint(self._blueprint, url_prefix="/stream")

    def publish(self, payload: dict, event_type: str) -> None:
        self._blueprint.publish(payload, type=event_type)


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: set[queue.Queue[Tuple[str, dict]]] = set()

    def init_app(self, app) -> None:
        @app.route("/stream")
        def stream():
            subscriber = self.subscribe()

            def event_stream():
                try:
                    while True:
                        event_type, payload = subscriber.get()
                        yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
                finally:
                    self.unsubscribe(subscriber)

            return Response(event_stream(), mimetype="text/event-stream")

    def subscribe(self) -> queue.Queue[Tuple[str, dict]]:
        q: queue.Queue[Tuple[str, dict]] = queue.Queue()
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, subscriber: queue.Queue[Tuple[str, dict]]) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, payload: dict, event_type: str) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put((event_type, payload))


def _attempt_redis_connection(url: str) -> bool:
    try:
        client = redis.from_url(url)
        client.ping()
        return True
    except Exception:
        return False


def build_event_bus(app) -> EventBus:
    strategy = os.getenv("VIDMELT_EVENT_STRATEGY", "auto").lower()
    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379/0")

    use_redis = False
    if strategy == "redis":
        use_redis = _attempt_redis_connection(redis_url)
    elif strategy == "auto":
        use_redis = _attempt_redis_connection(redis_url)

    if use_redis:
        from flask_sse import sse  # type: ignore

        bus = RedisEventBus(sse)
        bus.init_app(app)
        return bus

    bus = InMemoryEventBus()
    bus.init_app(app)
    return bus
