from django.contrib import admin

from app_collector.models import Clients, Mailings, Feedback, ClientsFiles


class ClientsInline(admin.StackedInline):
    """
    Отображение многих файлов для каждой записи модели Clients.
    """
    model = ClientsFiles


class ClientsAdmin(admin.ModelAdmin):
    inlines = [
        ClientsInline,
    ]
    list_display = [
        'id',
        'user',
        'client_name',
        'telephone_or_username',
        'amount_of_pmnt',
        'pmnt_date',
    ]
    list_display_links = [
        'id',
        'user',
        'client_name',
        'telephone_or_username',
        'amount_of_pmnt',
        'pmnt_date',
    ]


class MailingsAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'client',
        'mlng_txt',
        'sent_datetime',
        'sending_status',
        'send_info',
    ]
    list_display_links = [
        'id',
        'client',
        'mlng_txt',
        'sent_datetime',
        'sending_status',
        'send_info',
    ]


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'send_datetime']
    list_display_links = ['user', 'send_datetime']


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Clients, ClientsAdmin)
admin.site.register(Mailings, MailingsAdmin)

