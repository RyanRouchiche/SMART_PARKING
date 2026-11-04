import socket

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from detection.interface import stream_client
from public.notifications import FcmSender, ensure_group, process


class Command(BaseCommand):
    help = "Send push notifications to drivers when a favorite parking that was full has free spots again."

    def handle(self, *args, **options):
        client = stream_client()
        ensure_group(client)
        sender = FcmSender()
        consumer = socket.gethostname()
        self.stdout.write("Notification worker started")
        while True:
            close_old_connections()
            process(client, sender, consumer)
