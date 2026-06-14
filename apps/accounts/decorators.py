from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, "Accès refusé.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def staff_only(view_func):
    return role_required('directeur','banque','caissier','preteur')(view_func)

def directeur_only(view_func):
    return role_required('directeur')(view_func)

def caissier_only(view_func):
    return role_required('directeur','caissier','banque')(view_func)

def preteur_only(view_func):
    return role_required('directeur','preteur','banque')(view_func)
