from django.core.management.base import BaseCommand

from detection.health import alert, report


class Command(BaseCommand):
    help = "Check the model server and data freshness of open, visible parkings; email the team when problems change."

    def add_arguments(self, parser):
        parser.add_argument('--email', action='store_true')

    def handle(self, *args, email=False, **options):
        problems = report()['problems']
        for problem in problems:
            self.stdout.write(f"PROBLEM {problem}")
        if not problems:
            self.stdout.write("OK")
        if email:
            alert(problems)
