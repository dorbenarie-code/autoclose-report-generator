from myapp.utils.logger_config import get_logger
from typing import Callable, Any
from functools import wraps
from flask import session, redirect, url_for, flash


def role_required(
    *allowed_roles: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            role = session.get("role", "user")
            if role not in allowed_roles:
                flash(f"🔒 Access denied: {role} not allowed", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return wrapper

    return decorator
