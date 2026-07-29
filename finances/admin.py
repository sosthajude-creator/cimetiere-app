from django.contrib import admin
from .models import Facture, Paiement, AlerteFinanciere

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display  = ['id', 'reservation', 'montant', 'montant_paye', 'statut', 'created_at']
    list_filter   = ['statut']
    search_fields = ['reservation__client__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ['id', 'facture', 'montant', 'canal', 'reference', 'enregistre_par', 'created_at']
    list_filter   = ['canal']
    search_fields = ['reference', 'facture__reservation__client__email']
    readonly_fields = ['created_at']

@admin.register(AlerteFinanciere)
class AlerteFinanciereAdmin(admin.ModelAdmin):
    list_display  = ['type_alerte', 'message', 'lu', 'created_at']
    list_filter   = ['type_alerte', 'lu']
    readonly_fields = ['created_at']