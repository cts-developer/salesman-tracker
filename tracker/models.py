from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import Area, User


# ---------------------------------------------------------------------------
# Brands & Products
# ---------------------------------------------------------------------------

class Brand(models.Model):
    OWN = 'own'
    COMPETITOR = 'competitor'
    BRAND_TYPE_CHOICES = [(OWN, 'Our Brand'), (COMPETITOR, 'Competitor Brand')]

    STRENGTH_WEAK = 'weak'
    STRENGTH_MODERATE = 'moderate'
    STRENGTH_STRONG = 'strong'
    STRENGTH_CHOICES = [
        (STRENGTH_WEAK, 'Weak'),
        (STRENGTH_MODERATE, 'Moderate'),
        (STRENGTH_STRONG, 'Strong'),
    ]

    name = models.CharField(max_length=120, unique=True)
    brand_type = models.CharField(max_length=12, choices=BRAND_TYPE_CHOICES, default=OWN)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # ---- Competitor details (relevant when brand_type == COMPETITOR) ----
    contact_person = models.CharField(max_length=120, blank=True, help_text="Competitor's local rep/contact, if known.")
    contact_phone = models.CharField(max_length=20, blank=True)
    market_strength = models.CharField(max_length=10, choices=STRENGTH_CHOICES, blank=True)
    notes = models.TextField(blank=True, help_text="Market intel / notes about this competitor.")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_competitor(self):
        return self.brand_type == self.COMPETITOR


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=60, blank=True)
    category = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['brand__name', 'name']
        unique_together = ('brand', 'name')

    def __str__(self):
        return f"{self.name} ({self.brand.name})"


# ---------------------------------------------------------------------------
# Dealers — "Dealer" and "Counter" are the same thing in this system.
# A Dealer record represents the shop/counter itself.
# ---------------------------------------------------------------------------

class Dealer(models.Model):
    """A dealer/counter/shop — the single entity used everywhere a
    'dealer' or 'counter' used to be referenced separately."""

    COUNTER_TYPE_CHOICES = [
        ('retail', 'Retail Shop'),
        ('wholesale', 'Wholesale Counter'),
        ('hardware', 'Hardware Store'),
        ('showroom', 'Showroom'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='dealers')
    address = models.TextField(blank=True)
    counter_type = models.CharField(max_length=20, choices=COUNTER_TYPE_CHOICES, default='retail')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    brands_dealt = models.ManyToManyField(Brand, blank=True, related_name='dealers')
    products_dealt = models.ManyToManyField(Product, blank=True, related_name='dealers')
    assigned_salesmen = models.ManyToManyField(User, blank=True, related_name='assigned_dealers')
    gst_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dealers_created')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tracker:dealer_detail', args=[self.pk])

    @property
    def status(self):
        return 'active' if self.is_active else 'inactive'

    def get_status_display(self):
        return 'Active' if self.is_active else 'Inactive'

    @property
    def total_visits(self):
        return self.visits.count()

    @property
    def total_turnover(self):
        agg = self.turnovers.aggregate(total=models.Sum('amount'))
        return agg['total'] or 0

    # -- Turnover comparison helpers (in-house vs competitor) --------------
    def turnover_breakdown(self, date_from=None, date_to=None):
        qs = self.turnovers.all()
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        own = qs.filter(brand__brand_type=Brand.OWN).aggregate(t=models.Sum('amount'))['t'] or 0
        competitor = qs.filter(brand__brand_type=Brand.COMPETITOR).aggregate(t=models.Sum('amount'))['t'] or 0
        return {'own': own, 'competitor': competitor, 'total': own + competitor}


# ---------------------------------------------------------------------------
# Tracking: Visits with GPS check-in / check-out / time spent
# ---------------------------------------------------------------------------

class Visit(models.Model):
    """A single check-in/check-out event at a dealer — powers tracking,
    travel history, and time-spent-at-dealer features, and also the
    'total visit to a particular dealer' count."""

    salesman = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits')
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='visits')

    check_in_time = models.DateTimeField(default=timezone.now)
    check_in_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    check_in_lng = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    check_out_lng = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='visit_photos/', blank=True, null=True)

    class Meta:
        ordering = ['-check_in_time']

    def __str__(self):
        return f"{self.salesman} @ {self.dealer} on {self.check_in_time:%Y-%m-%d %H:%M}"

    @property
    def is_open(self):
        return self.check_out_time is None

    @property
    def duration_minutes(self):
        end = self.check_out_time or timezone.now()
        delta = end - self.check_in_time
        return round(delta.total_seconds() / 60)

    @property
    def duration_display(self):
        mins = self.duration_minutes
        h, m = divmod(mins, 60)
        if h:
            return f"{h}h {m}m"
        return f"{m}m"


# ---------------------------------------------------------------------------
# Product Awareness: stock & display rating per dealer
# ---------------------------------------------------------------------------

class ProductAwareness(models.Model):
    """Records what products/brands are available at a dealer, stock
    status and display quality — the 'Product Awareness' feature."""

    DISPLAY_EXCELLENT = 'excellent'
    DISPLAY_GOOD = 'good'
    DISPLAY_AVERAGE = 'average'
    DISPLAY_POOR = 'poor'
    DISPLAY_CHOICES = [
        (DISPLAY_EXCELLENT, 'Excellent'),
        (DISPLAY_GOOD, 'Good'),
        (DISPLAY_AVERAGE, 'Average'),
        (DISPLAY_POOR, 'Poor'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='awareness_records', null=True, blank=True)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='awareness_records')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='awareness_records')
    is_in_stock = models.BooleanField(default=True)
    stock_quantity_estimate = models.PositiveIntegerField(null=True, blank=True)
    display_quality = models.CharField(max_length=10, choices=DISPLAY_CHOICES, default=DISPLAY_GOOD)
    is_visible_to_customer = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='awareness_photos/', blank=True, null=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awareness_recorded')
    recorded_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = "Product Awareness Record"
        verbose_name_plural = "Product Awareness Records"

    def __str__(self):
        return f"{self.product} @ {self.dealer} - {self.get_display_quality_display()}"


# ---------------------------------------------------------------------------
# Price & Discount Comparison
# ---------------------------------------------------------------------------

class PriceComparison(models.Model):
    """Collects our product price/discount vs a competitor product's
    price/discount at a dealer — the 'Price & Discount Comparison' feature."""

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='price_records', null=True, blank=True)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='price_records')

    our_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='our_price_records',
        limit_choices_to={'brand__brand_type': Brand.OWN}
    )
    our_price = models.DecimalField(max_digits=10, decimal_places=2)
    our_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                                help_text="Discount % offered on our product.")

    competitor_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='competitor_price_records',
        null=True, blank=True, limit_choices_to={'brand__brand_type': Brand.COMPETITOR}
    )
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    competitor_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                                       help_text="Discount % offered on competitor product.")

    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='price_records_recorded')
    recorded_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.our_product} vs {self.competitor_product} @ {self.dealer}"

    @property
    def our_effective_price(self):
        return self.our_price * (1 - (self.our_discount_percent or 0) / 100)

    @property
    def competitor_effective_price(self):
        if self.competitor_price is None:
            return None
        return self.competitor_price * (1 - (self.competitor_discount_percent or 0) / 100)

    @property
    def price_difference(self):
        if self.competitor_price is None:
            return None
        return self.our_price - self.competitor_price

    @property
    def effective_price_difference(self):
        comp = self.competitor_effective_price
        if comp is None:
            return None
        return self.our_effective_price - comp

    @property
    def is_cheaper(self):
        diff = self.price_difference
        return diff is not None and diff < 0

    @property
    def is_effectively_cheaper(self):
        diff = self.effective_price_difference
        return diff is not None and diff < 0

    @property
    def discount_difference(self):
        """Positive means we are discounting more than the competitor."""
        return (self.our_discount_percent or 0) - (self.competitor_discount_percent or 0)


# ---------------------------------------------------------------------------
# Turnover
# ---------------------------------------------------------------------------

class Turnover(models.Model):
    """Sales/revenue recorded at a dealer — the 'Turnover' feature, used
    to measure performance and compare in-house vs competitor sales."""

    salesman = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turnovers')
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='turnovers')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnovers')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnovers')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnovers')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"₹{self.amount} - {self.dealer} on {self.date}"

    def save(self, *args, **kwargs):
        # Keep brand in sync with product when a product is selected directly.
        if self.product_id and not self.brand_id:
            self.brand = self.product.brand
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Project Visits (large opportunities: construction sites, bulk clients)
# ---------------------------------------------------------------------------

class ProjectVisit(models.Model):
    STAGE_LEAD = 'lead'
    STAGE_NEGOTIATION = 'negotiation'
    STAGE_FINALIZED = 'finalized'
    STAGE_EXECUTION = 'execution'
    STAGE_LOST = 'lost'
    STAGE_CHOICES = [
        (STAGE_LEAD, 'Lead / Prospect'),
        (STAGE_NEGOTIATION, 'Negotiation'),
        (STAGE_FINALIZED, 'Finalized'),
        (STAGE_EXECUTION, 'Under Execution'),
        (STAGE_LOST, 'Lost'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('construction', 'Construction Site'),
        ('bulk_client', 'Bulk Client'),
        ('government', 'Government Project'),
        ('institutional', 'Institutional'),
        ('other', 'Other'),
    ]

    salesman = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_visits')
    project_name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='construction')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_visits')
    location = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_LEAD)
    expected_business_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    visit_date = models.DateField(default=timezone.now)
    expected_closure_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='project_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.project_name} ({self.get_stage_display()})"


# ---------------------------------------------------------------------------
# Notifications (e.g. monthly turnover-update reminders)
# ---------------------------------------------------------------------------

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link_name = models.CharField(max_length=100, blank=True, help_text="URL name, e.g. tracker:turnover_create")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.recipient}"
