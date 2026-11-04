from django.core.management.base import BaseCommand

from parking.subscriptions import local_today, run_daily


class Command(BaseCommand):
    help = "Expire subscriptions, cancel them after the grace period and send renewal reminders."

    def handle(self, *args, **options):
        result = run_daily(local_today())
        self.stdout.write(f"expired={result['expired']} cancelled={result['cancelled']} reminded={result['reminded']}")
