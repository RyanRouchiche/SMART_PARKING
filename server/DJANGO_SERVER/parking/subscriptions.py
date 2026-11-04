import calendar
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from .models import ParkingMembership, Subscription

logger = logging.getLogger(__name__)

REMINDER_DAYS = (30, 7)

REMINDER = {
    'fr': (
        "Votre abonnement Mawqif se termine le {end}",
        "Bonjour,\n\nL'abonnement du parking « {parking} » se termine le {end}, dans {days} jours. "
        "Après cette date, le parking restera visible {grace} jours dans l'application, puis il en sera retiré.\n\n"
        "Contactez-nous pour le renouveler : {team}",
    ),
    'ar': (
        "ينتهي اشتراكك في موقف بتاريخ {end}",
        "مرحبًا،\n\nينتهي اشتراك الموقف « {parking} » بتاريخ {end}، أي بعد {days} يومًا. "
        "بعد هذا التاريخ، يبقى الموقف ظاهرًا في التطبيق لمدة {grace} يومًا، ثم يُسحب منه.\n\n"
        "اتصل بنا لتجديده: {team}",
    ),
}


def local_today():
    return timezone.localdate(timezone=ZoneInfo(settings.PARKING_TIME_ZONE))


def add_months(day, months):
    year, month = divmod(day.month - 1 + months, 12)
    year, month = day.year + year, month + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def start_trial(subscription, today):
    subscription.status = Subscription.TRIAL
    subscription.period_end = add_months(today, settings.TRIAL_MONTHS)
    subscription.save(update_fields=['status', 'period_end'])


def record_payment(invoice):
    if invoice.period_end < local_today():
        return
    subscription = invoice.subscription
    if subscription.period_end is None or invoice.period_end > subscription.period_end:
        subscription.period_end = invoice.period_end
    subscription.status = Subscription.ACTIVE
    subscription.save(update_fields=['status', 'period_end'])


def remind(subscription, days):
    owners = ParkingMembership.objects.filter(
        parking=subscription.parking, role=ParkingMembership.OWNER, user__is_active=True
    ).select_related('user')
    for membership in owners:
        user = membership.user
        subject, body = REMINDER.get(user.language, REMINDER['fr'])
        values = {
            'parking': subscription.parking.name,
            'end': subscription.period_end.strftime('%d/%m/%Y'),
            'days': days,
            'grace': settings.GRACE_DAYS,
            'team': settings.TEAM_EMAIL,
        }
        try:
            send_mail(subject.format(**values), body.format(**values), None, [user.email], fail_silently=False)
        except Exception:
            logger.exception("Reminder for %s could not be sent", subscription.parking_id)


def run_daily(today):
    lapsed = Subscription.objects.filter(
        status=Subscription.PAST_DUE, period_end__lt=today - timedelta(days=settings.GRACE_DAYS)
    ).update(status=Subscription.CANCELLED)
    expired = Subscription.objects.filter(
        status__in=(Subscription.TRIAL, Subscription.ACTIVE), period_end__lt=today
    ).update(status=Subscription.PAST_DUE)
    reminded = 0
    for days in REMINDER_DAYS:
        for subscription in Subscription.objects.filter(
            status__in=(Subscription.TRIAL, Subscription.ACTIVE), period_end=today + timedelta(days=days)
        ).select_related('parking'):
            if cache.add(f"reminded:{subscription.pk}:{subscription.period_end}:{days}", True, 3 * 24 * 3600):
                remind(subscription, days)
                reminded += 1
    return {'expired': expired, 'cancelled': lapsed, 'reminded': reminded}
