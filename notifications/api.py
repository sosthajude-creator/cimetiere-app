from ninja import Router, Schema
from typing import Optional
from .models import Notification
from users.models import User

router = Router()

# Schemas
class NotificationSchema(Schema):
    destinataire_email: str
    type_notif: str
    sujet: str
    message: str

# NOTIFICATIONS
@router.get("/")
def list_notifications(request, email: str):
    try:
        user = User.objects.get(email=email)
        notifications = Notification.objects.filter(
            destinataire=user
        ).order_by('-created_at')
        return [
            {
                "id": str(n.id),
                "type_notif": n.type_notif,
                "sujet": n.sujet,
                "message": n.message,
                "lu": n.lu,
                "envoye_par_email": n.envoye_par_email,
                "created_at": str(n.created_at),
            }
            for n in notifications
        ]
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouvé"}

@router.post("/")
def create_notification(request, data: NotificationSchema):
    try:
        user = User.objects.get(email=data.destinataire_email)
        notification = Notification.objects.create(
            destinataire=user,
            type_notif=data.type_notif,
            sujet=data.sujet,
            message=data.message,
        )
        return {
            "message": "Notification créée",
            "id": str(notification.id)
        }
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouvé"}

@router.put("/{notification_id}/lire")
def marquer_lu(request, notification_id: str):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.lu = True
        notification.save()
        return {"message": "Notification marquée comme lue"}
    except Notification.DoesNotExist:
        return {"error": "Notification non trouvée"}

@router.get("/non-lues")
def notifications_non_lues(request, email: str):
    try:
        user = User.objects.get(email=email)
        count = Notification.objects.filter(
            destinataire=user,
            lu=False
        ).count()
        return {"non_lues": count}
    except User.DoesNotExist:
        return {"error": "Utilisateur non trouvé"}