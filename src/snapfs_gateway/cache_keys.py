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

from typing import Optional


def build_cache_key(
    *,
    path: str,
    size: int,
    mtime: float,
    inode: Optional[int] = None,
    dev: Optional[int] = None,
) -> str:
    """
    Build a stable cache key for a file probe.

    Prefer (dev, inode, size, mtime) when available to be robust
    against path moves. Fallback to path-based key if inode/dev
    are missing or zero.
    """
    mti = int(mtime)
    if dev and inode:
        return f"snapfs:cache:inode:{dev}:{inode}:{size}:{mti}"
    return f"snapfs:cache:path:{path}:{size}:{mti}"
