from functools import wraps
from django.shortcuts import redirect

def driver_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('driver_id'):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view