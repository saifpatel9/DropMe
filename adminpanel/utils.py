from django.shortcuts import redirect
from functools import wraps
from django.contrib.auth import get_user_model
from adminpanel.models import AdminUser


def admin_login_required(view_func):
    """
    Ensure only admin-capable users can access admin panel views.

    Allowed:
      - AdminUser instances (custom admin model)
      - Passenger User with is_admin / is_staff / is_superuser True

    Everyone else is redirected away.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Not logged in at all → send to admin login
        if not user.is_authenticated:
            return redirect('/panel/login/')

        # Allow custom AdminUser model
        if isinstance(user, AdminUser):
            return view_func(request, *args, **kwargs)

        # Allow passenger users that are marked as admin/staff/superuser
        UserModel = get_user_model()
        if isinstance(user, UserModel) and (
            getattr(user, 'is_admin', False)
            or getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
        ):
            return view_func(request, *args, **kwargs)

        # Any other authenticated user (e.g. passenger) is not allowed in admin
        return redirect('homepage')

    return _wrapped_view
