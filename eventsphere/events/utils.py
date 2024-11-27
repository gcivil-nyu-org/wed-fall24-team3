from django.shortcuts import redirect
from django.urls import reverse
from .models import CreatorProfile, UserProfile


def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse("not_authorized"))
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func


def creator_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not CreatorProfile.objects.filter(creator=request.user).exists():
            return redirect(reverse("not_authorized"))
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func


def user_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not UserProfile.objects.filter(user=request.user).exists():
            return redirect(reverse("not_authorized"))
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func


def admin_or_creator_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if (
            not request.user.is_superuser
            and not CreatorProfile.objects.filter(creator=request.user).exists()
        ):
            return redirect(reverse("not_authorized"))
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func
