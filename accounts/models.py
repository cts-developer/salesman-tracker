from django.contrib.auth.models import AbstractUser
from django.db import models


class Area(models.Model):
    """Geographic / sales area used to organise all data location-wise."""
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g. WEST-01")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Area"
        verbose_name_plural = "Areas"

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    # ------------------------------------------------------------------
    # Roles: Owner > Area Manager > Marketing Executive
    # ------------------------------------------------------------------
    ROLE_OWNER = 'owner'
    ROLE_AREA_MANAGER = 'area_manager'
    ROLE_MARKETING_EXECUTIVE = 'marketing_executive'

    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_AREA_MANAGER, 'Area Manager'),
        (ROLE_MARKETING_EXECUTIVE, 'Marketing Executive'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MARKETING_EXECUTIVE)
    phone = models.CharField(max_length=20, blank=True)
    employee_code = models.CharField(max_length=30, blank=True, unique=False, null=True)
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salesmen', help_text="Primary area assigned to this user"
    )
    manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='team_members',
        limit_choices_to={'role': ROLE_AREA_MANAGER},
        help_text="The Area Manager this Marketing Executive reports to."
    )
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active_employee = models.BooleanField(default=True)
    date_joined_company = models.DateField(null=True, blank=True)

    # -- Canonical role helpers -------------------------------------------------
    @property
    def is_owner(self):
        return self.role == self.ROLE_OWNER or self.is_superuser

    @property
    def is_area_manager(self):
        return self.role == self.ROLE_AREA_MANAGER

    @property
    def is_marketing_executive(self):
        return self.role == self.ROLE_MARKETING_EXECUTIVE

    # -- Legacy aliases kept for backward compatibility with older templates ----
    @property
    def is_admin(self):
        return self.is_owner

    @property
    def is_manager(self):
        return self.is_area_manager

    @property
    def is_salesman(self):
        return self.is_marketing_executive

    @property
    def can_manage_all_users(self):
        return self.is_owner

    @property
    def can_manage_team(self):
        return self.is_owner or self.is_area_manager

    def managed_users_queryset(self):
        """Users this account is allowed to manage (create/edit/remove)."""
        if self.is_owner:
            return User.objects.all()
        if self.is_area_manager:
            return User.objects.filter(manager=self, role=self.ROLE_MARKETING_EXECUTIVE)
        return User.objects.none()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
