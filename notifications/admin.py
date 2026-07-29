from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['destinataire', 'type_notif', 'sujet', 'lu', 'envoye_par_email', 'created_at']
    list_filter   = ['type_notif', 'lu', 'envoye_par_email']
    search_fields = ['destinataire__email', 'sujet']
    readonly_fields = ['created_at']