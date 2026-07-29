from django.contrib import admin
from .models import Cimetiere, ZoneCimetiere, Bloc

@admin.register(Cimetiere)
class CimetiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'adresse', 'email_cimetiere', 'actif', 'created_at']
    search_fields = ['nom', 'adresse']

@admin.register(ZoneCimetiere)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['nom', 'cimetiere', 'superficie', 'exploitable']
    list_filter = ['exploitable', 'cimetiere']

@admin.register(Bloc)
class BlocAdmin(admin.ModelAdmin):
    list_display = ['nom', 'zone', 'created_at']
    list_filter = ['zone']