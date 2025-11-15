import json
import logging
from starlette.types import ASGIApp, Receive, Send, Scope

logger = logging.getLogger(__name__)


class DoubleEncodedJSONMiddleware:
    """Middleware to handle double-encoded JSON payloads from frontend.
    
    Some frontend clients may send JSON that's been stringified twice,
    resulting in payloads like '"{\"key\":\"value\"}"' instead of '{"key":"value"}'.
    This middleware detects and corrects such cases.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("latin1")

        if method in ["POST", "PUT", "PATCH"] and content_type:
            body_parts = []
            MAX_DOUBLE_ENCODE_CHECK_SIZE = 1024 * 1024  # 1MB - skip check for large bodies

            async def receive_wrapper():
                message = await receive()
                if message["type"] == "http.request":
                    body_parts.append(message.get("body", b""))

                    if not message.get("more_body", False):
                        body = b"".join(body_parts)
                        
                        # Skip double-encode check for large bodies to avoid memory issues
                        # and potential JSON parsing problems with base64-encoded files
                        if len(body) > MAX_DOUBLE_ENCODE_CHECK_SIZE:
                            logger.debug(f"Skipping double-encode check for large body ({len(body)} bytes)")
                            return message

                        if body:
                            try:
                                decoded = body.decode("utf-8")
                                # Only attempt to parse if it looks like a JSON string (starts with quote)
                                # This avoids expensive parsing for normal JSON payloads
                                if decoded.strip().startswith('"') and decoded.strip().endswith('"'):
                                    parsed = json.loads(decoded)
                                    
                                    # Only process if it's actually a double-encoded string
                                    if isinstance(parsed, str):
                                        try:
                                            # Verify it's valid JSON before re-encoding
                                            inner_parsed = json.loads(parsed)
                                            new_body = json.dumps(inner_parsed).encode("utf-8")
                                            
                                            if b"content-type" in headers and content_type != "application/json":
                                                new_headers = []
                                                for name, value in scope.get("headers", []):
                                                    if name != b"content-type":
                                                        new_headers.append((name, value))
                                                new_headers.append((b"content-type", b"application/json"))
                                                scope["headers"] = new_headers

                                            return {
                                                "type": "http.request",
                                                "body": new_body,
                                                "more_body": False
                                            }
                                        except (json.JSONDecodeError, ValueError):
                                            # Not actually double-encoded JSON, skip processing
                                            pass
                            except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
                                # If parsing fails, pass through original body
                                logger.debug(f"Double-encode check failed: {e}")
                                pass

                return message

            await self.app(scope, receive_wrapper, send)
        else:
            await self.app(scope, receive, send)
