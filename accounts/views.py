from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from .decorators import role_required, is_owner_or_area_manager
from .forms import (
    OwnerUserCreateForm, OwnerUserUpdateForm,
    AreaManagerExecutiveCreateForm, AreaManagerExecutiveUpdateForm,
)
from .models import User


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')


# ---------------------------------------------------------------------------
# User management
#   - Owner: manage ALL users (any role)
#   - Area Manager: manage (add/update/remove) only their own team of
#     Marketing Executives
#   - Marketing Executive: no access to user management at all
# ---------------------------------------------------------------------------

@role_required(is_owner_or_area_manager)
def user_list(request):
    users = request.user.managed_users_queryset().select_related('area', 'manager')
    return render(request, 'accounts/user_list.html', {'users': users})


@role_required(is_owner_or_area_manager)
def user_create(request):
    if request.user.is_owner:
        form_class = OwnerUserCreateForm
        form_kwargs = {}
    else:
        form_class = AreaManagerExecutiveCreateForm
        form_kwargs = {'manager_user': request.user}

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, **form_kwargs)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created.")
            return redirect('accounts:user_list')
    else:
        form = form_class(**form_kwargs)

    title = "Add User" if request.user.is_owner else "Add Marketing Executive"
    return render(request, 'accounts/user_form.html', {'form': form, 'title': title})


@role_required(is_owner_or_area_manager)
def user_edit(request, pk):
    target = get_object_or_404(request.user.managed_users_queryset(), pk=pk)
    form_class = OwnerUserUpdateForm if request.user.is_owner else AreaManagerExecutiveUpdateForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{target.username}' updated.")
            return redirect('accounts:user_list')
    else:
        form = form_class(instance=target)

    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit {target.username}'})


@role_required(is_owner_or_area_manager)
def user_delete(request, pk):
    target = get_object_or_404(request.user.managed_users_queryset(), pk=pk)
    if request.method == 'POST':
        username = target.username
        target.delete()
        messages.success(request, f"User '{username}' removed.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'target': target})
