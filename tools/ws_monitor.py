#!/usr/bin/env python3
"""Continuously monitor TankCtl live events over WebSocket.

This uses only the Python standard library so it can run without adding a
client dependency. It keeps the WebSocket open, prints incoming events, sends a
small text heartbeat periodically, and reconnects automatically on failure.

Examples:
  python tools/ws_monitor.py
  python tools/ws_monitor.py --url ws://192.168.1.100:8000/ws
  python tools/ws_monitor.py --device tank1
  python tools/ws_monitor.py --event telemetry_received --pretty
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import socket
import ssl
import struct
import sys
import time
from datetime import datetime
from threading import Event, Lock, Thread
from typing import Any
from urllib.parse import urlparse


DEFAULT_URL = os.environ.get("TANKCTL_WS_URL", "ws://192.168.1.100:8000/ws")


class WebSocketError(Exception):
    """Base error for monitor failures."""


class RawWebSocketClient:
    """Very small WebSocket client for monitoring server text events."""

    def __init__(self, url: str, timeout: float = 10.0) -> None:
        self.url = url
        self.timeout = timeout
        self.socket: socket.socket | ssl.SSLSocket | None = None
        self._send_lock = Lock()

    def connect(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"ws", "wss"}:
            raise WebSocketError(f"Unsupported scheme: {parsed.scheme}")

        host = parsed.hostname
        if not host:
            raise WebSocketError("Missing host in URL")

        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        raw_socket = socket.create_connection((host, port), timeout=self.timeout)
        raw_socket.settimeout(self.timeout)

        if parsed.scheme == "wss":
            context = ssl.create_default_context()
            self.socket = context.wrap_socket(raw_socket, server_hostname=host)
        else:
            self.socket = raw_socket

        key = base64.b64encode(os.urandom(16)).decode()
        host_header = host if parsed.port is None else f"{host}:{port}"
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode())

        response = self._read_http_headers()
        if "101 Switching Protocols" not in response:
            raise WebSocketError(f"Handshake failed:\n{response}")

    def close(self) -> None:
        if not self.socket:
            return

        try:
            self.send_close()
        except Exception:
            pass

        try:
            self.socket.close()
        finally:
            self.socket = None

    def send_text(self, text: str) -> None:
        self._send_frame(opcode=0x1, payload=text.encode("utf-8"))

    def send_pong(self, payload: bytes = b"") -> None:
        self._send_frame(opcode=0xA, payload=payload)

    def send_close(self) -> None:
        self._send_frame(opcode=0x8, payload=b"")

    def receive_frame(self) -> tuple[int, bytes]:
        first, second = self._recv_exact(2)
        opcode = first & 0x0F
        payload_length = second & 0x7F
        masked = bool(second & 0x80)

        if payload_length == 126:
            payload_length = struct.unpack("!H", self._recv_exact(2))[0]
        elif payload_length == 127:
            payload_length = struct.unpack("!Q", self._recv_exact(8))[0]

        masking_key = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(payload_length) if payload_length else b""

        if masked:
            payload = bytes(
                byte ^ masking_key[index % 4]
                for index, byte in enumerate(payload)
            )

        return opcode, payload

    def _read_http_headers(self) -> str:
        assert self.socket is not None
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise WebSocketError("Socket closed during handshake")
            data += chunk
        return data.decode("utf-8", "replace")

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        assert self.socket is not None
        with self._send_lock:
            first_byte = 0x80 | opcode
            mask_bit = 0x80
            payload_length = len(payload)

            header = bytearray([first_byte])
            if payload_length <= 125:
                header.append(mask_bit | payload_length)
            elif payload_length <= 65535:
                header.append(mask_bit | 126)
                header.extend(struct.pack("!H", payload_length))
            else:
                header.append(mask_bit | 127)
                header.extend(struct.pack("!Q", payload_length))

            masking_key = os.urandom(4)
            header.extend(masking_key)
            masked_payload = bytes(
                byte ^ masking_key[index % 4]
                for index, byte in enumerate(payload)
            )

            self.socket.sendall(bytes(header) + masked_payload)

    def _recv_exact(self, size: int) -> bytes:
        assert self.socket is not None
        data = b""
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                raise WebSocketError("Socket closed while reading frame")
            data += chunk
        return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="WebSocket URL")
    parser.add_argument("--device", help="Only print events for one device_id")
    parser.add_argument("--event", help="Only print one event type")
    parser.add_argument(
        "--heartbeat-seconds",
        type=float,
        default=20.0,
        help="How often to send a text heartbeat to keep the socket active",
    )
    parser.add_argument(
        "--reconnect-seconds",
        type=float,
        default=3.0,
        help="Base reconnect delay after disconnect",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON payloads",
    )
    return parser.parse_args()


def should_print(payload: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.device and payload.get("device_id") != args.device:
        return False
    if args.event and payload.get("event") != args.event:
        return False
    return True


def format_message(payload: dict[str, Any], pretty: bool) -> str:
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, (int, float)):
        iso_ts = datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")
    else:
        iso_ts = datetime.now().isoformat(timespec="seconds")

    if pretty:
        body = json.dumps(payload, indent=2, sort_keys=True)
    else:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    return f"[{iso_ts}] {body}"


def heartbeat_loop(client: RawWebSocketClient, stop_event: Event, interval: float) -> None:
    while not stop_event.wait(interval):
        try:
            client.send_text("heartbeat")
        except Exception:
            return


def monitor(args: argparse.Namespace) -> int:
    stop_event = Event()

    try:
        attempt = 0
        while True:
            attempt += 1
            client = RawWebSocketClient(args.url)
            heartbeat_stop = Event()
            heartbeat_thread: Thread | None = None

            try:
                print(f"Connecting to {args.url} (attempt {attempt})...", flush=True)
                client.connect()
                print("Connected. Monitoring events...", flush=True)

                heartbeat_thread = Thread(
                    target=heartbeat_loop,
                    args=(client, heartbeat_stop, args.heartbeat_seconds),
                    daemon=True,
                )
                heartbeat_thread.start()

                while not stop_event.is_set():
                    opcode, payload = client.receive_frame()

                    if opcode == 0x1:
                        text = payload.decode("utf-8", "replace")
                        try:
                            data = json.loads(text)
                        except json.JSONDecodeError:
                            print(f"[text] {text}", flush=True)
                            continue

                        if should_print(data, args):
                            print(format_message(data, args.pretty), flush=True)
                    elif opcode == 0x8:
                        raise WebSocketError("Server sent close frame")
                    elif opcode == 0x9:
                        client.send_pong(payload)
                    elif opcode == 0xA:
                        continue
                    else:
                        print(f"[info] Ignoring opcode {opcode}", flush=True)

            except KeyboardInterrupt:
                print("Stopping monitor.", flush=True)
                return 0
            except Exception as exc:
                print(f"Connection lost: {exc}", flush=True)
                delay = args.reconnect_seconds + random.uniform(0, 1.0)
                print(f"Reconnecting in {delay:.1f}s...", flush=True)
                time.sleep(delay)
            finally:
                heartbeat_stop.set()
                if heartbeat_thread is not None:
                    heartbeat_thread.join(timeout=1)
                client.close()
    except KeyboardInterrupt:
        print("Stopping monitor.", flush=True)
        return 0


def main() -> int:
    args = parse_args()
    return monitor(args)


if __name__ == "__main__":
    sys.exit(main())