#!/usr/bin/env python3
"""TCP-проброс 0.0.0.0:8391 -> 127.0.0.1:8390 (вариант А, HTTP без TLS).

Временное решение до nginx (Заказчик: «Nginx позже поставим»). Без socat
и sudo — чистый stdlib. Не для продакшена: HTTP открытым текстом."""
import socket
import threading

LISTEN = ("0.0.0.0", 8391)
TARGET = ("127.0.0.1", 8390)


def pump(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket) -> None:
    upstream = socket.socket()
    upstream.settimeout(10)
    try:
        upstream.connect(TARGET)
    except OSError:
        client.close()
        return
    upstream.settimeout(None)
    t = threading.Thread(target=pump, args=(upstream, client), daemon=True)
    t.start()
    pump(client, upstream)
    upstream.close()


def main() -> None:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(LISTEN)
    srv.listen(64)
    print(f"forwarding {LISTEN[0]}:{LISTEN[1]} -> {TARGET[0]}:{TARGET[1]}", flush=True)
    while True:
        client, _ = srv.accept()
        threading.Thread(target=handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    main()
