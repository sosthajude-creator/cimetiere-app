from django.db import models
from users.models import User
import uuid

class Notification(models.Model):
    class Type(models.TextChoices):
        MFA             = 'mfa',             'Code MFA'
        RESERVATION     = 'reservation',     'Confirmation réservation'
        VALIDATION      = 'validation',      'Validation réservation'
        FACTURE         = 'facture',         'Facture générée'
        PAIEMENT        = 'paiement',        'Paiement reçu'
        ECHEANCE        = 'echeance',        'Échéance concession'
        RETARD          = 'retard',          'Retard de paiement'
        EXHUMATION      = 'exhumation',      'Demande exhumation'
        SEUIL_CRITIQUE  = 'seuil_critique',  'Seuil places critique'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notif  = models.CharField(max_length=30, choices=Type.choices)
    sujet       = models.CharField(max_length=200)
    message     = models.TextField()
    lu          = models.BooleanField(default=False)
    envoye_par_email = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.type_notif} → {self.destinataire}"