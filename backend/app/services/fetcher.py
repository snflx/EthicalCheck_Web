"""Bounded HTTP fetcher that connects to an already validated public IP."""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urlsplit

from .url_guard import URLRejected, checked_redirect, normalize_url, resolve_public


class FetchError(Exception):
    pass


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port, pinned_ip, timeout):
        super().__init__(host, port, timeout=timeout)
        self.pinned_ip = pinned_ip

    def connect(self):
        self.sock = socket.create_connection((self.pinned_ip, self.port), self.timeout)


class PinnedHTTPSConnection(PinnedHTTPConnection):
    def connect(self):
        raw = socket.create_connection((self.pinned_ip, self.port), self.timeout)
        context = ssl.create_default_context()
        try:
            self.sock = context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def fetch_html(url: str, timeout: int, max_bytes: int) -> tuple[str, str]:
    target = normalize_url(url)
    for redirect_count in range(4):
        parsed = urlsplit(target)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pinned_ip = resolve_public(host)
        conn_type = PinnedHTTPSConnection if parsed.scheme == "https" else PinnedHTTPConnection
        conn = conn_type(host, port, pinned_ip, timeout)
        host_header = f"[{host}]" if ":" in host else host
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        deadline = time.monotonic() + timeout
        try:
            conn.request("GET", path, headers={
                "Host": host_header,
                "User-Agent": "EthicalCheck-Web/1.0 (+public-page-audit)",
                "Accept": "text/html,application/xhtml+xml;q=0.9",
                "Accept-Encoding": "identity",
                "Connection": "close",
            })
            response = conn.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                response.close()
                if not location or redirect_count >= 3:
                    raise FetchError("El sitio excedió el límite de redirecciones.")
                target = checked_redirect(target, location)
                continue
            if response.status < 200 or response.status >= 300:
                raise FetchError(f"El sitio respondió con el estado HTTP {response.status}.")
            content_type = (response.getheader("Content-Type") or "").lower()
            if "html" not in content_type:
                raise FetchError("La dirección no devolvió contenido HTML.")
            content_encoding = (response.getheader("Content-Encoding") or "identity").lower()
            if content_encoding not in {"", "identity"}:
                raise FetchError("El sitio respondió contenido comprimido que no se puede limitar de forma segura.")
            length = response.getheader("Content-Length")
            if length:
                try:
                    if int(length) > max_bytes:
                        raise FetchError("La página supera el tamaño máximo permitido para el análisis.")
                except ValueError:
                    pass
            chunks, received = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise FetchError("El sitio tardó demasiado en responder.")
                if conn.sock:
                    conn.sock.settimeout(remaining)
                chunk = response.read(min(65_536, max_bytes + 1 - received))
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
                if received > max_bytes:
                    raise FetchError("La página supera el tamaño máximo permitido para el análisis.")
            body = b"".join(chunks)
            if not body.strip():
                raise FetchError("El sitio devolvió una página HTML vacía.")
            charset = response.headers.get_content_charset() or "utf-8"
            return target, body.decode(charset, errors="replace")
        except (socket.timeout, TimeoutError) as exc:
            raise FetchError("El sitio tardó demasiado en responder.") from exc
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            raise FetchError("No fue posible conectar de forma segura con el sitio.") from exc
        finally:
            conn.close()
    raise FetchError("El sitio excedió el límite de redirecciones.")
