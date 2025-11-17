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

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

# later we'll import snapfs_agent_mysql.query here

router = APIRouter(prefix="/query", tags=["query"])


class SqlQuery(BaseModel):
    sql: str
    params: Optional[Dict[str, Any]] = None


class SqlResult(BaseModel):
    rows: List[Dict[str, Any]]


@router.post("/sql", response_model=SqlResult)
async def query_sql(body: SqlQuery):
    """
    Execute a raw SQL query against the SnapFS backing store.

    For now this is a stub that returns an empty result set.
    Later, this will delegate to snapfs-agent-mysql (or similar).
    """
    # TODO: use snapfs-agent-mysql.query.run_sql(body.sql, body.params)
    rows: List[Dict[str, Any]] = []
    return SqlResult(rows=rows)
