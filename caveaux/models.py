from django.db import models
from etablissements.models import Bloc
import uuid

class Caveau(models.Model):
    class Statut(models.TextChoices):
        DISPONIBLE    = 'disponible',    'Disponible'
        RESERVE       = 'reserve',       'Réservé'
        OCCUPE        = 'occupe',        'Occupé'
        INEXPLOITABLE = 'inexploitable', 'Inexploitable'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bloc       = models.ForeignKey(Bloc, on_delete=models.CASCADE, related_name='caveaux', null=True, blank=True)
    numero     = models.CharField(max_length=20, unique=True)
    latitude   = models.FloatField()
    longitude  = models.FloatField()
    longueur   = models.FloatField(help_text="En mètres")
    largeur    = models.FloatField(help_text="En mètres")
    prix       = models.DecimalField(max_digits=10, decimal_places=2, default=75000)
    statut     = models.CharField(max_length=20, choices=Statut.choices, default=Statut.DISPONIBLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def zone(self):
        return self.bloc.zone

    @property
    def cimetiere(self):
        return self.bloc.zone.cimetiere

    def __str__(self):
        return "Caveau " + self.numero + " — " + self.statut


class AuditCaveau(models.Model):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caveau            = models.ForeignKey(Caveau, on_delete=models.CASCADE, related_name='audits')
    modifie_par       = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    ancien_statut     = models.CharField(max_length=20)
    nouveau_statut    = models.CharField(max_length=20)
    date_modification = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Audit " + str(self.caveau) + " : " + self.ancien_statut + " -> " + self.nouveau_statut