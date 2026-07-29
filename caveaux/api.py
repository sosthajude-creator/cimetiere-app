from ninja import Router, Schema
from typing import Optional
from .models import Caveau, AuditCaveau
from etablissements.models import ZoneCimetiere, Bloc, Cimetiere
from users.models import User

router = Router()


class ZoneCimetiereSchema(Schema):
    nom: str
    cimetiere_id: str
    superficie: float = 0
    exploitable: bool = True


class BlocSchema(Schema):
    nom: str
    zone_id: str


class CaveauSchema(Schema):
    bloc_id: str
    numero: str
    latitude: float
    longitude: float
    longueur: float
    largeur: float
    prix: float = 75000


class StatutSchema(Schema):
    statut: str
    modifie_par_email: str


# ============ ZONES ============
@router.get("/zones")
def list_zones(request, cimetiere_id: str = None):
    qs = ZoneCimetiere.objects.select_related('cimetiere').all()
    if cimetiere_id:
        qs = qs.filter(cimetiere_id=cimetiere_id)
    return [
        {
            "id": str(z.id),
            "nom": z.nom,
            "superficie": float(z.superficie),
            "exploitable": z.exploitable,
            "cimetiere_id": str(z.cimetiere.id),
            "cimetiere_nom": z.cimetiere.nom,
        }
        for z in qs
    ]


@router.post("/zones")
def create_zone(request, data: ZoneCimetiereSchema):
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
    except Exception as ex:
        return {"error": str(ex)}


# ============ BLOCS ============
@router.get("/blocs")
def list_blocs(request, zone_id: str = None, cimetiere_id: str = None):
    qs = Bloc.objects.select_related('zone__cimetiere').all()
    if zone_id:
        qs = qs.filter(zone_id=zone_id)
    if cimetiere_id:
        qs = qs.filter(zone__cimetiere_id=cimetiere_id)
    return [
        {
            "id": str(b.id),
            "nom": b.nom,
            "zone_id": str(b.zone.id),
            "zone_nom": b.zone.nom,
            "cimetiere_id": str(b.zone.cimetiere.id),
            "cimetiere_nom": b.zone.cimetiere.nom,
        }
        for b in qs
    ]


@router.post("/blocs")
def create_bloc(request, data: BlocSchema):
    try:
        zone = ZoneCimetiere.objects.get(id=data.zone_id)
        bloc = Bloc.objects.create(nom=data.nom, zone=zone)
        return {"message": "Bloc cree", "id": str(bloc.id)}
    except ZoneCimetiere.DoesNotExist:
        return {"error": "Zone non trouvee"}
    except Exception as ex:
        return {"error": str(ex)}


# ============ CAVEAUX ============
@router.get("/")
def list_caveaux(request, cimetiere_id: str = None):
    qs = Caveau.objects.select_related('bloc__zone__cimetiere').all()
    if cimetiere_id:
        qs = qs.filter(bloc__zone__cimetiere_id=cimetiere_id)
    return [
        {
            "id": str(c.id),
            "zone": c.bloc.zone.nom if c.bloc and c.bloc.zone else "",
            "bloc": c.bloc.nom if c.bloc else "",
            "numero": c.numero,
            "latitude": float(c.latitude),
            "longitude": float(c.longitude),
            "longueur": float(c.longueur),
            "largeur": float(c.largeur),
            "statut": c.statut,
            "prix": float(c.prix),
            "cimetiere_id": str(c.bloc.zone.cimetiere.id) if c.bloc and c.bloc.zone and c.bloc.zone.cimetiere else None,
            "cimetiere_nom": c.bloc.zone.cimetiere.nom if c.bloc and c.bloc.zone and c.bloc.zone.cimetiere else None,
        }
        for c in qs
    ]


@router.post("/")
def create_caveau(request, data: CaveauSchema):
    try:
        bloc = Bloc.objects.get(id=data.bloc_id)
        caveau = Caveau.objects.create(
            bloc=bloc,
            numero=data.numero,
            latitude=data.latitude,
            longitude=data.longitude,
            longueur=data.longueur,
            largeur=data.largeur,
            prix=data.prix,
        )
        return {"message": "Caveau cree", "id": str(caveau.id)}
    except Bloc.DoesNotExist:
        return {"error": "Bloc non trouve"}
    except Exception as ex:
        return {"error": str(ex)}


@router.put("/{caveau_id}/statut")
def update_statut(request, caveau_id: str, data: StatutSchema):
    try:
        caveau = Caveau.objects.get(id=caveau_id)
        try:
            user = User.objects.get(email=data.modifie_par_email)
        except User.DoesNotExist:
            return {"error": "Utilisateur non trouve"}
        AuditCaveau.objects.create(
            caveau=caveau,
            modifie_par=user,
            ancien_statut=caveau.statut,
            nouveau_statut=data.statut,
        )
        caveau.statut = data.statut
        caveau.save()
        return {"message": "Statut mis a jour"}
    except Caveau.DoesNotExist:
        return {"error": "Caveau non trouve"}


# ============ CARTE ============
@router.get("/carte")
def carte_caveaux(request, cimetiere_id: str = None):
    """
    ✅ Si cimetiere_id est fourni → filtre par cimetiere (pour admin/agent/secretariat)
    ✅ Si pas de cimetiere_id → retourne TOUS les caveaux (pour client/superadmin)
    """
    qs = Caveau.objects.select_related('bloc__zone__cimetiere').all()
    if cimetiere_id:
        qs = qs.filter(bloc__zone__cimetiere_id=cimetiere_id)
    return [
        {
            "id": str(c.id),
            "numero": c.numero,
            "latitude": float(c.latitude),
            "longitude": float(c.longitude),
            "statut": c.statut,
            "zone": c.bloc.zone.nom if c.bloc and c.bloc.zone else "",
            "bloc": c.bloc.nom if c.bloc else "",
            "cimetiere_id": str(c.bloc.zone.cimetiere.id) if c.bloc and c.bloc.zone and c.bloc.zone.cimetiere else None,
            "cimetiere_nom": c.bloc.zone.cimetiere.nom if c.bloc and c.bloc.zone and c.bloc.zone.cimetiere else None,
            "prix": float(c.prix),
            "couleur": {
                "disponible": "vert",
                "reserve": "orange",
                "occupe": "rouge",
                "inexploitable": "gris"
            }.get(c.statut, "gris")
        }
        for c in qs
    ]


# ============ STATISTIQUES ============
@router.get("/statistiques")
def statistiques(request, cimetiere_id: str = None):
    qs = Caveau.objects.all()
    if cimetiere_id:
        qs = qs.filter(bloc__zone__cimetiere_id=cimetiere_id)
    total = qs.count()
    disponibles = qs.filter(statut='disponible').count()
    reserves = qs.filter(statut='reserve').count()
    occupes = qs.filter(statut='occupe').count()
    inexploitables = qs.filter(statut='inexploitable').count()
    taux_occupation = (occupes / total * 100) if total > 0 else 0
    return {
        "total": total,
        "disponibles": disponibles,
        "reserves": reserves,
        "occupes": occupes,
        "inexploitables": inexploitables,
        "taux_occupation": round(taux_occupation, 2)
    }