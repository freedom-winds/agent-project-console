"""Shared API utilities."""
from functools import wraps
from typing import Optional

from flask import jsonify, request

from ..services import token_service
from ..services.node_service import ValidationError as NodeValidationError
from ..services.project_service import ValidationError as ProjectValidationError
from ..services.evidence_service import ValidationError as EvidenceValidationError
from ..services.checkpoint_service import ValidationError as CheckpointValidationError


def json_error(message: str, status: int = 400):
    return jsonify({"error": "validation_error", "message": message}), status


def actor_from_request() -> str:
    return request.headers.get("X-APC-Actor") or request.headers.get("X-Actor") or "human"


def auth_required(scopes: Optional[list] = None):
    """Optional auth: if request has Authorization header, validate token. If not, allow as 'human'.
    Used by MCP -> REST flow where MCP must include the token.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            authorization = request.headers.get("Authorization", "")
            token = ""
            if authorization.lower().startswith("bearer "):
                token = authorization.split(" ", 1)[1].strip()
            if token:
                rec = token_service.verify_token(token)
                if not rec:
                    return json_error("invalid token", 401)
                request.environ["apc.token"] = rec
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def handle_validation(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (
            NodeValidationError,
            ProjectValidationError,
            EvidenceValidationError,
            CheckpointValidationError,
        ) as e:
            return json_error(e.message, e.status)
        except ValueError as e:
            return json_error(str(e), 400)
    return wrapper
