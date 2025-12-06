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
    mtime: int
    inode: Optional[int] = None
    dev: Optional[int] = None


class CacheResult(BaseModel):
    status: str  # "HIT" or "MISS"
    algo: Optional[str] = None
    hash: Optional[str] = None

    # TODO: add mtime, inode, dev size back to response for client validation?
    # mtime: Optional[float] = None
    # size: Optional[int] = None
    # inode: Optional[int] = None
    # dev: Optional[int] = None


@router.post("/batch", response_model=List[CacheResult])
async def cache_batch(probes: List[FileProbe]):
    """
    Probe L1 (Redis). On MISS, probe L2 (MySQL).
    """
    results: List[CacheResult] = []

    # First pass: L1 (Redis)
    misses = []
    for i, p in enumerate(probes):
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
            misses.append((i, p, key))

    # Second pass: L2 (MySQL)
    if misses:
        # lazy import to avoid circulars
        from ..db import lookup_file_hash

        for idx, probe, key in misses:
            hit = lookup_file_hash(probe)
            if not hit:
                continue

            algo, hash_hex = hit

            # Hydrate Redis L1
            await bus.cache_set(key, {"algo": algo, "hash": hash_hex})

            # Flip MISS to HIT
            results[idx] = CacheResult(
                status="HIT",
                algo=algo,
                hash=hash_hex,
            )

    return results
