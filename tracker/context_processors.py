def role_flags(request):
    """Expose simple role booleans + unread notification count to all templates."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    return {
        # Canonical names
        'is_owner_user': getattr(user, 'is_owner', False),
        'is_area_manager_user': getattr(user, 'is_area_manager', False),
        'is_marketing_executive_user': getattr(user, 'is_marketing_executive', False),
        # Legacy aliases (kept so older templates keep working)
        'is_admin_user': getattr(user, 'is_owner', False),
        'is_manager_user': getattr(user, 'is_area_manager', False),
        'is_salesman_user': getattr(user, 'is_marketing_executive', False),
        'unread_notification_count': user.notifications.filter(is_read=False).count(),
    }
