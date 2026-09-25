# Salesman Tracker

A professional field-sales operations console for a marketing agency, built with
Django, Bootstrap 5 and SQLite. Tracks marketing executives' GPS check-ins/
check-outs, product availability and display quality at every dealer/counter,
competitor price & discount comparisons, dealer relationships, turnover (with
in-house vs. competitor comparison and growth insights), and large project
opportunities — all organised area-wise for easy performance analysis.

## Features

| Module | Description |
|---|---|
| **Tracking** | GPS-based check-in / check-out at dealers/counters, with full travel/visit history |
| **Product Awareness** | Log stock availability and shelf-display quality per product, per dealer |
| **Price & Discount Comparison** | Capture your product's price & discount vs. a competitor's, at any dealer, with an effective-price-after-discount comparison |
| **Dealers / Counters** | A dealer **is** the counter/shop — one unified record per outlet, with GPS, type, brands/products dealt, and assigned salesmen |
| **Competitor Details** | Track competitor brands with contact person, contact phone, market strength and notes |
| **Turnover** | Revenue recorded per dealer & brand; view **this month / last month / overall** totals with green ▲ / red ▼ growth arrows |
| **In-house vs Competitor Turnover** | Per-dealer comparison of your turnover vs. competitor turnover, month by month |
| **Monthly Turnover Reminder** | Automatic in-app notification on the 2nd of every month nudging users to update their turnover |
| **Project Visits** | Log visits to large opportunities (construction sites, bulk clients) with stage and expected value |
| **Area-wise Reporting** | All data organised and reportable by sales area/region |
| **Dealer Visit Count** | Total-visits-per-dealer breakdown, by salesman, to ensure regular follow-up |
| **User Management** | Owner manages all users; Area Managers manage (add/edit/remove) only their own team of Marketing Executives |

## Tech Stack

- **Backend:** Django 6.0 (Python)
- **Database:** SQLite (default, zero-config)
- **Frontend:** HTML5, Bootstrap 5.3, custom CSS design system, vanilla JS
- **Auth:** Django's built-in auth with a custom `User` model (**Owner / Area Manager / Marketing Executive** roles)

## Getting Started

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create an Owner account

```bash
python manage.py createsuperuser
```
Then set that user's `role` to `owner` (either in `/admin/` or by editing the
row directly) so they get full Owner permissions in the app itself.

### 5. (Optional) Load demo data

A ready-made demo dataset (areas, an Owner, Area Managers, Marketing
Executives, dealers/counters, visits, price/discount comparisons, turnover,
project pipeline) can be generated with:

```bash
python manage.py seed_demo_data
```

### 6. Set up the monthly turnover reminder (optional but recommended)

Add a daily cron job (it only actually sends reminders on the 2nd of the
month, so it's safe to run every day):

```bash
0 9 * * * /path/to/venv/bin/python /path/to/manage.py send_turnover_reminders
```

You can test it immediately regardless of today's date with:

```bash
python manage.py send_turnover_reminders --force
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** and sign in.

## Demo Credentials (after seeding)

| Role | Username | Password |
|---|---|---|
| Owner | `owner` | `owner12345` |
| Area Manager | `suresh.kulkarni` | `manager12345` |
| Area Manager | `anita.deshmukh` | `manager12345` |
| Marketing Executive | `rahul.sharma` | `salesman123` |
| Marketing Executive | `priya.singh` | `salesman123` |
| Marketing Executive | `amit.patel` | `salesman123` |
| Marketing Executive | `neha.joshi` | `salesman123` |
| Marketing Executive | `vikram.rao` | `salesman123` |

> Change all demo passwords before deploying anywhere beyond local testing.

## Project Structure

```
salesman_tracker/
├── accounts/                # Custom User model (Owner/Area Manager/Marketing
│   │                          Executive + manager relationship), Area model,
│   │                          login/logout + user management views
│   ├── models.py
│   ├── forms.py              # Owner & Area-Manager scoped user forms
│   ├── views.py              # user_list / user_create / user_edit / user_delete
│   ├── decorators.py         # role_required, is_owner, is_owner_or_area_manager
│   └── urls.py
├── tracker/                  # All core business logic & models
│   ├── models.py              # Brand (+ competitor details), Product, Dealer
│   │                           (== Counter), Visit, ProductAwareness,
│   │                           PriceComparison (+ discounts), Turnover
│   │                           (brand-based), ProjectVisit, Notification
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── management/commands/
│       ├── seed_demo_data.py
│       └── send_turnover_reminders.py
├── templates/                # Bootstrap-based, mobile-responsive templates
├── static/css/style.css      # Professional light theme design system
├── static/js/app.js          # Sidebar toggle + GPS geolocation capture
├── config/                   # Django project settings & root URLs
├── manage.py
└── requirements.txt
```

## Roles & Permissions

- **Owner** — full access to everything, including managing **all** users of any role.
- **Area Manager** — manages dealers, areas, catalogue, reports, and can **add/edit/remove Marketing Executives on their own team only** (new MEs they create are automatically assigned to them). Cannot manage other Area Managers or the Owner.
- **Marketing Executive** — no access to user management at all. Can check in/out of dealers, log product awareness, price/discount comparisons, turnover and project visits — and only sees their **own** activity/data.

## Notes for Production Deployment

- Set `DEBUG = False` and configure `ALLOWED_HOSTS` in `config/settings.py`.
- Replace the `SECRET_KEY` with a securely generated value (use an environment variable).
- Swap SQLite for PostgreSQL/MySQL if you expect concurrent multi-user write load at scale.
- Serve static/media files via a proper web server (Nginx, WhiteNoise, or a CDN) instead of Django's dev server.
- Use HTTPS and a production WSGI/ASGI server such as Gunicorn or Daphne.
- Schedule `send_turnover_reminders` via cron (Linux) or Task Scheduler (Windows) — see step 6 above.
