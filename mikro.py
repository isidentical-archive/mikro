"""A micro service tool built atop on python's http.server"""

from __future__ import annotations

import argparse
import io
import logging
import socket
import socketserver
import sys
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from http.client import HTTPMessage
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable, Dict


class HTTPMethod(Enum):
    """HTTP methods 
    (see bpo-26380 for why this doesnt included in http package)
    """

    GET = "get"
    POST = "post"
    UNKNOWN = -1


@dataclass
class Response:
    """HTTP Response"""

    code: HTTPStatus
    body: str


@dataclass
class Client:
    """ Connection information """

    host: str
    port: int


@dataclass
class Buffers:
    """ Read and Write buffers """

    read: io.BufferedReader
    write: socketserver._SocketWriter


@dataclass
class RequestInfo:
    """ HTTP Request Details """

    close_connection: bool
    raw_requestline: bytes
    request_version: str
    requestline: str
    path: str


@dataclass
class Request:
    """ HTTP Request """

    socket: socket.socket
    client: Client
    server: socketserver.TCPServer
    buffers: Buffers
    method: HTTPMethod
    request_info: RequestInfo
    headers: HTTPMessage

    @classmethod
    def from_dispatcher(cls, dispatcher):
        client = Client(*dispatcher.client_address)
        buffers = Buffers(dispatcher.rfile, dispatcher.wfile)
        method = getattr(HTTPMethod, dispatcher.command, HTTPMethod.UNKNOWN)
        request_info = RequestInfo(
            close_connection=dispatcher.close_connection,
            raw_requestline=dispatcher.raw_requestline,
            request_version=dispatcher.request_version,
            requestline=dispatcher.requestline,
            path=dispatcher.path,
        )
        return cls(
            dispatcher.connection,
            client,
            dispatcher.server,
            buffers,
            method,
            request_info,
            dispatcher.headers,
        )


class Mikro(BaseHTTPRequestHandler):
    """Dispatch HTTP requests to registered services"""

    _services: Dict[str, Callable[[...], Response]] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def service(cls, path, *args, **kwargs):
        def wrapper(func):
            cls._services[path] = func
            func._extras = args
            for keyword, value in kwargs.items():
                setattr(func, keyword, value)
            return func

        return wrapper

    def do_POST(self):
        self.dispatch(self.path, HTTPMethod.POST)

    def do_GET(self):
        self.dispatch(self.path, HTTPMethod.GET)

    def dispatch(self, path, method):
        handler = self._services.get(path)
        if handler is not None:
            response = handler(Request.from_dispatcher(self))
        else:
            response = Response(HTTPStatus.NOT_FOUND, f"No handler found for {path}")


def serve(
    host="0.0.0.0", port=7676, level_logging=logging.DEBUG, level_handler=logging.DEBUG
):
    with socketserver.TCPServer((host, port), Mikro) as httpd:
        logger = logging.getLogger(__name__)
        logger.setLevel(level_logging)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level_handler)

        formatter = logging.Formatter(
            "[MIKRO] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info("Starting server at %s:%s", *httpd.server_address)
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="MikroCTL - Run/Manage mikro services")

    parser.add_argument("-H", "--host", help="Server host", default="0.0.0.0", type=str)
    parser.add_argument("-P", "--port", help="Server port", default=7676, type=int)
    parser.add_argument(
        "-Ll", "--level-logging", help="Logging level", default=logging.DEBUG, type=int
    )
    parser.add_argument(
        "-Lh",
        "--level-handler",
        help="Standard out handler level",
        default=logging.DEBUG,
        type=int,
    )

    args = parser.parse_args()
    serve(**vars(args))


if __name__ == "__main__":
    main()
