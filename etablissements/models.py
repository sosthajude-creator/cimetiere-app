from django.db import models
from users.models import User
import uuid

class Cimetiere(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom           = models.CharField(max_length=200)
    adresse       = models.CharField(max_length=300)
    ville         = models.CharField(max_length=100, default="Brazzaville")  # ✅ NOUVEAU
    latitude      = models.FloatField()
    longitude     = models.FloatField()
    superficie    = models.FloatField(help_text="En m²")
    email_cimetiere = models.EmailField(unique=True)
    admins        = models.ManyToManyField(User, related_name='cimetieres_geres', blank=True)
    actif         = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class ZoneCimetiere(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom        = models.CharField(max_length=100)
    cimetiere  = models.ForeignKey(Cimetiere, on_delete=models.CASCADE, related_name='zones')
    superficie = models.FloatField(help_text="En m²", default=0)
    exploitable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom + " — " + self.cimetiere.nom


class Bloc(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom        = models.CharField(max_length=100)
    zone       = models.ForeignKey(ZoneCimetiere, on_delete=models.CASCADE, related_name='blocs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom + " — " + self.zone.nom