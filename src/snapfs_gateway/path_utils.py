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

__doc__ = """
Path utilities for SnapFS gateway.

Canonical form:
- Always forward slashes `/`
- No trailing slash except root
- Collapse duplicate separators
- Remove `.` segments
- Preserve `..` literally (don't try to resolve)
- Handle Windows-style backslashes gracefully
"""

import re


def normalize_path(path: str) -> str:
    """
    Normalize a path string into SnapFS canonical form.

    This is intentionally a *string-level* transform. It does not touch the
    filesystem or resolve symlinks.

    Examples
    --------
    >>> normalize_path(r"C:\\show\\seq\\shot\\image.exr")
    'C:/show/seq/shot/image.exr'

    >>> normalize_path("//server/share//dir/./file.exr")
    '//server/share/dir/file.exr'
    """
    if path is None:
        return None  # type: ignore[return-value]

    if path == "":
        return ""

    # 1) Convert Windows separators to POSIX-style
    path = path.replace("\\", "/")

    # 2) Separate UNC prefix (//server/share) if present so we can safely
    #    collapse remaining duplicate slashes.
    unc_prefix = ""
    rest = path

    if rest.startswith("//"):
        # UNC or "network style" path: //server/share/...
        # Split off `//server/share` as the prefix.
        parts = rest[2:].split("/", 2)  # server, share, remainder?
        if len(parts) >= 2:
            server, share = parts[0], parts[1]
            unc_prefix = f"//{server}/{share}"
            rest = parts[2] if len(parts) == 3 else ""
        # else: something weird like `//foo`; leave as-is below.

    # 3) Collapse multiple slashes in the remainder
    rest = re.sub(r"/{2,}", "/", rest)

    # 4) Split into segments, drop '.' segments, preserve '..'
    segments = []
    for seg in rest.split("/"):
        if seg == "" and segments:
            # interior empty segment, already collapsed above, be defensive
            continue
        if seg == ".":
            continue
        segments.append(seg)

    # 5) Re-join
    if unc_prefix:
        norm = "/".join([unc_prefix] + [s for s in segments if s])
    else:
        norm = "/".join(segments)

        # Preserve leading slash if original had it and we aren't UNC
        if path.startswith("/") and not norm.startswith("/"):
            norm = "/" + norm

    # 6) Strip trailing slash except for root and UNC root
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm.rstrip("/")

    return norm
