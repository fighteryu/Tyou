"""
decorators.py

Decorators for URL handlers

"""
from functools import wraps
from flask import redirect, request, abort, g
from application import settings


def login_required(func):
    """Requires standard login credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not users.get_current_user():
            return redirect(users.create_login_url(request.url))
        return func(*args, **kwargs)
    return decorated_view


def admin_required(func):
    """Requires admin credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if users.get_current_user():
            if users.get_current_user().email() != settings.BLOGUSERMAIL:
                abort(401)  # Unauthorized
            return func(*args, **kwargs)
        return redirect(users.create_login_url(request.url))
    return decorated_view
