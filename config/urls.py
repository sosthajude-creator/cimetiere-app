from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI(
    title="API Gestion de Cimetière",
    description="API REST pour l'application de gestion de cimetière",
    version="1.0.0",
)

from users.api import router as users_router
from caveaux.api import router as caveaux_router
from reservations.api import router as reservations_router
from finances.api import router as finances_router
from notifications.api import router as notifications_router
from etablissements.api import router as etablissements_router

api.add_router("/auth", users_router)
api.add_router("/caveaux", caveaux_router)
api.add_router("/reservations", reservations_router)
api.add_router("/finances", finances_router)
api.add_router("/notifications", notifications_router)
api.add_router("/etablissements", etablissements_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls),  # ✅ Changé de 'api/' à '' (racine)
]