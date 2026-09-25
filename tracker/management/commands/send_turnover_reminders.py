from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from tracker.models import Notification


class Command(BaseCommand):
    """Creates an in-app notification for every active user reminding them
    to update their turnover for the month.

    Intended to run once a day via cron/Task Scheduler; it only actually
    creates notifications on the 2nd of the month (or every day if --force
    is passed), and never creates a duplicate reminder for the same month.

    Example crontab entry (runs daily at 9 AM, only acts on the 2nd):
        0 9 * * * /path/to/venv/bin/python /path/to/manage.py send_turnover_reminders
    """

    help = "Send a reminder (on the 2nd of each month) asking users to update their turnover."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help="Send reminders regardless of today's date (useful for testing).",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        if today.day != 2 and not options['force']:
            self.stdout.write(f"Today ({today}) is not the 2nd of the month — nothing to do. Use --force to override.")
            return

        month_label = today.strftime('%B %Y')
        users = User.objects.filter(is_active=True, is_active_employee=True)

        created = 0
        for user in users:
            already_sent = Notification.objects.filter(
                recipient=user,
                title="Update your turnover",
                created_at__year=today.year,
                created_at__month=today.month,
            ).exists()
            if already_sent:
                continue
            Notification.objects.create(
                recipient=user,
                title="Update your turnover",
                message=f"Reminder: please update your turnover entries for {month_label}.",
                link_name='tracker:turnover_create',
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Sent {created} turnover reminder notification(s) for {month_label}."))
