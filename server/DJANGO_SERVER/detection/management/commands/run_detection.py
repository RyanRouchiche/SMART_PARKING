import logging
import time

from django.core.management.base import BaseCommand

from detection.worker import Supervisor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Capture every zone once and publish its occupancy to the WebSocket groups"

    def add_arguments(self, parser):
        parser.add_argument('--shard', type=int, default=0)
        parser.add_argument('--shards', type=int, default=1)
        parser.add_argument('--sync-interval', type=float, default=10)

    def handle(self, shard, shards, sync_interval, **options):
        supervisor = Supervisor(shard, shards)
        self.stdout.write(f"Detection worker {shard + 1}/{shards} started")
        try:
            while True:
                try:
                    supervisor.sync()
                except Exception:
                    logger.exception("Zone sync failed, retrying")
                time.sleep(sync_interval)
        except KeyboardInterrupt:
            supervisor.stop()
