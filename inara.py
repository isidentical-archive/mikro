"""A web framework built atop on python's http.server"""

from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from typing import Dict, Callable


@dataclass
class Response:
    """HTTP Response"""

    code: HTTPStatus
    body: str

class Dispatcher(SimpleHTTPRequestHandler):
    """Dispatch HTTP requests to registered services"""
    
    _services: Dict[str, Callable[..., Response]] = {}
