from ninja import Router, Schema
from typing import Optional
from django.http import FileResponse
from django.db import transaction
from .models import Facture, Paiement, AlerteFinanciere
from reservations.models import Reservation
from users.models import User
import random
import string
import os

router = Router()


class FactureSchema(Schema):
    reservation_id: str
    montant: float


class PaiementRequestSchema(Schema):
    facture_id: str
    montant: float
    canal: str
    numero_telephone: Optional[str] = None
    numero_carte: Optional[str] = None
    enregistre_par_email: str


def generer_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def simuler_paiement_backend(canal, montant, numero=None):
    """Simule un paiement (95% de succès)"""
    import time
    time.sleep(0.5)
    succes = random.random() < 0.95
    if not succes:
        return False, "Transaction refusee par l'operateur"
    messages = {
        'mobile_money': f"Paiement MTN Mobile Money de {montant} FCFA accepte",
        'airtel_money': f"Paiement Airtel Money de {montant} FCFA accepte",
        'wave': f"Paiement Wave de {montant} FCFA accepte",
        'orange_money': f"Paiement Orange Money de {montant} FCFA accepte",
        'especes': f"Paiement en especes de {montant} FCFA enregistre",
        'virement': f"Virement bancaire de {montant} FCFA confirme",
        'carte_bancaire': f"Paiement par carte de {montant} FCFA accepte",
    }
    return True, messages.get(canal, f"Paiement de {montant} FCFA accepte")


@router.get("/")
def list_factures(request, client_email: str = None, cimetiere_id: str = None):
    factures = Facture.objects.select_related('reservation__client').all()
    
    if client_email:
        factures = factures.filter(reservation__client__email=client_email)
    
    if cimetiere_id:
        factures = factures.filter(reservation__caveau__bloc__zone__cimetiere_id=cimetiere_id)
    
    return [
        {
            "id": str(f.id),
            "reservation": str(f.reservation.id),
            "client": f"{f.reservation.client.prenom} {f.reservation.client.nom}",
            "client_email": f.reservation.client.email,
            "montant": float(f.montant),
            "montant_paye": float(f.montant_paye),
            "montant_restant": float(f.montant_restant),
            "statut": f.statut,
            "created_at": str(f.created_at),
        }
        for f in factures
    ]


@router.post("/")
def create_facture(request, data: FactureSchema):
    try:
        reservation = Reservation.objects.get(id=data.reservation_id)
        if hasattr(reservation, 'facture'):
            return {"error": "Une facture existe deja"}
        facture = Facture.objects.create(reservation=reservation, montant=data.montant)
        return {"message": "Facture creee", "id": str(facture.id)}
    except Reservation.DoesNotExist:
        return {"error": "Reservation non trouvee"}


@router.post("/{facture_id}/generer-pdf")
def generer_pdf(request, facture_id: str):
    try:
        from .services import generer_facture_pdf
        facture = Facture.objects.get(id=facture_id)
        chemin, nom_fichier = generer_facture_pdf(facture)
        facture.pdf_path = chemin
        facture.save()
        return {"message": "Facture PDF generee", "fichier": nom_fichier}
    except Facture.DoesNotExist:
        return {"error": "Facture non trouvee"}
    except Exception as ex:
        return {"error": str(ex)}


@router.get("/{facture_id}/telecharger-pdf")
def telecharger_pdf(request, facture_id: str):
    try:
        facture = Facture.objects.get(id=facture_id)
        if not facture.pdf_path or not os.path.exists(facture.pdf_path):
            from .services import generer_facture_pdf
            chemin, nom_fichier = generer_facture_pdf(facture)
            facture.pdf_path = chemin
            facture.save()
        if not os.path.exists(facture.pdf_path):
            return {"error": "Fichier introuvable"}
        return FileResponse(open(facture.pdf_path, 'rb'), as_attachment=True, filename=f"facture_{str(facture.id)[:8].upper()}.pdf")
    except Facture.DoesNotExist:
        return {"error": "Facture non trouvee"}


# ✅ ENDPOINT CORRIGÉ - Ne modifie PAS montant_restant (c'est une property)
@router.post("/simuler-paiement")
def simuler_paiement_api(request, data: PaiementRequestSchema):
    """Endpoint pour simuler un paiement"""
    try:
        print(f"\n{'='*50}")
        print(f"📝 DONNÉES REÇUES:")
        print(f"   - Facture ID: {data.facture_id}")
        print(f"   - Montant: {data.montant}")
        print(f"   - Canal: {data.canal}")
        print(f"   - Email: {data.enregistre_par_email}")
        print(f"{'='*50}")
        
        print(f"🔍 Recherche de la facture: {data.facture_id}")
        facture = Facture.objects.get(id=data.facture_id)
        print(f"✅ Facture trouvée: {facture.id}")
        print(f"   - Montant total: {facture.montant}")
        print(f"   - Montant payé: {facture.montant_paye}")
        print(f"   - Montant restant: {facture.montant_restant}")
        print(f"   - Statut: {facture.statut}")
        
        enregistre_par = User.objects.get(email=data.enregistre_par_email)
        print(f"✅ Utilisateur trouvé: {enregistre_par.email}")
        
        # Vérifier si la facture est déjà payée
        if facture.statut == 'payee':
            print(f"❌ Facture déjà payée!")
            return {"error": "Cette facture est deja payee en totalite"}
        
        # Vérifier le montant
        montant_restant = float(facture.montant_restant)
        if data.montant > montant_restant:
            return {"error": f"Montant superieur au reste a payer ({montant_restant} FCFA)"}
        
        if data.montant <= 0:
            return {"error": "Montant invalide"}
        
        # Simuler le paiement
        print(f"🔄 Simulation du paiement de {data.montant} FCFA via {data.canal}...")
        succes, message = simuler_paiement_backend(data.canal, data.montant, data.numero_telephone or data.numero_carte)
        
        if not succes:
            print(f"❌ Paiement refusé: {message}")
            return {"error": message, "succes": False}
        
        print(f"✅ Paiement simulé avec succès!")
        
        # ✅ UTILISER transaction.atomic() pour garantir la sauvegarde
        with transaction.atomic():
            # Créer le paiement
            reference = generer_reference()
            print(f"📝 Création du paiement: {reference}")
            
            paiement = Paiement.objects.create(
                facture=facture,
                montant=data.montant,
                canal=data.canal,
                reference=reference,
                enregistre_par=enregistre_par
            )
            print(f"✅ Paiement créé en base: ID={paiement.id}")
            
            # ✅ Mettre à jour SEULEMENT montant_paye
            ancien_montant_paye = float(facture.montant_paye)
            nouveau_montant_paye = ancien_montant_paye + data.montant
            
            print(f"💰 Mise à jour facture:")
            print(f"   - Ancien payé: {ancien_montant_paye}")
            print(f"   - Nouveau payé: {nouveau_montant_paye}")
            
            facture.montant_paye = nouveau_montant_paye
            
            # ✅ Déterminer le statut
            if nouveau_montant_paye >= float(facture.montant):
                facture.statut = 'payee'
                print(f"   - Statut: PAYÉE")
            else:
                facture.statut = 'partielle'
                print(f"   - Statut: PARTIELLE")
            
            facture.save()
            print(f"✅ Facture sauvegardée en base!")
            
            # Recharger pour voir les valeurs recalculées
            facture.refresh_from_db()
            print(f"🔄 Rechargé depuis DB:")
            print(f"   - Montant payé: {facture.montant_paye}")
            print(f"   - Montant restant: {facture.montant_restant}")
            print(f"   - Statut: {facture.statut}")
        
        # Générer le PDF si payée
        if facture.statut == 'payee':
            try:
                from .services import generer_facture_pdf
                chemin, nom = generer_facture_pdf(facture)
                facture.pdf_path = chemin
                facture.save()
                print(f"📄 PDF généré: {chemin}")
            except Exception as ex:
                print(f"⚠️ Erreur génération PDF: {ex}")
        
        print(f"{'='*50}")
        print(f"✅ PAIEMENT TERMINÉ AVEC SUCCÈS")
        print(f"{'='*50}\n")
        
        return {
            "succes": True,
            "message": message,
            "reference": reference,
            "montant_paye": float(facture.montant_paye),
            "montant_restant": float(facture.montant_restant),
            "statut_facture": facture.statut
        }
        
    except Facture.DoesNotExist:
        print(f"❌ Facture non trouvée: {data.facture_id}")
        return {"error": "Facture non trouvee"}
    except User.DoesNotExist:
        print(f"❌ Utilisateur non trouvé: {data.enregistre_par_email}")
        return {"error": "Utilisateur non trouve"}
    except Exception as ex:
        print(f"❌ ERREUR: {str(ex)}")
        import traceback
        traceback.print_exc()
        return {"error": str(ex)}


# ✅ STATISTIQUES CORRIGÉES
@router.get("/statistiques")
def statistiques_financieres(request):
    from django.db.models import Sum
    
    # Calculer depuis les factures (plus fiable)
    total_revenus = Facture.objects.aggregate(total=Sum('montant_paye'))['total'] or 0
    
    stats = {
        "total_factures": Facture.objects.count(),
        "total_revenus": float(total_revenus),
        "factures_payees": Facture.objects.filter(statut='payee').count(),
        "factures_partielles": Facture.objects.filter(statut='partielle').count(),
        "factures_en_attente": Facture.objects.filter(statut='en_attente').count(),
    }
    
    print(f"📊 Statistiques financières: {stats}")
    return stats


@router.get("/alertes")
def list_alertes(request):
    alertes = AlerteFinanciere.objects.filter(lu=False).order_by('-created_at')
    return [{"id": str(a.id), "type_alerte": a.type_alerte, "message": a.message, "created_at": str(a.created_at)} for a in alertes]