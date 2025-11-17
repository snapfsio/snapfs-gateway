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
    # placeholder DB URL for later integration with snapfs-agent-mysql
    mysql_url: str = os.getenv("SNAPFS_MYSQL_URL") or None

    # future: JWT secret, token issuer, etc.


settings = Settings()
