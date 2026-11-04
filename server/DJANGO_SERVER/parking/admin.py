from django.contrib import admin

from .models import Invoice, Parking, ParkingMembership, Subscription, Zone
from .services import published_parkings
from .subscriptions import local_today, start_trial


class MembershipInline(admin.TabularInline):
    model = ParkingMembership
    extra = 0


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0
    fields = ('number', 'name', 'camera')


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    can_delete = False
    fields = ('status', 'period_end', 'notes')


@admin.register(Parking)
class ParkingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity', 'is_published', 'subscription_status', 'period_end', 'in_app', 'created_at')
    list_filter = ('is_published', 'subscription__status')
    search_fields = ('name', 'address')
    list_select_related = ('subscription',)

    def get_inlines(self, request, obj):
        return [SubscriptionInline, ZoneInline, MembershipInline] if obj else [ZoneInline, MembershipInline]

    @admin.display(description="Abonnement", ordering='subscription__status')
    def subscription_status(self, parking):
        return parking.subscription.get_status_display()

    @admin.display(description="Fin de période", ordering='subscription__period_end')
    def period_end(self, parking):
        return parking.subscription.period_end

    @admin.display(description="Visible dans l'app", boolean=True)
    def in_app(self, parking):
        return published_parkings().filter(pk=parking.pk).exists()


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('parking', 'number', 'name', 'camera')
    list_filter = ('parking',)


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ('reference', 'amount_da', 'period_end', 'paid_on', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('parking', 'status', 'period_end')
    list_filter = ('status',)
    search_fields = ('parking__name',)
    list_select_related = ('parking',)
    readonly_fields = ('parking',)
    inlines = [InvoiceInline]
    actions = ['begin_trial']

    def has_add_permission(self, request):
        return False

    @admin.action(description="Démarrer l'essai gratuit")
    def begin_trial(self, request, queryset):
        today = local_today()
        for subscription in queryset.filter(status=Subscription.REQUEST):
            start_trial(subscription, today)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('reference', 'subscription', 'amount_da', 'period_end', 'paid_on', 'created_at')
    list_filter = ('paid_on',)
    search_fields = ('reference', 'subscription__parking__name')
