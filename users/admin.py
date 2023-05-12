from django.contrib import admin
from users.models import Profile, DyatelSettings, Transaction, PaymentsInvoices


class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'tlg_session_file',
        'green_api_id_instance',
    ]
    list_display_links = [
        'id',
        'user',
        'tlg_session_file',
        'green_api_id_instance',
    ]


@admin.register(DyatelSettings)
class DyatelSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'key',
    ]
    list_display_links = [
        'key',
    ]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "transaction_type",
        "transaction_datetime",
        "amount",
    ]
    list_display_links = [
        "id",
        "user",
        "transaction_type",
        "transaction_datetime",
        "amount",
    ]


@admin.register(PaymentsInvoices)
class PaymentsInvoicesAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "amount",
        "is_paid",
        "created_at",
        "payment_url",
    ]
    list_display_links =[
        "user",
        "amount",
        "is_paid",
        "created_at",
        "payment_url",
    ]
    list_filter = 'created_at', 'is_paid',
    search_fields = [
        "user",
        "amount",
        "is_paid",
        "created_at",
        "payment_url",
    ]
    search_help_text = 'Поиск по полям, отображённым в данной таблице'


admin.site.register(Profile, ProfileAdmin)
