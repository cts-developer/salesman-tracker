from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def role_required(test_func):
    """Like user_passes_test, but shows a friendly 'access denied' page for
    authenticated users instead of bouncing them back to the login screen."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return render(request, 'tracker/access_denied.html', status=403)
        return wrapped
    return decorator


def is_owner(user):
    return user.is_authenticated and user.is_owner


def is_owner_or_area_manager(user):
    return user.is_authenticated and (user.is_owner or user.is_area_manager)
