"""URL validation and DNS pinning for outbound requests."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit


class URLRejected(ValueError):
    pass


def normalize_url(raw: str) -> str:
    if not isinstance(raw, str) or len(raw) > 2048 or any(ord(c) < 32 for c in raw):
        raise URLRejected("La URL no es válida o excede el límite permitido.")
    try:
        parts = urlsplit(raw.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise URLRejected("Usa una URL pública que comience con http:// o https://.")
        if parts.username is not None or parts.password is not None or "@" in parts.netloc:
            raise URLRejected("No se permiten credenciales dentro de la URL.")
        host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
            raise URLRejected("No se permiten nombres de host locales o internos.")
        port = parts.port
        if port is not None and not (1 <= port <= 65535):
            raise URLRejected("El puerto de la URL no es válido.")
        expected_port = 80 if parts.scheme.lower() == "http" else 443
        if port is not None and port != expected_port:
            raise URLRejected("Solo se permiten los puertos web estándar: 80 para HTTP y 443 para HTTPS.")
        try:
            ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            if "." not in host:
                raise URLRejected("El dominio debe ser público y estar completamente calificado.")
        netloc = f"[{host}]" if ":" in host else host
        return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, URLRejected):
            raise
        raise URLRejected("La URL tiene un formato inválido.") from exc


def resolve_public(host: str) -> str:
    try:
        literal = ipaddress.ip_address(host.strip("[]"))
        candidates = [literal]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise URLRejected("No se pudo resolver el dominio indicado.") from exc
        candidates = []
        for info in infos:
            try:
                candidates.append(ipaddress.ip_address(info[4][0].split("%", 1)[0]))
            except ValueError:
                continue
    if not candidates or any(not address.is_global for address in candidates):
        raise URLRejected("El dominio resuelve a una dirección no pública y fue bloqueado.")
    return str(candidates[0])


def checked_redirect(current: str, location: str) -> str:
    destination = normalize_url(urljoin(current, location))
    parsed = urlsplit(destination)
    resolve_public(parsed.hostname or "")
    return destination
