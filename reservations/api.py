from ninja import Router, Schema
from typing import Optional
from django.utils import timezone
from datetime import date, timedelta
from .models import Reservation, Concession, Exhumation
from caveaux.models import Caveau, AuditCaveau
from users.models import User

router = Router()

# --- Schémas ---
class ReservationSchema(Schema):
    client_email: str
    caveau_id: str
    defunt_nom: str
    defunt_prenom: str
    defunt_deces: str
    type_concession: str = 'temporaire'
    date_fin: Optional[str] = None

class ValidationSchema(Schema):
    admin_email: str
    statut: str  # 'validee', 'rejetee' ou 'annulee'

class ExhumationSchema(Schema):
    concession_id: str
    demandeur_email: str
    motif: str

class ValidationExhumationSchema(Schema):
    admin_email: str
    statut: str  # 'validee' ou 'rejetee'


# ==========================================
# 1. GESTION DES RÉSERVATIONS
# ==========================================
@router.get("/")
def list_reservations(request):
    reservations = Reservation.objects.select_related(
        'client', 'caveau', 'validee_par'
    ).all()
    return [
        {
            "id": str(r.id),
            "client": f"{r.client.prenom} {r.client.nom}" if r.client else "N/A",
            "client_email": r.client.email if r.client else "",
            "caveau": r.caveau.numero if r.caveau else "N/A",
            "cimetiere_id": str(r.caveau.cimetiere.id) if r.caveau and r.caveau.cimetiere else None,
            "statut": r.statut,
            "defunt_nom": r.defunt_nom,
            "defunt_prenom": r.defunt_prenom,
            "defunt_deces": str(r.defunt_deces),
            "created_at": str(r.created_at),
        }
        for r in reservations
    ]

@router.post("/")
def create_reservation(request, data: ReservationSchema):
    try:
        client = User.objects.get(email=data.client_email)
        caveau = Caveau.objects.get(id=data.caveau_id)

        if caveau.statut != 'disponible':
            return {"error": "Ce caveau n'est pas disponible"}

        reservation = Reservation.objects.create(
            client=client,
            caveau=caveau,
            defunt_nom=data.defunt_nom,
            defunt_prenom=data.defunt_prenom,
            defunt_deces=date.fromisoformat(data.defunt_deces),
            statut='en_attente',
        )

        # Passer le caveau en réservé (orange)
        AuditCaveau.objects.create(
            caveau=caveau,
            modifie_par=client,
            ancien_statut=caveau.statut,
            nouveau_statut='reserve',
        )
        caveau.statut = 'reserve'
        caveau.save()

        # Créer la concession associée
        date_fin = None
        if data.date_fin:
            date_fin = date.fromisoformat(data.date_fin)
        elif data.type_concession == 'temporaire':
            # Par défaut 20 ans si temporaire et pas de date spécifiée
            date_fin = date.today() + timedelta(days=365*20)

        Concession.objects.create(
            reservation=reservation,
            type_concess=data.type_concession,
            date_debut=date.today(),
            date_fin=date_fin,
        )

        return {
            "message": "Réservation créée avec succès",
            "id": str(reservation.id)
        }

    except User.DoesNotExist:
        return {"error": "Client non trouvé"}
    except Caveau.DoesNotExist:
        return {"error": "Caveau non trouvé"}
    except Exception as e:
        return {"error": str(e)}

@router.put("/{reservation_id}/valider")
def valider_reservation(request, reservation_id: str, data: ValidationSchema):
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        admin = User.objects.get(email=data.admin_email)

        if admin.role not in ['admin', 'superadmin', 'secretariat']:
            return {"error": "Permission refusee"}

        reservation.statut = data.statut
        reservation.validee_par = admin
        reservation.validee_le = timezone.now()
        reservation.save()

        caveau = reservation.caveau
        
        if data.statut == 'validee':
            AuditCaveau.objects.create(
                caveau=caveau,
                modifie_par=admin,
                ancien_statut=caveau.statut,
                nouveau_statut='occupe',
            )
            caveau.statut = 'occupe'
            caveau.save()

            # Créer automatiquement la facture si elle n'existe pas
            from finances.models import Facture
            try:
                facture = reservation.facture
            except:
                facture = Facture.objects.create(
                    reservation=reservation,
                    montant=75000,
                )

            # Générer le PDF et envoyer par email
            try:
                from finances.services import generer_facture_pdf
                chemin, nom_fichier = generer_facture_pdf(facture)
                facture.pdf_path = chemin
                facture.save()

                try:
                    from django.core.mail import EmailMessage
                    email = EmailMessage(
                        subject='Facture - Gestion de Cimetiere',
                        body=f'Bonjour {reservation.client.prenom},\n\nVotre reservation a ete validee. Veuillez trouver en piece jointe votre facture.\n\nMontant : 75 000 FCFA\n\nCordialement,\nAdministration du Cimetiere',
                        from_email='sosthajude@gmail.com',
                        to=[reservation.client.email],
                    )
                    email.attach_file(chemin)
                    email.send(fail_silently=True)
                except:
                    pass
            except Exception as ex:
                print("Erreur PDF : " + str(ex))

        else: # Rejetée ou Annulée
            AuditCaveau.objects.create(
                caveau=caveau,
                modifie_par=admin,
                ancien_statut=caveau.statut,
                nouveau_statut='disponible',
            )
            caveau.statut = 'disponible'
            caveau.save()

        return {"message": "Reservation " + data.statut + " avec succes"}

    except Reservation.DoesNotExist:
        return {"error": "Reservation non trouvee"}
    except User.DoesNotExist:
        return {"error": "Administrateur non trouve"}
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# 2. GESTION DES CONCESSIONS
# ==========================================
@router.get("/concessions")
def list_concessions(request):
    concessions = Concession.objects.select_related(
        'reservation', 
        'reservation__client',
        'reservation__caveau',
    ).all()
    
    result = []
    for c in concessions:
        # ✅ Calcul automatique de l'expiration pour le frontend
        est_expiree = False
        if c.type_concess == 'temporaire' and c.date_fin:
            est_expiree = date.today() > c.date_fin
            
        result.append({
            "id": str(c.id),
            "reservation_id": str(c.reservation.id),
            "caveau": c.reservation.caveau.numero if c.reservation.caveau else "N/A",
            "client": f"{c.reservation.client.prenom} {c.reservation.client.nom}" if c.reservation.client else "N/A",
            "client_email": c.reservation.client.email if c.reservation.client else "",
            "defunt_nom": c.reservation.defunt_nom,
            "defunt_prenom": c.reservation.defunt_prenom,
            "type_concess": c.type_concess,
            "date_debut": str(c.date_debut),
            "date_fin": str(c.date_fin) if c.date_fin else "Perpetuelle",
            "renouvelee": getattr(c, 'renouvelee', False),
            "est_expiree": est_expiree, # ✅ Champ crucial pour afficher/masquer le bouton Exhumer
        })
    return result

@router.put("/{reservation_id}/renouveler")
def renouveler_concession(request, reservation_id: str, data: ValidationSchema):
    """Prolonge une concession temporaire de 20 ans"""
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        admin = User.objects.get(email=data.admin_email)

        if admin.role not in ['admin', 'superadmin', 'secretariat']:
            return {"error": "Permission refusee"}

        try:
            concession = Concession.objects.get(reservation=reservation)
        except Concession.DoesNotExist:
            return {"error": "Concession non trouvee pour cette reservation"}

        if concession.type_concess != 'temporaire':
            return {"error": "Seules les concessions temporaires peuvent etre renouvelees"}

        # ✅ Prolonger la date de fin de 20 ans
        if concession.date_fin:
            concession.date_fin = concession.date_fin + timedelta(days=365*20)
        else:
            concession.date_fin = date.today() + timedelta(days=365*20)
            
        # Si le modèle a un champ 'renouvelee', on le met à jour
        if hasattr(concession, 'renouvelee'):
            concession.renouvelee = True
        concession.save()

        return {"message": "Concession renouvelee pour 20 ans supplementaires"}

    except Reservation.DoesNotExist:
        return {"error": "Reservation non trouvee"}
    except User.DoesNotExist:
        return {"error": "Administrateur non trouve"}
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# 3. GESTION DES EXHUMATIONS
# ==========================================
@router.get("/exhumations")
def list_exhumations(request):
    exhumations = Exhumation.objects.select_related(
        'concession', 'demandeur', 'validee_par'
    ).all().order_by('-created_at')
    
    return [
        {
            "id": str(e.id),
            "concession": str(e.concession.id),
            "demandeur": f"{e.demandeur.prenom} {e.demandeur.nom}" if e.demandeur else "N/A",
            "motif": e.motif,
            "statut": e.statut,
            "date_validation": str(e.date_validation) if e.date_validation else None,
            "created_at": str(e.created_at),
        }
        for e in exhumations
    ]

@router.post("/exhumations")
def create_exhumation(request, data: ExhumationSchema):
    try:
        concession = Concession.objects.get(id=data.concession_id)
        demandeur = User.objects.get(email=data.demandeur_email)

        # ✅ Vérification 1 : La réservation associée doit être validée
        if concession.reservation.statut != 'validee':
            return {"error": "Cette reservation n'est pas validee"}

        # ✅ Vérification 2 : Si temporaire, la concession doit être expirée
        if concession.type_concess == 'temporaire' and concession.date_fin:
            if date.today() <= concession.date_fin:
                jours_restants = (concession.date_fin - date.today()).days
                return {"error": f"La concession n'est pas encore expiree. Il reste {jours_restants} jours."}

        # ✅ Vérification 3 : Pas de demande en attente pour cette concession
        if Exhumation.objects.filter(concession=concession, statut='en_attente').exists():
            return {"error": "Une demande d'exhumation est deja en attente pour cette concession"}

        exhumation = Exhumation.objects.create(
            concession=concession,
            demandeur=demandeur,
            motif=data.motif,
            statut='en_attente'
        )
        return {
            "message": "Demande d'exhumation créée avec succes",
            "id": str(exhumation.id)
        }
    except Concession.DoesNotExist:
        return {"error": "Concession non trouvee"}
    except User.DoesNotExist:
        return {"error": "Demandeur non trouve"}
    except Exception as e:
        return {"error": str(e)}

@router.put("/exhumations/{exhumation_id}/valider")
def valider_exhumation(request, exhumation_id: str, data: ValidationExhumationSchema):
    try:
        exhumation = Exhumation.objects.get(id=exhumation_id)
        admin = User.objects.get(email=data.admin_email)

        if admin.role not in ['admin', 'superadmin']:
            return {"error": "Permission refusee"}

        if exhumation.statut != 'en_attente':
            return {"error": "Cette demande a deja ete traitee"}

        exhumation.statut = data.statut
        exhumation.validee_par = admin
        exhumation.date_validation = timezone.now()
        exhumation.save()

        # ✅ Si validée : on libère le caveau (statut inexploitable pour nettoyage)
        if data.statut == 'validee':
            reservation = exhumation.concession.reservation
            if reservation.caveau:
                AuditCaveau.objects.create(
                    caveau=reservation.caveau,
                    modifie_par=admin,
                    ancien_statut=reservation.caveau.statut,
                    nouveau_statut='inexploitable',
                )
                reservation.caveau.statut = 'inexploitable'
                reservation.caveau.save()
            
            # La réservation est annulée
            reservation.statut = 'annulee'
            reservation.save()
            
            return {"message": "Exhumation validee. Le caveau a ete libere pour nettoyage."}

        return {"message": f"Exhumation {data.statut} avec succes"}

    except Exhumation.DoesNotExist:
        return {"error": "Exhumation non trouvee"}
    except User.DoesNotExist:
        return {"error": "Administrateur non trouve"}
    except Exception as e:
        return {"error": str(e)}