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

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..bus import bus
from ..cache_keys import build_cache_key

router = APIRouter(prefix="/cache", tags=["cache"])


class FileProbe(BaseModel):
    path: str
    size: int
    mtime: float
    inode: Optional[int] = None
    dev: Optional[int] = None


class CacheResult(BaseModel):
    status: str  # "HIT" or "MISS"
    algo: Optional[str] = None
    hash: Optional[str] = None


@router.post("/batch", response_model=List[CacheResult])
async def cache_batch(probes: List[FileProbe]):
    """
    Probe the L1 cache for a batch of file metadata records.

    L1 = Redis. For now, we do not fall back to L2 (MySQL); MISS means
    the scanner should hash and send a file.upsert event.
    """
    results: List[CacheResult] = []

    for p in probes:
        key = build_cache_key(
            path=p.path,
            size=p.size,
            mtime=p.mtime,
            inode=p.inode,
            dev=p.dev,
        )
        entry = await bus.cache_get(key)

        if entry and "hash" in entry and "algo" in entry:
            results.append(
                CacheResult(
                    status="HIT",
                    algo=entry["algo"],
                    hash=entry["hash"],
                )
            )
        else:
            results.append(CacheResult(status="MISS"))

    return results
