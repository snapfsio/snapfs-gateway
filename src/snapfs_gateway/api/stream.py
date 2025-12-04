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

import asyncio
import json
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from ..bus import bus
from ..config import settings

router = APIRouter(tags=["stream"])


@router.websocket("/stream")
async def stream_events(
    websocket: WebSocket,
    subject: str = Query(
        ..., description="JetStream subject to consume from, e.g. snapfs.files"
    ),
    durable: str = Query(..., description="Durable consumer name, e.g. mysql or es"),
    batch: int = Query(100, description="Max messages per batch"),
):
    """
    WebSocket bridge between agents and NATS JetStream.

    Agents connect with something like:
        ws://gateway/stream?subject=snapfs.files&durable=mysql&batch=100

    Server flow per connection:
      - Ensure JetStream stream exists for the subject
      - Create or attach to a durable pull consumer
      - Loop:
          - fetch up to `batch` messages
          - send them to the client as a single JSON batch
          - wait for an ACK message referencing the batch ID
          - ACK all JetStream messages in that batch
    """
    await websocket.accept()

    await bus.connect()

    try:
        js = bus.js  # will raise RuntimeError if JetStream is not ready
    except RuntimeError:
        # Tell the client clearly that streaming isn't available
        await websocket.send_json(
            {
                "type": "error",
                "message": "JetStream is not available on the gateway.",
            }
        )
        await websocket.close(code=1011)
        return

    stream_name = settings.nats_stream

    # Ensure stream exists for this subject
    await bus.ensure_stream(stream_name, [subject])

    # Create / attach to durable pull consumer
    try:
        sub = await js.pull_subscribe(
            subject=subject,
            durable=durable,
            stream=stream_name,
        )
    except Exception as e:
        # Log the actual error server-side
        print(
            f"[gateway] Failed to create JetStream consumer for durable={durable!r}: {e!r}"
        )
        # Tell the client what went wrong
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Failed to create JetStream consumer for durable={durable}: {e}",
            }
        )
        await websocket.close(code=1011)
        return

    pending_batches: Dict[str, List] = {}

    try:
        print(f"[gateway] Client connected for subject={subject!r} durable={durable!r}")
        while True:
            # Fetch up to `batch` messages
            try:
                msgs = await sub.fetch(batch=batch, timeout=1.0)
            except Exception:
                msgs = []

            if not msgs:
                # No data available yet, small sleep to avoid tight loop
                await asyncio.sleep(0.5)
                continue

            batch_id = str(uuid.uuid4())
            items = []

            for idx, msg in enumerate(msgs):
                try:
                    payload = msg.data.decode("utf-8")
                    data = json.loads(payload)
                except Exception:
                    # Fallback to raw string if JSON fails
                    data = {"raw": msg.data.decode("utf-8", errors="replace")}

                items.append(
                    {
                        "index": idx,
                        "data": data,
                    }
                )

            # Track msgs so we can ACK them when client acks the batch
            pending_batches[batch_id] = msgs

            # Send batch to client
            await websocket.send_json(
                {
                    "type": "events",
                    "batch": batch_id,
                    "messages": items,
                }
            )

            # Wait for client ACK for this batch
            try:
                ack_msg = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            if not isinstance(ack_msg, dict):
                # Ignore malformed messages, but don't ACK JetStream
                pending_batches.pop(batch_id, None)
                continue

            ack_type = ack_msg.get("type")
            ack_batch = ack_msg.get("batch")

            if ack_type == "ack" and ack_batch == batch_id:
                # ACK all JetStream msgs in this batch
                for m in pending_batches.pop(batch_id, []):
                    try:
                        await m.ack()
                    except Exception:
                        # If ack fails, JetStream will redeliver later
                        pass
            else:
                # Treat anything else as "do not ack"; messages will be redelivered
                pending_batches.pop(batch_id, None)

    except WebSocketDisconnect as e:
        # Client disconnected; unacked messages will be redelivered
        print(f"[gateway] Client durable={durable!r} disconnected from stream: {e}")
        return

    except Exception as e:
        print(f"[gateway] Error in stream for durable={durable!r}: {e!r}")
        await websocket.close(code=1011)
        return
