from django.contrib import admin
from .models import Caveau, AuditCaveau

@admin.register(Caveau)
class CaveauAdmin(admin.ModelAdmin):
    list_display  = ['numero', 'bloc', 'statut', 'prix', 'latitude', 'longitude', 'created_at']
    list_filter   = ['statut']
    search_fields = ['numero']

@admin.register(AuditCaveau)
class AuditCaveauAdmin(admin.ModelAdmin):
    list_display  = ['caveau', 'modifie_par', 'ancien_statut', 'nouveau_statut', 'date_modification']
    list_filter   = ['ancien_statut', 'nouveau_statut']
    readonly_fields = ['caveau', 'modifie_par', 'ancien_statut', 'nouveau_statut', 'date_modification']