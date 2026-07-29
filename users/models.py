from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        extra_fields.setdefault('statut_validation', 'valide')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN   = 'superadmin',   'Super Administrateur'
        ADMIN        = 'admin',        'Administrateur'
        AGENT        = 'agent',        'Agent de terrain'
        SECRETARIAT  = 'secretariat',  'Secrétariat'
        CLIENT       = 'client',       'Client'

    class StatutValidation(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        VALIDE     = 'valide',     'Validé'
        REJETE     = 'rejete',     'Rejeté'

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email               = models.EmailField(unique=True)
    nom                 = models.CharField(max_length=100)
    prenom              = models.CharField(max_length=100)
    telephone           = models.CharField(max_length=20, blank=True)
    role                = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    email_cimetiere     = models.EmailField(blank=True, null=True)

    # ✅ NOUVEAU : lien direct vers le cimetière (pour agent/secretariat/admin)
    cimetiere           = models.ForeignKey(
        'etablissements.Cimetiere',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='personnels'
    )


    statut_validation   = models.CharField(max_length=20, choices=StatutValidation.choices, default=StatutValidation.VALIDE)
    is_active           = models.BooleanField(default=True)
    is_staff            = models.BooleanField(default=False)
    mfa_code            = models.CharField(max_length=6, blank=True, null=True)
    mfa_expiry          = models.DateTimeField(blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    objects = UserManager()

    def __str__(self):
        return self.prenom + " " + self.nom + " (" + self.role + ")"

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN

    @property
    def can_access_admin(self):
        return self.role in ['superadmin', 'admin', 'agent', 'secretariat']