from __future__ import annotations

import csv
import io
import json
import logging
import mimetypes
import queue
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .config import Settings
from .poller import InverterPoller
from .storage import Storage


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppContext:
    settings: Settings
    storage: Storage
    poller: InverterPoller


class DashboardServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address: tuple[str, int], context: AppContext) -> None:
        self.context = context
        super().__init__(address, DashboardHandler)


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer
    protocol_version = "HTTP/1.1"
    server_version = "MUSTPowerDesk/0.2"
    sys_version = ""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if path in {"/", "/index.html"}:
                self._serve_static("index.html")
            elif path == "/api/current":
                self._json_response({"data": self.server.context.poller.latest(), "health": self.server.context.poller.health()})
            elif path == "/api/health":
                self._json_response(self.server.context.poller.health())
            elif path == "/healthz":
                health = self.server.context.poller.health()
                status = (
                    HTTPStatus.OK
                    if health.get("status") in {"online", "degraded"}
                    else HTTPStatus.SERVICE_UNAVAILABLE
                )
                self._json_response(health, status)
            elif path == "/api/history":
                self._history(query)
            elif path == "/api/export.csv":
                self._export_csv(query)
            elif path == "/api/events":
                self._events()
            elif path.startswith("/assets/"):
                self._serve_static(path.removeprefix("/assets/"))
            else:
                self._json_response({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except BrokenPipeError:
            pass
        except Exception:
            LOGGER.exception("request failed: %s", self.path)
            if not self.wfile.closed:
                self._json_response({"error": "internal server error"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/index.html"}:
            self._serve_static("index.html", head_only=True)
        elif path.startswith("/assets/"):
            self._serve_static(path.removeprefix("/assets/"), head_only=True)
        else:
            self._json_response({"error": "not found"}, HTTPStatus.NOT_FOUND, head_only=True)

    def _history(self, query: dict[str, list[str]]) -> None:
        end_ts = _query_timestamp(query, "to") or int(time.time())
        range_value = query.get("range", ["24h"])[0]
        start_value = _query_timestamp(query, "from")
        if start_value is None:
            start_value = _range_start(range_value, end_ts, self.server.context.storage)
        if start_value > end_ts:
            raise ValueError("from must be before to")
        period = query.get("period", ["auto"])[0]
        if period == "auto":
            period = _auto_period(end_ts - start_value)
        result = self.server.context.storage.history(start_value, end_ts, period)
        self._json_response(result)

    def _export_csv(self, query: dict[str, list[str]]) -> None:
        end_ts = _query_timestamp(query, "to") or int(time.time())
        range_value = query.get("range", ["24h"])[0]
        start_ts = _query_timestamp(query, "from")
        if start_ts is None:
            start_ts = _range_start(range_value, end_ts, self.server.context.storage)
        period = query.get("period", ["auto"])[0]
        if period == "auto":
            period = _auto_period(end_ts - start_ts)
        result = self.server.context.storage.history(start_ts, end_ts, period)

        output = io.StringIO()
        points = result["points"]
        columns = list(points[0].keys()) if points else ["captured_at"]
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(points)
        payload = output.getvalue().encode("utf-8")
        self._send_bytes(
            payload,
            content_type="text/csv; charset=utf-8",
            disposition=f'attachment; filename="must-inverter-{period}.csv"',
        )

    def _events(self) -> None:
        subscriber = self.server.context.poller.events.subscribe()
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            self.wfile.write(b"retry: 5000\n\n")
            self.wfile.flush()
            latest = self.server.context.poller.latest()
            if latest:
                self._send_event("snapshot", {"data": latest, "health": self.server.context.poller.health()})
            while True:
                try:
                    event = subscriber.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue
                self._send_event(event["type"], {key: value for key, value in event.items() if key != "type"})
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            pass
        finally:
            self.server.context.poller.events.unsubscribe(subscriber)

    def _send_event(self, event_name: str, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        self.wfile.write(f"event: {event_name}\ndata: {payload}\n\n".encode("utf-8"))
        self.wfile.flush()

    def _serve_static(self, relative: str, head_only: bool = False) -> None:
        public_dir = self.server.context.settings.public_dir.resolve()
        requested = (public_dir / relative).resolve()
        try:
            requested.relative_to(public_dir)
        except ValueError:
            self._json_response({"error": "not found"}, HTTPStatus.NOT_FOUND, head_only=head_only)
            return
        if not requested.is_file():
            self._json_response({"error": "not found"}, HTTPStatus.NOT_FOUND, head_only=head_only)
            return
        payload = requested.read_bytes()
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        self._send_bytes(payload, content_type=content_type, head_only=head_only)

    def _json_response(self, payload: object, status: HTTPStatus = HTTPStatus.OK, head_only: bool = False) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _send_bytes(
        self,
        data: bytes,
        *,
        content_type: str,
        disposition: str | None = None,
        head_only: bool = False,
    ) -> None:
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), microphone=()")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )

    def log_message(self, format: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)


def _query_timestamp(query: dict[str, list[str]], key: str) -> int | None:
    value = query.get(key, [None])[0]
    if value is None:
        return None
    try:
        if value.isdigit():
            return int(float(value))
        from datetime import datetime, timezone

        if len(value) == 10:
            return int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"invalid {key} timestamp") from None


def _range_start(range_value: str, end_ts: int, storage: Storage) -> int:
    if range_value == "all":
        oldest = storage.stats()["oldest_at"]
        if oldest:
            from datetime import datetime

            return int(datetime.fromisoformat(oldest.replace("Z", "+00:00")).timestamp())
        return end_ts - 86400
    ranges = {
        "1h": 3600,
        "6h": 6 * 3600,
        "24h": 24 * 3600,
        "7d": 7 * 86400,
        "30d": 30 * 86400,
        "90d": 90 * 86400,
        "1y": 365 * 86400,
    }
    if range_value not in ranges:
        raise ValueError("range must be 1h, 6h, 24h, 7d, 30d, 90d, 1y, or all")
    return end_ts - ranges[range_value]


def _auto_period(seconds: int) -> str:
    if seconds <= 6 * 3600:
        return "minute"
    if seconds <= 3 * 86400:
        return "30m"
    if seconds <= 45 * 86400:
        return "day"
    if seconds <= 180 * 86400:
        return "week"
    return "month"
