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

import pymysql

from .config import settings


def get_mysql_connection():
    """
    Return a *new* MySQL connection. Gateway does read-only lookups,
    so per-request connections are fine. MySQL can pool internally.
    """
    return pymysql.connect(
        host=settings.mysql_url_parsed.host,
        user=settings.mysql_url_parsed.username,
        password=settings.mysql_url_parsed.password,
        database=settings.mysql_url_parsed.database,
        port=settings.mysql_url_parsed.port or 3306,
        charset="utf8mb4",
        autocommit=True,
    )


def lookup_file_hash(probe):
    """
    Try to find a matching row in MySQL L2 cache.
    Returns (algo, hash) if found, else None.
    """
    sql_base = """
        SELECT algo, hash
        FROM file_cache
        WHERE path = %s
          AND size = %s
          AND mtime = %s
    """

    params = [probe.path, probe.size, int(probe.mtime)]

    # Optionally include inode/dev when present
    # TODO: consider dropping path when inode/dev are present for file moves
    if probe.inode is not None and probe.dev is not None:
        sql = sql_base + " AND inode = %s AND dev = %s LIMIT 1;"
        params.extend([probe.inode, probe.dev])
    else:
        sql = sql_base + " LIMIT 1;"

    conn = get_mysql_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            if not row:
                return None
            algo, hash_hex = row
            if not algo or not hash_hex:
                return None
            return algo, hash_hex
    finally:
        conn.close()
