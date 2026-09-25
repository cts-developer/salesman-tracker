import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Area, User
from tracker.models import (
    Brand, Product, Dealer, Visit, ProductAwareness,
    PriceComparison, Turnover, ProjectVisit,
)


class Command(BaseCommand):
    help = "Seed the database with realistic demo data for Salesman Tracker."

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write("Seeding demo data...")

        # --- Areas -----------------------------------------------------
        area_data = [
            ("South Mumbai", "MUM-S", "Mumbai", "Maharashtra"),
            ("Andheri-Borivali", "MUM-W", "Mumbai", "Maharashtra"),
            ("Pune City", "PUN-C", "Pune", "Maharashtra"),
            ("Ahmedabad West", "AMD-W", "Ahmedabad", "Gujarat"),
            ("Bengaluru South", "BLR-S", "Bengaluru", "Karnataka"),
        ]
        areas = []
        for name, code, city, state in area_data:
            a, _ = Area.objects.get_or_create(code=code, defaults=dict(
                name=name, city=city, state=state, is_active=True))
            areas.append(a)

        # --- Owner --------------------------------------------------------
        owner, created = User.objects.get_or_create(
            username='owner', defaults=dict(
                first_name='Ramesh', last_name='Agarwal', role=User.ROLE_OWNER,
                phone='9820000001', email='owner@salesmantracker.local',
                is_staff=True, is_superuser=True,
            ))
        if created:
            owner.set_password('owner12345')
            owner.save()

        # --- Area Managers --------------------------------------------------
        area_manager_data = [
            ("suresh.kulkarni", "Suresh", "Kulkarni", areas[0], "9820011223"),
            ("anita.deshmukh", "Anita", "Deshmukh", areas[2], "9820011224"),
        ]
        area_managers = []
        for username, fn, ln, area, phone in area_manager_data:
            m, created = User.objects.get_or_create(username=username, defaults=dict(
                first_name=fn, last_name=ln, role=User.ROLE_AREA_MANAGER, area=area,
                phone=phone, email=f"{username}@salesmantracker.local",
            ))
            if created:
                m.set_password('manager12345')
                m.save()
            area_managers.append(m)

        # --- Marketing Executives, each reporting to an Area Manager -------
        salesman_data = [
            ("rahul.sharma", "Rahul", "Sharma", areas[0], "9820012345", "EMP-101", area_managers[0]),
            ("priya.singh", "Priya", "Singh", areas[1], "9820012346", "EMP-102", area_managers[0]),
            ("amit.patel", "Amit", "Patel", areas[2], "9820012347", "EMP-103", area_managers[1]),
            ("neha.joshi", "Neha", "Joshi", areas[3], "9820012348", "EMP-104", area_managers[1]),
            ("vikram.rao", "Vikram", "Rao", areas[4], "9820012349", "EMP-105", area_managers[1]),
        ]
        salesmen = []
        for username, fn, ln, area, phone, code, manager in salesman_data:
            s, created = User.objects.get_or_create(username=username, defaults=dict(
                first_name=fn, last_name=ln, role=User.ROLE_MARKETING_EXECUTIVE, area=area,
                phone=phone, employee_code=code, email=f"{username}@salesmantracker.local",
                manager=manager,
                date_joined_company=date(2024, random.randint(1, 12), random.randint(1, 28)),
            ))
            if created:
                s.set_password('salesman123')
                s.save()
            salesmen.append(s)

        # --- Brands & Products (incl. competitor details) ------------------
        own_brands = ["Suntech Paints", "Suntech Hardware", "Suntech Adhesives"]
        comp_brand_info = [
            ("Asian Shield", "R. Bhatia", "9811100001", Brand.STRENGTH_STRONG,
             "Market leader in the region, strong dealer loyalty schemes."),
            ("Berger Pro", "K. Nair", "9811100002", Brand.STRENGTH_MODERATE,
             "Competitive pricing but weaker after-sales support."),
            ("Nerolac Plus", "S. Iyer", "9811100003", Brand.STRENGTH_MODERATE,
             "Aggressive discounting during festive season."),
        ]

        own_brand_objs = []
        for name in own_brands:
            b, _ = Brand.objects.get_or_create(name=name, defaults=dict(brand_type=Brand.OWN))
            own_brand_objs.append(b)

        comp_brand_objs = []
        for name, contact, phone, strength, notes in comp_brand_info:
            b, _ = Brand.objects.get_or_create(name=name, defaults=dict(
                brand_type=Brand.COMPETITOR, contact_person=contact,
                contact_phone=phone, market_strength=strength, notes=notes,
            ))
            comp_brand_objs.append(b)

        categories = ["Emulsion Paint", "Enamel Paint", "Primer", "Adhesive", "Putty"]
        products = []
        for brand in own_brand_objs + comp_brand_objs:
            for i in range(3):
                cat = random.choice(categories)
                p, _ = Product.objects.get_or_create(
                    brand=brand, name=f"{cat} {random.choice(['1L','4L','10L','20kg'])} #{i+1}",
                    defaults=dict(category=cat, sku=f"SKU-{brand.id}{i}",
                                  unit_price=random.randint(150, 4500))
                )
                products.append(p)
        own_products = [p for p in products if p.brand.brand_type == Brand.OWN]
        comp_products = [p for p in products if p.brand.brand_type == Brand.COMPETITOR]

        # --- Dealers (Dealer == Counter) ------------------------------------
        dealer_names = [
            "Shree Ganesh Hardware", "City Paint House", "New Bombay Traders",
            "Patel Building Materials", "Om Sai Enterprises", "Krishna Hardware Mart",
            "Vishal Paints & Sanitary", "Royal Decor Hub",
        ]
        counter_types = ['retail', 'wholesale', 'hardware', 'showroom']
        dealers = []
        for i, dn in enumerate(dealer_names):
            area = areas[i % len(areas)]
            owner_name = random.choice(["R. Mehta", "S. Iyer", "K. Verma", "A. Khan", "M. Desai"])
            d, _ = Dealer.objects.get_or_create(name=dn, defaults=dict(
                owner_name=owner_name,
                contact_person=owner_name,
                phone=f"98{random.randint(10000000,99999999)}",
                email=f"{dn.split()[0].lower()}@example.com",
                area=area,
                address=f"{random.randint(1,200)}, Main Market Road, {area.city}",
                counter_type=random.choice(counter_types),
                latitude=18.9 + random.uniform(-0.4, 0.4),
                longitude=72.8 + random.uniform(-0.4, 0.6),
                gst_number=f"27AAAA{1000+i}A1Z{i%9}",
                is_active=random.random() > 0.1,
                created_by=area_managers[0],
            ))
            d.brands_dealt.set(random.sample(own_brand_objs + comp_brand_objs, k=3))
            d.products_dealt.set(random.sample(products, k=5))
            d.assigned_salesmen.add(random.choice(salesmen))
            dealers.append(d)

        # --- Visits, Awareness, Price/Discount, Turnover ---------------------
        now = timezone.now()
        salesman_has_open_visit = set()
        for day_offset in range(60):
            day = now - timedelta(days=day_offset)
            for salesman in salesmen:
                if random.random() < 0.55:
                    visited_dealers = random.sample(dealers, k=min(random.randint(1, 3), len(dealers)))
                    for d in visited_dealers:
                        check_in = day.replace(
                            hour=random.randint(9, 16), minute=random.randint(0, 59), second=0, microsecond=0)
                        duration = random.randint(15, 90)
                        check_out = check_in + timedelta(minutes=duration)
                        is_today_open = (
                            day_offset == 0 and random.random() < 0.15
                            and salesman.id not in salesman_has_open_visit
                        )
                        if is_today_open:
                            salesman_has_open_visit.add(salesman.id)

                        visit = Visit.objects.create(
                            salesman=salesman, dealer=d,
                            check_in_time=check_in,
                            check_in_lat=d.latitude, check_in_lng=d.longitude,
                            check_out_time=None if is_today_open else check_out,
                            check_out_lat=None if is_today_open else d.latitude,
                            check_out_lng=None if is_today_open else d.longitude,
                            notes=random.choice([
                                "Stock replenished, good visibility.",
                                "Discussed upcoming scheme with dealer.",
                                "Counter needs better shelf display.",
                                "",
                            ]),
                        )

                        if random.random() < 0.6 and own_products:
                            for prod in random.sample(own_products, k=min(2, len(own_products))):
                                ProductAwareness.objects.create(
                                    visit=visit, dealer=d, product=prod,
                                    is_in_stock=random.random() > 0.15,
                                    stock_quantity_estimate=random.randint(5, 80),
                                    display_quality=random.choice(['excellent', 'good', 'average', 'poor']),
                                    is_visible_to_customer=random.random() > 0.1,
                                    recorded_by=salesman,
                                    remarks="",
                                )

                        if random.random() < 0.4 and own_products and comp_products:
                            our_p = random.choice(own_products)
                            comp_p = random.choice(comp_products)
                            PriceComparison.objects.create(
                                visit=visit, dealer=d,
                                our_product=our_p, our_price=our_p.unit_price,
                                our_discount_percent=random.choice([0, 5, 10, 12]),
                                competitor_product=comp_p,
                                competitor_price=comp_p.unit_price + random.randint(-150, 150),
                                competitor_discount_percent=random.choice([0, 5, 8, 15]),
                                recorded_by=salesman,
                            )

                        if random.random() < 0.5:
                            chosen_brand = random.choice(own_brand_objs + comp_brand_objs)
                            chosen_products = [p for p in products if p.brand_id == chosen_brand.id]
                            Turnover.objects.create(
                                salesman=salesman, dealer=d, brand=chosen_brand,
                                product=random.choice(chosen_products) if chosen_products else None,
                                visit=visit,
                                amount=random.randint(800, 25000),
                                date=check_in.date(),
                            )

        # --- Project Visits -------------------------------------------------
        project_names = [
            "Lakeview Residency Tower B", "Greenfield IT Park Phase 2",
            "Sunrise Public School Renovation", "Metro Mall Extension",
            "Hillcrest Bungalows", "Riverside Logistics Hub",
        ]
        stages = ['lead', 'negotiation', 'finalized', 'execution', 'lost']
        ptypes = ['construction', 'bulk_client', 'government', 'institutional']
        for i, pname in enumerate(project_names):
            ProjectVisit.objects.get_or_create(
                project_name=pname,
                defaults=dict(
                    salesman=random.choice(salesmen),
                    project_type=random.choice(ptypes),
                    area=random.choice(areas),
                    location=f"{random.choice(['Sector 12','Phase 3','MIDC Road','Ring Road'])}, {random.choice(areas).city}",
                    contact_person=random.choice(["Mr. Kapoor", "Ms. Reddy", "Mr. Bansal"]),
                    contact_phone=f"98{random.randint(10000000,99999999)}",
                    stage=stages[i % len(stages)],
                    expected_business_value=random.randint(150000, 4500000),
                    visit_date=date.today() - timedelta(days=random.randint(0, 25)),
                    expected_closure_date=date.today() + timedelta(days=random.randint(10, 90)),
                    notes="Discussed bulk pricing and delivery schedule on site visit.",
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Done. Owner login: owner / owner12345\n"
            f"Area Manager logins: suresh.kulkarni / anita.deshmukh (password: manager12345)\n"
            f"Marketing Executive logins: e.g. rahul.sharma (password: salesman123)\n"
            f"Areas={Area.objects.count()} Dealers={len(dealers)} "
            f"Visits={Visit.objects.count()} Turnover entries={Turnover.objects.count()} "
            f"Projects={ProjectVisit.objects.count()}"
        ))
