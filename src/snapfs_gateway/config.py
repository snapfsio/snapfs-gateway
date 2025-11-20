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

from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    env: str = os.getenv("SNAPFS_ENV", "dev")

    # L1 cache config
    redis_url: str = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
    default_ttl: int = int(os.getenv("SNAPFS_CACHE_TTL", "604800"))  # 7 days

    # NATS / JetStream config
    nats_url: str = os.getenv("NATS_URL", "nats://localhost:4222")
    # Stream that holds file events, e.g. SNAPS_FILES
    nats_stream: str = os.getenv("SNAPFS_STREAM", "SNAPFS_FILES")

    # Default subject for file events
    default_subject: str = os.getenv("SNAPFS_SUBJECT", "snapfs.files")


settings = Settings()
