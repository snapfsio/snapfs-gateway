#!/usr/bin/env python3
#
# Copyright (c) 2025 SnapFS, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from typing import Any, Dict, List, Optional

import nats
from nats.js.api import StreamConfig
from nats.js.errors import APIError as JSAPIError
from redis import asyncio as aioredis

from .config import settings

logger = logging.getLogger(__name__)


class Bus:
    """
    Shared infra access:
    - Redis (L1 cache)
    - MySQL (L2 cache) -- see db.py
    - NATS + JetStream (event log)
    """

    def __init__(self):
        self._redis = None
        self._nats = None
        self._js = None

    async def connect(self):
        # Redis
        if settings.redis_url and self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

        # NATS + JetStream
        if self._nats is None:
            try:
                self._nats = await nats.connect(settings.nats_url)
                self._js = self._nats.jetstream()
                logger.info("Connected to NATS at %s", settings.nats_url)
            except Exception as e:
                # NATS not available; keep running without it.
                logger.warning("Failed to connect to NATS (%s); JetStream disabled.", e)
                self._nats = None
                self._js = None

    @property
    def redis(self):
        return self._redis

    @property
    def nats(self):
        if self._nats is None:
            raise RuntimeError("NATS not connected")
        return self._nats

    @property
    def js(self):
        if self._js is None:
            raise RuntimeError("JetStream not initialized")
        return self._js

    # ------------------------
    # Redis cache helpers
    # ------------------------

    async def cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self._redis:
            return None
        val = await self._redis.get(key)
        if not val:
            return None
        return json.loads(val)

    async def cache_set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = settings.default_ttl):
        if not self._redis:
            return
        await self._redis.set(key, json.dumps(value), ex=ttl)

    # ------------------------
    # JetStream helpers
    # ------------------------

    async def ensure_stream(self, stream: str, subjects: List[str]):
        """
        Make sure a JetStream stream exists for the given subjects.
        If NATS/JetStream is unavailable, this becomes a no-op.
        """
        await self.connect()
        if self._js is None:
            return

        try:
            await self.js.stream_info(stream)
        except JSAPIError:
            cfg = StreamConfig(
                name=stream,
                subjects=subjects,
            )
            await self.js.add_stream(cfg)

    async def publish_events(
        self,
        subject: str,
        events: List[Dict[str, Any]],
        stream: Optional[str] = None,
    ):
        """
        Publish a list of events to JetStream under `subject`.

        If NATS/JetStream is unavailable, this is a no-op (Redis L1 still works).
        """
        await self.connect()
        if self._js is None:
            logger.warning(
                "publish_events called but JetStream is not available; skipping publish."
            )
            return

        stream_name = stream or settings.nats_stream
        await self.ensure_stream(stream_name, [subject])

        payload = json.dumps({"events": events}).encode("utf-8")
        await self.js.publish(subject, payload)


bus = Bus()
