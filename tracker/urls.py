from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Tracking / visits
    path('visits/', views.visit_list, name='visit_list'),
    path('visits/active/', views.visit_active, name='visit_active'),
    path('visits/check-in/', views.check_in, name='check_in'),
    path('visits/check-out/<int:pk>/', views.check_out, name='check_out'),
    path('visits/<int:pk>/', views.visit_detail, name='visit_detail'),

    # Dealers (Dealer and Counter are the same entity)
    path('dealers/', views.dealer_list, name='dealer_list'),
    path('dealers/add/', views.dealer_create, name='dealer_create'),
    path('dealers/<int:pk>/', views.dealer_detail, name='dealer_detail'),
    path('dealers/<int:pk>/edit/', views.dealer_edit, name='dealer_edit'),
    path('dealers/<int:pk>/visits/', views.dealer_visit_count, name='dealer_visit_count'),
    path('dealers/<int:pk>/turnover-comparison/', views.dealer_turnover_comparison, name='dealer_turnover_comparison'),

    # Product awareness
    path('awareness/', views.awareness_list, name='awareness_list'),
    path('awareness/add/', views.awareness_create, name='awareness_create'),

    # Price & discount comparison
    path('prices/', views.price_list, name='price_list'),
    path('prices/add/', views.price_create, name='price_create'),

    # Turnover
    path('turnover/', views.turnover_list, name='turnover_list'),
    path('turnover/add/', views.turnover_create, name='turnover_create'),

    # Project visits
    path('projects/', views.project_list, name='project_list'),
    path('projects/add/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),

    # Areas / reports
    path('areas/', views.area_list, name='area_list'),
    path('areas/add/', views.area_create, name='area_create'),
    path('areas/<int:pk>/edit/', views.area_edit, name='area_edit'),
    path('reports/area/', views.area_report, name='area_report'),

    # Catalogue (brands incl. competitor details, products)
    path('catalogue/', views.catalogue, name='catalogue'),
    path('catalogue/brand/add/', views.brand_create, name='brand_create'),
    path('catalogue/brand/<int:pk>/edit/', views.brand_edit, name='brand_edit'),
    path('catalogue/product/add/', views.product_create, name='product_create'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
]
