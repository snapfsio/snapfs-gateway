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

    sql = """
        SELECT algo, hash
        FROM file_cache
        WHERE path = %s
        LIMIT 1;
    """

    # TODO: harden query with inode + dev?
    # leave mtime, dev and size checks to client side for now
    # AND inode = %s
    # AND dev = %s

    conn = get_mysql_connection()
    try:
        with conn.cursor() as cur:
            raw_sql = cur.mogrify(sql, (probe.path))
            cur.execute(raw_sql)
            row = cur.fetchone()
            if not row:
                return None
            algo, hash_hex = row
            if not algo or not hash_hex:
                return None
            return algo, hash_hex
    finally:
        conn.close()
