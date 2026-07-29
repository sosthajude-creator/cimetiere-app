import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

# Vérifie si un superuser existe déjà
if not User.objects.filter(email='sosthajude@gmail.com').exists():
    User.objects.create_superuser(
        email='sosthajude@gmail.com',
        password='1234',
        nom='Amboulo',
        prenom='Sostha',
        role='superadmin',
        email_cimetiere='sosthajude@gmail.com',
        statut_validation='valide',
        is_active=True
    )
    print("✅ Superuser créé : sosthajude@gmail.com / 1234")
else:
    print("ℹ️ Le superuser existe déjà.")