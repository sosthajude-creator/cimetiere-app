from ninja import Router, Schema
from typing import Optional
from .models import Cimetiere, ZoneCimetiere, Bloc
from users.models import User

router = Router()


class CimetiereSchema(Schema):
    nom: str
    adresse: str
    latitude: float
    longitude: float
    superficie: float
    email_cimetiere: str
    admin_email: str


class ZoneSchema(Schema):
    nom: str
    cimetiere_id: str
    superficie: float = 0
    exploitable: bool = True


class BlocSchema(Schema):
    nom: str
    zone_id: str


@router.get("/")
def list_cimetieres(request):
    cimetieres = Cimetiere.objects.filter(actif=True)
    return [
        {
            "id": str(c.id),
            "nom": c.nom,
            "adresse": c.adresse,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "superficie": c.superficie,
            "email_cimetiere": c.email_cimetiere,
        }
        for c in cimetieres
    ]


@router.post("/")
def create_cimetiere(request, data: CimetiereSchema):
    try:
        admin = User.objects.get(email=data.admin_email)
        cimetiere = Cimetiere.objects.create(
            nom=data.nom,
            adresse=data.adresse,
            latitude=data.latitude,
            longitude=data.longitude,
            superficie=data.superficie,
            email_cimetiere=data.email_cimetiere,
        )
        cimetiere.admins.add(admin)
        cimetiere.save()
        return {"message": "Cimetiere cree", "id": str(cimetiere.id)}
    except User.DoesNotExist:
        return {"error": "Admin non trouve"}


@router.get("/{cimetiere_id}/zones")
def list_zones(request, cimetiere_id: str):
    try:
        cimetiere = Cimetiere.objects.get(id=cimetiere_id)
        zones = cimetiere.zones.all()
        return [
            {
                "id": str(z.id),
                "nom": z.nom,
                "superficie": z.superficie,
                "exploitable": z.exploitable,
                "blocs": [
                    {"id": str(b.id), "nom": b.nom}
                    for b in z.blocs.all()
                ]
            }
            for z in zones
        ]
    except Cimetiere.DoesNotExist:
        return {"error": "Cimetiere non trouve"}


@router.post("/zones")
def create_zone(request, data: ZoneSchema):
    try:
        cimetiere = Cimetiere.objects.get(id=data.cimetiere_id)
        zone = ZoneCimetiere.objects.create(
            nom=data.nom,
            cimetiere=cimetiere,
            superficie=data.superficie,
            exploitable=data.exploitable,
        )
        return {"message": "Zone creee", "id": str(zone.id)}
    except Cimetiere.DoesNotExist:
        return {"error": "Cimetiere non trouve"}


@router.post("/blocs")
def create_bloc(request, data: BlocSchema):
    try:
        zone = ZoneCimetiere.objects.get(id=data.zone_id)
        bloc = Bloc.objects.create(nom=data.nom, zone=zone)
        return {"message": "Bloc cree", "id": str(bloc.id)}
    except ZoneCimetiere.DoesNotExist:
        return {"error": "Zone non trouvee"}


@router.get("/{cimetiere_id}/caveaux")
def caveaux_par_cimetiere(request, cimetiere_id: str):
    try:
        cimetiere = Cimetiere.objects.get(id=cimetiere_id)
        from caveaux.models import Caveau
        caveaux = Caveau.objects.filter(bloc__zone__cimetiere=cimetiere)
        return [
            {
                "id": str(c.id),
                "numero": c.numero,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "statut": c.statut,
                "prix": float(c.prix),
                "zone": c.bloc.zone.nom,
                "bloc": c.bloc.nom,
                "couleur": {
                    "disponible": "green",
                    "reserve": "orange",
                    "occupe": "red",
                    "inexploitable": "gray"
                }.get(c.statut, "gray")
            }
            for c in caveaux
        ]
    except Cimetiere.DoesNotExist:
        return {"error": "Cimetiere non trouve"}


@router.get("/carte")
def carte_tous_cimetieres(request):
    cimetieres = Cimetiere.objects.filter(actif=True)
    return [
        {
            "id": str(c.id),
            "nom": c.nom,
            "adresse": c.adresse,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "total_caveaux": sum(b.caveaux.count() for z in c.zones.all() for b in z.blocs.all()),
            "disponibles": sum(b.caveaux.filter(statut='disponible').count() for z in c.zones.all() for b in z.blocs.all()),
        }
        for c in cimetieres
    ]


# ✅ NOUVEAUX ENDPOINTS : infos cimetière pour la carte
@router.get("/{cimetiere_id}/infos")
def infos_cimetiere(request, cimetiere_id: str):
    """Renvoie toutes les infos d'un cimetière (affiché au clic sur la carte)"""
    try:
        cimetiere = Cimetiere.objects.get(id=cimetiere_id)
        proprio = cimetiere.admins.first()
        proprio_info = None
        if proprio:
            proprio_info = {
                "nom": proprio.nom,
                "prenom": proprio.prenom,
                "email": proprio.email,
                "telephone": proprio.telephone,
            }

        return {
            "id": str(cimetiere.id),
            "nom": cimetiere.nom,
            "adresse": cimetiere.adresse,
            "latitude": cimetiere.latitude,
            "longitude": cimetiere.longitude,
            "superficie": cimetiere.superficie,
            "email": cimetiere.email_cimetiere,
            "proprietaire": proprio_info,
            "total_zones": cimetiere.zones.count(),
            "total_caveaux": sum(b.caveaux.count() for z in cimetiere.zones.all() for b in z.blocs.all()),
        }
    except Cimetiere.DoesNotExist:
        return {"error": "Cimetiere non trouve"}


@router.get("/{cimetiere_id}/caveaux-detail")
def caveaux_detail_cimetiere(request, cimetiere_id: str):
    """Liste tous les caveaux d'un cimetière avec leurs infos complètes"""
    try:
        cimetiere = Cimetiere.objects.get(id=cimetiere_id)
        from caveaux.models import Caveau
        caveaux = Caveau.objects.filter(bloc__zone__cimetiere=cimetiere).select_related('bloc__zone')
        return [
            {
                "id": str(c.id),
                "numero": c.numero,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "statut": c.statut,
                "prix": float(c.prix),
                "zone": c.bloc.zone.nom,
                "bloc": c.bloc.nom,
                "longueur": float(c.longueur),
                "largeur": float(c.largeur),
            }
            for c in caveaux
        ]
    except Cimetiere.DoesNotExist:
        return {"error": "Cimetiere non trouve"}


@router.post("/nouveau-cimetiere")
def nouveau_cimetiere(request, data: dict):
    """Permet à un admin de créer un nouveau cimetière"""
    try:
        from users.models import User
        
        # Récupérer l'admin
        admin = User.objects.get(email=data.get("admin_email"))
        
        # Créer le cimetière
        cimetiere = Cimetiere.objects.create(
            nom=data.get("nom"),
            adresse=data.get("adresse"),
            latitude=float(data.get("latitude")),
            longitude=float(data.get("longitude")),
            superficie=float(data.get("superficie")),
            email_cimetiere=data.get("email_cimetiere"),
        )
        
        # ✅ Lier l'admin au cimetière via le ManyToManyField 'admins' de Cimetiere
        cimetiere.admins.add(admin)
        cimetiere.save()
        
        # ✅ Si l'admin n'a pas encore de cimetiere principal, on lui assigne celui-ci
        if not admin.cimetiere:
            admin.cimetiere = cimetiere
            admin.save()
        
        return {
            "message": "Nouveau cimetiere cree avec succes",
            "cimetiere_id": str(cimetiere.id)
        }
    except User.DoesNotExist:
        return {"error": "Admin non trouve"}
    except Exception as ex:
        print(f"ERREUR DETAILLEE: {str(ex)}")
        return {"error": str(ex)}


@router.get("/mes-cimetieres")
def mes_cimetieres(request, admin_email: str = None):
    """Liste UNIQUEMENT les cimetières gérés par l'admin connecté"""
    if not admin_email:
        return []
    
    try:
        # ✅ On filtre par l'email de l'admin via la relation ManyToMany 'admins'
        cimetieres = Cimetiere.objects.filter(admins__email=admin_email, actif=True)
        
        print(f"📊 Cimetières trouvés pour {admin_email} : {cimetieres.count()}")
        
        resultats = []
        for c in cimetieres:
            resultats.append({
                "id": str(c.id),
                "nom": c.nom,
                "adresse": c.adresse,
                "superficie": c.superficie,
            })
            print(f"   -> {c.nom}")
        
        return resultats
    except Exception as ex:
        print(f"❌ ERREUR mes_cimetieres: {str(ex)}")
        return []


@router.post("/changer-cimetiere")
def changer_cimetiere(request, data: dict):
    """Change le cimetière principal d'un admin"""
    try:
        admin = User.objects.get(email=data.get("admin_email"))
        cimetiere_id = data.get("cimetiere_id")
        
        # Vérifier que l'admin gère bien ce cimetière
        if not Cimetiere.objects.filter(id=cimetiere_id, admins=admin).exists():
            return {"error": "Vous ne gérez pas ce cimetière"}
        
        # Mettre à jour le cimetière principal
        admin.cimetiere_id = cimetiere_id
        admin.save()
        
        return {"message": "Cimetière changé avec succès"}
    except User.DoesNotExist:
        return {"error": "Admin non trouvé"}
    except Exception as ex:
        return {"error": str(ex)}