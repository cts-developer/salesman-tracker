from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Area

admin.site.site_header = "Salesman Tracker Administration"
admin.site.site_title = "Salesman Tracker Admin"
admin.site.index_title = "System Management"


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'state', 'is_active', 'created_at')
    list_filter = ('is_active', 'state')
    search_fields = ('name', 'code', 'city')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'manager', 'area', 'phone', 'is_active_employee', 'is_staff')
    list_filter = ('role', 'area', 'is_active_employee')
    fieldsets = UserAdmin.fieldsets + (
        ('Salesman Tracker Profile', {
            'fields': ('role', 'manager', 'phone', 'employee_code', 'area', 'profile_photo',
                       'is_active_employee', 'date_joined_company')
        }),
    )
