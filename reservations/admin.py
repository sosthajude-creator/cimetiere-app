from django.contrib import admin
from .models import Reservation, Concession, Exhumation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = ['id', 'client', 'caveau', 'statut', 'defunt_nom', 'defunt_prenom', 'created_at']
    list_filter   = ['statut']
    search_fields = ['defunt_nom', 'defunt_prenom', 'client__email']
    readonly_fields = ['created_at', 'validee_le']

@admin.register(Concession)
class ConcessionAdmin(admin.ModelAdmin):
    list_display  = ['reservation', 'type_concess', 'date_debut', 'date_fin', 'renouvelee']
    list_filter   = ['type_concess', 'renouvelee']

@admin.register(Exhumation)
class ExhumationAdmin(admin.ModelAdmin):
    list_display  = ['id', 'concession', 'demandeur', 'statut', 'date_validation', 'created_at']
    list_filter   = ['statut']
    search_fields = ['demandeur__email']
    readonly_fields = ['created_at', 'date_validation']