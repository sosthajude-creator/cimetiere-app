from ninja import Router, Schema
from typing import Optional
from django.utils import timezone
from datetime import datetime, timedelta
from jose import jwt
from django.conf import settings
from .models import User
import random
import string

router = Router()


class LoginSchema(Schema):
    email: str
    password: str


class MFASchema(Schema):
    email: str
    code: str


class UserCreateSchema(Schema):
    email: str
    password: str
    nom: str
    prenom: str
    telephone: Optional[str] = None
    role: str = 'client'
    email_cimetiere: Optional[str] = None


class AdminCreateSchema(Schema):
    email: str
    password: str
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email_cimetiere: str
    nom_cimetiere: str
    adresse_cimetiere: str
    ville_cimetiere: str
    latitude_cimetiere: float
    longitude_cimetiere: float
    superficie_cimetiere: float


def generate_token(user):
    payload = {
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def generate_mfa_code():
    return ''.join(random.choices(string.digits, k=6))


def send_mfa_email(user_email, code):
    """Envoie le code MFA par email"""
    try:
        from django.core.mail import send_mail
        
        sujet = "Votre code de verification - Gestion Cimetiere"
        message = f"""Bonjour,

Votre code de verification a 6 chiffres est :

========================
    CODE MFA : {code}
========================

Ce code est valable pendant 10 minutes.

Si vous n'avez pas demande ce code, veuillez ignorer cet email.

Cordialement,
Administration - Gestion de Cimetiere
Republique du Congo
"""
        
        send_mail(
            subject=sujet,
            message=message,
            from_email=f'Gestion Cimetiere <{settings.EMAIL_HOST_USER}>',
            recipient_list=[user_email],
            fail_silently=False,
        )
        print(f"✅ Email MFA envoyé à {user_email}")
        return True
    except Exception as ex:
        print(f"❌ ERREUR envoi email MFA : {str(ex)}")
        return False


@router.post("/login")
def login(request, data: LoginSchema):
    try:
        print(f"\n{'='*50}")
        print(f"🔍 Tentative de login pour: {data.email}")
        
        user = User.objects.get(email=data.email)
        print(f"✅ Utilisateur trouvé: {user.email}")
        
        if not user.check_password(data.password):
            print(f"❌ Mot de passe incorrect pour {user.email}")
            return {"error": "Email ou mot de passe incorrect"}

        print(f"✅ Mot de passe vérifié")
        
        if user.statut_validation == 'en_attente':
            print(f"⏳ Compte en attente de validation")
            return {"error": "Votre compte est en attente de validation par l'administrateur du cimetiere"}
        
        if user.statut_validation == 'rejete':
            print(f"🚫 Compte rejeté")
            return {"error": "Votre demande a ete rejetee. Contactez l'administrateur"}

        print(f"✅ Statut de validation: {user.statut_validation}")
        
        # Générer le code MFA
        code = generate_mfa_code()
        print(f"🔢 Code MFA généré: {code}")
        
        user.mfa_code = code
        user.mfa_expiry = timezone.now() + timedelta(minutes=10)
        user.save()
        print(f"💾 Code MFA sauvegardé en base")
        
        # Envoyer le code par email
        print(f"📧 Tentative d'envoi du code MFA à {user.email}")
        succes = send_mfa_email(user.email, code)
        print(f"{'✅' if succes else '❌'} Résultat envoi email: {succes}")
        
        if not succes:
            print(f"❌ Échec de l'envoi email")
            return {"error": "Impossible d'envoyer le code MFA par email. Verifiez votre adresse email ou contactez le support."}

        print(f"✅ Login réussi, code MFA envoyé")
        print(f"{'='*50}\n")
        
        return {"message": "Code MFA envoye par email. Verifiez votre boite de reception.", "email": user.email}
    except User.DoesNotExist:
        print(f"❌ Utilisateur non trouvé: {data.email}")
        return {"error": "Utilisateur non trouve"}
    except Exception as e:
        print(f"❌ ERREUR dans login: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Erreur serveur: {str(e)}"}


@router.post("/verify-mfa")
def verify_mfa(request, data: MFASchema):
    try:
        user = User.objects.get(email=data.email)
        if user.mfa_code != data.code:
            return {"error": "Code MFA incorrect"}
        if timezone.now() > user.mfa_expiry:
            return {"error": "Code MFA expire"}

        # ✅ CORRECTION 1 : Vérifier is_active avant de générer le token
        if not user.is_active:
            return {"error": "Votre compte n'est pas encore actif. Contactez l'administrateur."}

        user.mfa_code = None
        user.mfa_expiry = None
        user.save()
        token = generate_token(user)

        cimetiere_id = str(user.cimetiere.id) if hasattr(user, 'cimetiere') and user.cimetiere else None
        cimetiere_nom = user.cimetiere.nom if hasattr(user, 'cimetiere') and user.cimetiere else None

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "telephone": user.telephone,
                "role": user.role,
                "is_active": user.is_active,
                "email_cimetiere": user.email_cimetiere,
                "cimetiere_id": cimetiere_id,
                "cimetiere_nom": cimetiere_nom,
            }
        }
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouve"}


@router.post("/register")
def register(request, data: UserCreateSchema):
    if User.objects.filter(email=data.email).exists():
        return {"error": "Email deja utilise"}

    cimetiere = None
    statut = 'valide'

    if data.role == 'client':
        statut = 'valide'
    elif data.role in ['agent', 'secretariat']:
        statut = 'en_attente'
        if data.email_cimetiere:
            try:
                from etablissements.models import Cimetiere
                cimetiere = Cimetiere.objects.get(email_cimetiere=data.email_cimetiere, actif=True)
                for admin in cimetiere.admins.all():
                    try:
                        from django.core.mail import send_mail
                        send_mail(
                            subject='Nouvelle demande de poste - ' + cimetiere.nom,
                            message='Une nouvelle demande de poste (' + data.role + ') a ete soumise par ' + data.prenom + ' ' + data.nom + ' (' + data.email + ').',
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[admin.email],
                            fail_silently=True,
                        )
                    except:
                        pass
            except Exception:
                return {"error": "Aucun cimetiere trouve avec cet email."}

    # ✅ CORRECTION 2 : Mettre is_active=False pour les comptes en attente
    is_actif = True if statut == 'valide' else False

    user = User.objects.create(
        email=data.email,
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone or '',
        role=data.role,
        email_cimetiere=data.email_cimetiere,
        cimetiere=cimetiere,
        statut_validation=statut,
        is_active=is_actif,  # ✅ AJOUTÉ
    )
    user.set_password(data.password)
    user.save()

    if statut == 'valide':
        return {"message": "Compte cree avec succes ! Vous pouvez vous connecter."}
    else:
        return {"message": "Demande soumise ! En attente de validation."}


@router.post("/register-admin")
def register_admin(request, data: AdminCreateSchema):
    if User.objects.filter(email=data.email).exists():
        return {"error": "Email deja utilise"}

    user = User.objects.create(
        email=data.email,
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone or '',
        role='admin',
        email_cimetiere=data.email_cimetiere,
        statut_validation='valide',
        is_active=True,  # ✅ Admin toujours actif
    )
    user.set_password(data.password)
    user.save()

    from etablissements.models import Cimetiere
    cimetiere = Cimetiere.objects.create(
        nom=data.nom_cimetiere,
        adresse=data.adresse_cimetiere,
        latitude=data.latitude_cimetiere,
        longitude=data.longitude_cimetiere,
        superficie=data.superficie_cimetiere,
        email_cimetiere=data.email_cimetiere,
        ville=data.ville_cimetiere,
    )
    cimetiere.admins.add(user)
    cimetiere.save()

    user.cimetiere = cimetiere
    user.save()

    return {
        "message": "Compte admin et cimetiere crees avec succes !",
        "cimetiere_id": str(cimetiere.id)
    }


@router.get("/users")
def list_users(request):
    users = User.objects.select_related('cimetiere').all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "nom": u.nom,
            "prenom": u.prenom,
            "role": u.role,
            "is_active": u.is_active,
            "statut_validation": u.statut_validation,
            "email_cimetiere": u.email_cimetiere,
            "cimetiere_id": str(u.cimetiere.id) if u.cimetiere else None,
            "cimetiere_nom": u.cimetiere.nom if u.cimetiere else None,
        }
        for u in users
    ]


@router.put("/users/{user_id}/valider")
def valider_user(request, user_id: str, statut: str):
    try:
        user = User.objects.get(id=user_id)
        user.statut_validation = statut
        
        # ✅ CORRECTION 3 : Mettre is_active=True quand validé
        if statut == 'valide':
            user.is_active = True
        elif statut == 'rejete':
            user.is_active = False
        
        user.save()

        if statut == 'valide':
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject='Votre compte a ete valide',
                    message='Bonjour ' + user.prenom + ',\n\nVotre compte a ete valide. Vous pouvez maintenant vous connecter.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except:
                pass
        return {"message": "Utilisateur " + statut}
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouve"}


@router.put("/users/{user_id}/role")
def update_role(request, user_id: str, role: str):
    try:
        user = User.objects.get(id=user_id)
        user.role = role
        user.save()
        return {"message": "Role mis a jour"}
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouve"}


@router.put("/users/{user_id}/activer")
def toggle_actif(request, user_id: str):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        statut = "active" if user.is_active else "desactive"
        return {"message": "Utilisateur " + statut}
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouve"}


@router.get("/en-attente")
def users_en_attente(request, cimetiere_id: str = None):
    qs = User.objects.filter(statut_validation='en_attente').select_related('cimetiere')
    if cimetiere_id:
        qs = qs.filter(cimetiere_id=cimetiere_id)
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "nom": u.nom,
            "prenom": u.prenom,
            "role": u.role,
            "email_cimetiere": u.email_cimetiere,
            "cimetiere_id": str(u.cimetiere.id) if u.cimetiere else None,
            "cimetiere_nom": u.cimetiere.nom if u.cimetiere else None,
        }
        for u in qs
    ]