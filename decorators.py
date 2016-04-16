"""
decorators.py

Decorators for URL handlers

"""
from functools import wraps
from flask import redirect, session


def admin_required(func):
    """Requires admin credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session.get("is_admin", False):
            return func(*args, **kwargs)
        return redirect("/manager/login")
    return decorated_view
