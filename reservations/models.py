from django.db import models
from users.models import User
from caveaux.models import Caveau
from etablissements.models import Cimetiere
import uuid

class Reservation(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        VALIDEE    = 'validee',    'Validée'
        REJETEE    = 'rejetee',    'Rejetée'
        ANNULEE    = 'annulee',    'Annulée'

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    caveau        = models.ForeignKey(Caveau, on_delete=models.CASCADE, related_name='reservations')
    cimetiere     = models.ForeignKey(Cimetiere, on_delete=models.CASCADE, related_name='reservations', null=True)
    statut        = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    defunt_nom    = models.CharField(max_length=100)
    defunt_prenom = models.CharField(max_length=100)
    defunt_deces  = models.DateField()
    validee_par   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validations')
    validee_le    = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Reservation " + str(self.id) + " — " + self.statut


class Concession(models.Model):
    class Type(models.TextChoices):
        TEMPORAIRE  = 'temporaire',  'Temporaire'
        PERPETUELLE = 'perpetuelle', 'Perpétuelle'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation  = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    type_concess = models.CharField(max_length=20, choices=Type.choices)
    date_debut   = models.DateField()
    date_fin     = models.DateField(null=True, blank=True)
    renouvelee   = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Concession " + self.type_concess + " — " + str(self.reservation)


class Exhumation(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        VALIDEE    = 'validee',    'Validée'
        REJETEE    = 'rejetee',    'Rejetée'

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    concession        = models.ForeignKey(Concession, on_delete=models.CASCADE, related_name='exhumations')
    demandeur         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exhumations')
    motif             = models.TextField()
    statut            = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    validee_par       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exhumations_validees')
    date_validation   = models.DateTimeField(null=True, blank=True)
    autorisation_pdf  = models.CharField(max_length=255, blank=True)
    proces_verbal_pdf = models.CharField(max_length=255, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Exhumation " + str(self.id) + " — " + self.statut