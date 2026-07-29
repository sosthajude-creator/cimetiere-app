from django.db import models
from users.models import User
from reservations.models import Reservation
import uuid

class Facture(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        PARTIELLE  = 'partielle',  'Partielle'
        PAYEE      = 'payee',      'Payée'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='facture')
    montant     = models.DecimalField(max_digits=10, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut      = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    pdf_path    = models.CharField(max_length=255, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    @property
    def montant_restant(self):
        return self.montant - self.montant_paye

    def __str__(self):
        return f"Facture {self.id} — {self.statut}"


class Paiement(models.Model):
    class Canal(models.TextChoices):
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        AIRTEL_MONEY = 'airtel_money', 'Airtel Money'
        ESPECES      = 'especes',      'Espèces'
        VIREMENT     = 'virement',     'Virement'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facture    = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant    = models.DecimalField(max_digits=10, decimal_places=2)
    canal      = models.CharField(max_length=20, choices=Canal.choices)
    reference  = models.CharField(max_length=100, blank=True)
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} via {self.canal}"


class AlerteFinanciere(models.Model):
    class Type(models.TextChoices):
        RETARD_PAIEMENT = 'retard_paiement', 'Retard de paiement'
        SEUIL_CRITIQUE  = 'seuil_critique',  'Seuil critique de places'
        ECHEANCE        = 'echeance',         'Échéance concession'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_alerte = models.CharField(max_length=30, choices=Type.choices)
    message    = models.TextField()
    lu         = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerte {self.type_alerte} — {self.created_at}"