from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator

from accounts.decorators import role_required, is_owner, is_owner_or_area_manager
from accounts.models import Area, User
from .forms import (
    AreaForm, DealerForm, CheckInForm, CheckOutForm, ProductAwarenessForm,
    PriceComparisonForm, TurnoverForm, ProjectVisitForm, BrandForm, ProductForm,
)
from .models import (
    Dealer, Visit, ProductAwareness, PriceComparison, Turnover,
    ProjectVisit, Brand, Product, Notification,
)

# Kept as local aliases so the rest of this module reads naturally.
is_admin_or_manager = is_owner_or_area_manager
is_admin = is_owner


# ---------------------------------------------------------------------------
# Turnover growth-insight helpers
# ---------------------------------------------------------------------------

def _add_months(anchor_date, delta_months):
    """Return the 1st of the month that is delta_months away from anchor_date."""
    month_index = anchor_date.month - 1 + delta_months
    year = anchor_date.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _month_bounds(anchor_date, months_back=0):
    first_of_month = _add_months(anchor_date, -months_back)
    next_month = _add_months(anchor_date, -months_back + 1)
    return first_of_month, next_month


def turnover_growth_summary(turnover_qs, today=None):
    """Returns this-month / last-month / overall turnover totals plus a
    growth percentage + direction ('up', 'down', 'flat') vs last month."""
    today = today or timezone.localdate()
    this_start, this_end = _month_bounds(today, 0)
    last_start, last_end = _month_bounds(today, 1)

    this_month = turnover_qs.filter(date__gte=this_start, date__lt=this_end).aggregate(t=Sum('amount'))['t'] or 0
    last_month = turnover_qs.filter(date__gte=last_start, date__lt=last_end).aggregate(t=Sum('amount'))['t'] or 0
    overall = turnover_qs.aggregate(t=Sum('amount'))['t'] or 0

    if last_month:
        growth_percent = round(((this_month - last_month) / last_month) * 100, 1)
    elif this_month:
        growth_percent = 100.0
    else:
        growth_percent = 0.0

    if growth_percent > 0:
        direction = 'up'
    elif growth_percent < 0:
        direction = 'down'
    else:
        direction = 'flat'

    return {
        'this_month': this_month,
        'last_month': last_month,
        'overall': overall,
        'growth_percent': growth_percent,
        'direction': direction,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    user = request.user
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)

    if user.is_marketing_executive:
        visits_qs = Visit.objects.filter(salesman=user)
        turnover_qs = Turnover.objects.filter(salesman=user)
    else:
        visits_qs = Visit.objects.all()
        turnover_qs = Turnover.objects.all()

    context = {
        'total_dealers': Dealer.objects.filter(is_active=True).count(),
        'visits_today': visits_qs.filter(check_in_time__date=today).count(),
        'open_visits': visits_qs.filter(check_out_time__isnull=True),
        'visits_week': visits_qs.filter(check_in_time__date__gte=week_ago).count(),
        'recent_visits': visits_qs.select_related('dealer', 'salesman')[:8],
        'active_projects': (ProjectVisit.objects.filter(salesman=user) if user.is_marketing_executive
                             else ProjectVisit.objects.all()).exclude(stage='lost')[:6],
        'areas': Area.objects.filter(is_active=True),
        'turnover': turnover_growth_summary(turnover_qs, today),
    }

    if not user.is_marketing_executive:
        context['team_size'] = User.objects.filter(role=User.ROLE_MARKETING_EXECUTIVE).count()
        context['area_performance'] = (
            Area.objects.filter(is_active=True)
            .annotate(
                dealers_count=Count('dealers', distinct=True),
                turnover_total=Sum('dealers__turnovers__amount'),
            )
            .order_by('-turnover_total')[:6]
        )
        context['top_salesmen'] = (
            User.objects.filter(role=User.ROLE_MARKETING_EXECUTIVE)
            .annotate(visit_count=Count('visits', distinct=True),
                      turnover_total=Sum('turnovers__amount'))
            .order_by('-turnover_total')[:5]
        )

    return render(request, 'tracker/dashboard.html', context)


# ---------------------------------------------------------------------------
# Tracking — Check-in / Check-out / Travel history
# ---------------------------------------------------------------------------

@login_required
def visit_list(request):
    visits = Visit.objects.select_related('dealer', 'salesman', 'dealer__area')
    if request.user.is_marketing_executive:
        visits = visits.filter(salesman=request.user)

    area_id = request.GET.get('area')
    salesman_id = request.GET.get('salesman')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if area_id:
        visits = visits.filter(dealer__area_id=area_id)
    if salesman_id:
        visits = visits.filter(salesman_id=salesman_id)
    if date_from:
        visits = visits.filter(check_in_time__date__gte=date_from)
    if date_to:
        visits = visits.filter(check_in_time__date__lte=date_to)

    paginator = Paginator(visits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'areas': Area.objects.filter(is_active=True),
        'salesmen': User.objects.filter(role=User.ROLE_MARKETING_EXECUTIVE),
        'filters': request.GET,
    }
    return render(request, 'tracker/visit_list.html', context)


@login_required
def check_in(request):
    if request.method == 'POST':
        form = CheckInForm(request.POST, request.FILES)
        if form.is_valid():
            # prevent multiple open visits
            open_visit = Visit.objects.filter(salesman=request.user, check_out_time__isnull=True).first()
            if open_visit:
                messages.warning(request, f"You already have an open visit at {open_visit.dealer}. Please check out first.")
                return redirect('tracker:visit_active')
            visit = form.save(commit=False)
            visit.salesman = request.user
            visit.check_in_time = timezone.now()
            visit.save()
            messages.success(request, f"Checked in at {visit.dealer} successfully.")
            return redirect('tracker:visit_active')
    else:
        form = CheckInForm()
        if request.user.is_marketing_executive:
            form.fields['dealer'].queryset = Dealer.objects.filter(
                Q(assigned_salesmen=request.user) | Q(assigned_salesmen__isnull=True),
                is_active=True
            ).distinct()

    return render(request, 'tracker/check_in.html', {'form': form})


@login_required
def visit_active(request):
    visit = Visit.objects.filter(salesman=request.user, check_out_time__isnull=True).select_related('dealer').first()
    form = CheckOutForm() if visit else None
    return render(request, 'tracker/visit_active.html', {'visit': visit, 'form': form})


@login_required
def check_out(request, pk):
    visit = get_object_or_404(Visit, pk=pk, salesman=request.user, check_out_time__isnull=True)
    if request.method == 'POST':
        form = CheckOutForm(request.POST, instance=visit)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.check_out_time = timezone.now()
            visit.save()
            messages.success(request, f"Checked out from {visit.dealer}. Time spent: {visit.duration_display}.")
            return redirect('tracker:dashboard')
    return redirect('tracker:visit_active')


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(
        Visit.objects.select_related('dealer', 'salesman')
        .prefetch_related('awareness_records__product', 'price_records', 'turnovers'),
        pk=pk
    )
    if request.user.is_marketing_executive and visit.salesman != request.user:
        messages.error(request, "You don't have permission to view this visit.")
        return redirect('tracker:visit_list')
    return render(request, 'tracker/visit_detail.html', {'visit': visit})


# ---------------------------------------------------------------------------
# Dealers (Dealer and Counter are the same entity)
# ---------------------------------------------------------------------------

@login_required
def dealer_list(request):
    dealers = Dealer.objects.select_related('area').annotate(visit_count=Count('visits', distinct=True))
    q = request.GET.get('q')
    area_id = request.GET.get('area')
    status = request.GET.get('status')
    if q:
        dealers = dealers.filter(Q(name__icontains=q) | Q(owner_name__icontains=q) | Q(address__icontains=q))
    if area_id:
        dealers = dealers.filter(area_id=area_id)
    if status == 'active':
        dealers = dealers.filter(is_active=True)
    elif status == 'inactive':
        dealers = dealers.filter(is_active=False)

    dealers = dealers.order_by('name')
    paginator = Paginator(dealers, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page_obj,
        'areas': Area.objects.filter(is_active=True),
        'filters': request.GET,
        'total_active': Dealer.objects.filter(is_active=True).count(),
        'total_inactive': Dealer.objects.filter(is_active=False).count(),
    }
    return render(request, 'tracker/dealer_list.html', context)


@login_required
def dealer_detail(request, pk):
    dealer = get_object_or_404(
        Dealer.objects.select_related('area').prefetch_related('brands_dealt', 'products_dealt', 'assigned_salesmen'),
        pk=pk
    )
    visits = dealer.visits.select_related('salesman').order_by('-check_in_time')[:10]
    awareness = dealer.awareness_records.select_related('product', 'product__brand').order_by('-recorded_at')[:10]
    prices = dealer.price_records.select_related('our_product', 'competitor_product').order_by('-recorded_at')[:10]
    turnovers = dealer.turnovers.select_related('brand', 'product').order_by('-date')[:10]

    turnover_summary = turnover_growth_summary(dealer.turnovers.all())
    turnover_summary['breakdown'] = dealer.turnover_breakdown()

    context = {
        'dealer': dealer, 'visits': visits, 'awareness': awareness,
        'prices': prices, 'turnovers': turnovers,
        'turnover_total': turnover_summary['overall'],
        'turnover_summary': turnover_summary,
        'visit_count': dealer.visits.count(),
    }
    return render(request, 'tracker/dealer_detail.html', context)


@login_required
def dealer_turnover_comparison(request, pk):
    """In-house vs competitor turnover comparison for a single dealer,
    broken down month by month for the last 6 months."""
    dealer = get_object_or_404(Dealer, pk=pk)
    today = timezone.localdate()
    months = []
    for i in range(5, -1, -1):
        start, end = _month_bounds(today, i)
        qs = dealer.turnovers.filter(date__gte=start, date__lt=end)
        own = qs.filter(brand__brand_type=Brand.OWN).aggregate(t=Sum('amount'))['t'] or 0
        competitor = qs.filter(brand__brand_type=Brand.COMPETITOR).aggregate(t=Sum('amount'))['t'] or 0
        months.append({
            'label': start.strftime('%b %Y'), 'own': own, 'competitor': competitor,
            'diff': own - competitor,
        })

    by_brand = (
        dealer.turnovers.exclude(brand__isnull=True)
        .values('brand__name', 'brand__brand_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    overall = dealer.turnover_breakdown()
    return render(request, 'tracker/dealer_turnover_comparison.html', {
        'dealer': dealer, 'months': months, 'by_brand': by_brand, 'overall': overall,
    })


@role_required(is_owner_or_area_manager)
def dealer_create(request):
    if request.method == 'POST':
        form = DealerForm(request.POST)
        if form.is_valid():
            dealer = form.save(commit=False)
            dealer.created_by = request.user
            dealer.save()
            form.save_m2m()
            messages.success(request, f"Dealer '{dealer.name}' created.")
            return redirect('tracker:dealer_detail', pk=dealer.pk)
    else:
        form = DealerForm()
    return render(request, 'tracker/dealer_form.html', {'form': form, 'title': 'Add Dealer'})


@role_required(is_owner_or_area_manager)
def dealer_edit(request, pk):
    dealer = get_object_or_404(Dealer, pk=pk)
    if request.method == 'POST':
        form = DealerForm(request.POST, instance=dealer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dealer '{dealer.name}' updated.")
            return redirect('tracker:dealer_detail', pk=dealer.pk)
    else:
        form = DealerForm(instance=dealer)
    return render(request, 'tracker/dealer_form.html', {'form': form, 'title': 'Edit Dealer'})


# ---------------------------------------------------------------------------
# Product Awareness
# ---------------------------------------------------------------------------

@login_required
def awareness_list(request):
    records = ProductAwareness.objects.select_related('dealer', 'product', 'product__brand', 'recorded_by')
    if request.user.is_marketing_executive:
        records = records.filter(recorded_by=request.user)
    dealer_id = request.GET.get('dealer')
    if dealer_id:
        records = records.filter(dealer_id=dealer_id)
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tracker/awareness_list.html', {'page_obj': page_obj, 'filters': request.GET})


@login_required
def awareness_create(request):
    if request.method == 'POST':
        form = ProductAwarenessForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(request, "Product awareness record saved.")
            return redirect('tracker:awareness_list')
    else:
        form = ProductAwarenessForm()
    return render(request, 'tracker/awareness_form.html', {'form': form, 'title': 'Add Product Awareness Record'})


# ---------------------------------------------------------------------------
# Price & Discount Comparison
# ---------------------------------------------------------------------------

@login_required
def price_list(request):
    records = PriceComparison.objects.select_related('dealer', 'our_product', 'competitor_product')
    if request.user.is_marketing_executive:
        records = records.filter(recorded_by=request.user)
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tracker/price_list.html', {'page_obj': page_obj})


@login_required
def price_create(request):
    if request.method == 'POST':
        form = PriceComparisonForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(request, "Price & discount comparison recorded.")
            return redirect('tracker:price_list')
    else:
        form = PriceComparisonForm()
    return render(request, 'tracker/price_form.html', {'form': form, 'title': 'Add Price & Discount Comparison'})


# ---------------------------------------------------------------------------
# Turnover
# ---------------------------------------------------------------------------

@login_required
def turnover_list(request):
    records = Turnover.objects.select_related('dealer', 'brand', 'product', 'salesman')
    if request.user.is_marketing_executive:
        records = records.filter(salesman=request.user)
    summary = turnover_growth_summary(records)
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tracker/turnover_list.html', {'page_obj': page_obj, 'total': summary['overall'], 'summary': summary})


@login_required
def turnover_create(request):
    if request.method == 'POST':
        form = TurnoverForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.salesman = request.user
            record.save()
            messages.success(request, "Turnover entry recorded.")
            return redirect('tracker:turnover_list')
    else:
        form = TurnoverForm()
    return render(request, 'tracker/turnover_form.html', {'form': form, 'title': 'Add Turnover Entry'})


# ---------------------------------------------------------------------------
# Project Visits
# ---------------------------------------------------------------------------

@login_required
def project_list(request):
    projects = ProjectVisit.objects.select_related('area', 'salesman')
    if request.user.is_marketing_executive:
        projects = projects.filter(salesman=request.user)
    stage = request.GET.get('stage')
    if stage:
        projects = projects.filter(stage=stage)
    paginator = Paginator(projects, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    pipeline_value = projects.exclude(stage='lost').aggregate(t=Sum('expected_business_value'))['t'] or 0
    return render(request, 'tracker/project_list.html', {'page_obj': page_obj, 'pipeline_value': pipeline_value, 'filters': request.GET})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(ProjectVisit.objects.select_related('area', 'salesman'), pk=pk)
    return render(request, 'tracker/project_detail.html', {'project': project})


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectVisitForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.salesman = request.user
            project.save()
            messages.success(request, f"Project visit '{project.project_name}' logged.")
            return redirect('tracker:project_detail', pk=project.pk)
    else:
        form = ProjectVisitForm()
    return render(request, 'tracker/project_form.html', {'form': form, 'title': 'Log Project Visit'})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(ProjectVisit, pk=pk)
    if request.user.is_marketing_executive and project.salesman != request.user:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('tracker:project_list')
    if request.method == 'POST':
        form = ProjectVisitForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project visit updated.")
            return redirect('tracker:project_detail', pk=project.pk)
    else:
        form = ProjectVisitForm(instance=project)
    return render(request, 'tracker/project_form.html', {'form': form, 'title': 'Edit Project Visit'})


# ---------------------------------------------------------------------------
# Area-wise reports
# ---------------------------------------------------------------------------

@role_required(is_owner_or_area_manager)
def area_report(request):
    areas = Area.objects.annotate(
        dealers_count=Count('dealers', distinct=True),
        visits_count=Count('dealers__visits', distinct=True),
        turnover_total=Sum('dealers__turnovers__amount'),
        projects_count=Count('project_visits', distinct=True),
        pipeline_value=Sum('project_visits__expected_business_value'),
    ).order_by('-turnover_total')
    return render(request, 'tracker/area_report.html', {'areas': areas})


@role_required(is_owner_or_area_manager)
def area_list(request):
    areas = Area.objects.annotate(salesmen_count=Count('salesmen', distinct=True))
    return render(request, 'tracker/area_list.html', {'areas': areas})


@role_required(is_owner_or_area_manager)
def area_create(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Area created.")
            return redirect('tracker:area_list')
    else:
        form = AreaForm()
    return render(request, 'tracker/area_form.html', {'form': form, 'title': 'Add Area'})


@role_required(is_owner_or_area_manager)
def area_edit(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, "Area updated.")
            return redirect('tracker:area_list')
    else:
        form = AreaForm(instance=area)
    return render(request, 'tracker/area_form.html', {'form': form, 'title': 'Edit Area'})


@login_required
def dealer_visit_count(request, pk):
    """'Total visit to a particular dealer' feature — detail breakdown."""
    dealer = get_object_or_404(Dealer, pk=pk)
    visits = dealer.visits.select_related('salesman').order_by('-check_in_time')
    by_salesman = visits.values('salesman__first_name', 'salesman__last_name', 'salesman__username').annotate(
        count=Count('id')
    ).order_by('-count')
    paginator = Paginator(visits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tracker/dealer_visit_count.html', {
        'dealer': dealer, 'page_obj': page_obj, 'by_salesman': by_salesman, 'total': visits.count(),
    })


# ---------------------------------------------------------------------------
# Brands & Products (catalogue management, incl. competitor details)
# ---------------------------------------------------------------------------

@role_required(is_owner_or_area_manager)
def catalogue(request):
    brands = Brand.objects.prefetch_related('products')
    return render(request, 'tracker/catalogue.html', {'brands': brands})


@role_required(is_owner_or_area_manager)
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand added.")
            return redirect('tracker:catalogue')
    else:
        form = BrandForm()
    return render(request, 'tracker/brand_form.html', {'form': form, 'title': 'Add Brand'})


@role_required(is_owner_or_area_manager)
def brand_edit(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand updated.")
            return redirect('tracker:catalogue')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'tracker/brand_form.html', {'form': form, 'title': f'Edit {brand.name}'})


@role_required(is_owner_or_area_manager)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added.")
            return redirect('tracker:catalogue')
    else:
        form = ProductForm()
    return render(request, 'tracker/product_form.html', {'form': form, 'title': 'Add Product'})


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    notifications.filter(is_read=False).update(is_read=True)
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tracker/notification_list.html', {'page_obj': page_obj})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link_name or 'tracker:notification_list')
