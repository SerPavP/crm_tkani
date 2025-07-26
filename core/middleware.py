from django.shortcuts import redirect
from django.urls import reverse

class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            # Allow access to login page
            if request.path == reverse("core:login") or request.path.startswith("/admin/"):
                return None
            # Redirect unauthenticated users to login
            return redirect(reverse("core:login"))

        if request.user.is_superuser:
            return None  # Superuser has full access

        try:
            user_profile = request.user.userprofile
        except:
            # If no profile exists, redirect to login
            return redirect(reverse("core:login"))

        # Define access rules based on roles
        # Admin and Accountant can access most parts except user management (handled by Django admin perms)
        # Warehouse has restricted access

        # Warehouse specific access
        if user_profile.is_warehouse_only:
            allowed_warehouse_paths = [
                "/warehouse/",
                "/core/",
                "/fabrics/",  # Складовщик может просматривать ткани
                "/admin/logout/",
                "/core/logout/",
            ]
            if not any(request.path.startswith(path) for path in allowed_warehouse_paths):
                return redirect("/warehouse/") # Redirect to warehouse dashboard

        # General access for Admin/Accountant
        elif user_profile.role in ["admin", "accountant"]:
            # Allow access to all paths for admin
            if user_profile.role == "admin":
                return None
            # Restrict accountant from user management in admin
            if user_profile.role == "accountant" and "/admin/auth/user/" in request.path:
                return redirect("/core/") # Redirect to home

        return None


