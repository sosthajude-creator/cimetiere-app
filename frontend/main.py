import flet as ft
from pages.login import LoginPage
from pages.dashboard import DashboardPage
from pages.carte import CartePage
from pages.reservations import ReservationsPage
from pages.paiement import PaiementPage
from pages.inscription import InscriptionPage
from pages.utilisateurs import UtilisateursPage
from pages.concessions import ConcessionsPage
from pages.exhumations import ExhumationsPage
from pages.nouveau_cimetiere import NouveauCimetierePage

API_URL = "https://cimetiere-app.onrender.com"

def main(page: ft.Page):
    page.title = "Gestion de Cimetière"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F5F5F5"
    page.fonts = {
        "Poppins": "https://fonts.gstatic.com/s/poppins/v20/pXew8Av7yZPWFsFWwXlVnA.ttf"
    }
    page.theme = ft.Theme(font_family="Poppins")
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600

    # Stockage de la session
    page.session_data = {}

    def route_change(e):
        page.views.clear()

        if page.route == "/" or page.route == "/login":
            page.views.append(LoginPage(page, API_URL).build())
        elif page.route == "/inscription":
            page.views.append(InscriptionPage(page,API_URL).build())
        elif page.route == "/dashboard":
            page.views.append(DashboardPage(page, API_URL).build())
        elif page.route == "/carte":
            page.views.append(CartePage(page, API_URL).build())
        elif page.route == "/reservations":
            page.views.append(ReservationsPage(page, API_URL).build())
        elif page.route == "/paiement":
            page.views.append(PaiementPage(page, API_URL).build())
        elif page.route =="/utilisateurs":
            page.views.append(UtilisateursPage(page, API_URL).build()) 
        elif page.route == "/concessions":
            page.views.append(ConcessionsPage(page, API_URL).build())  
        elif page.route == "/exhumations":
            page.views.append(ExhumationsPage(page, API_URL).build())
        elif page.route == "/nouveau-cimetiere":
            page.views.append(NouveauCimetierePage(page, API_URL).build())         

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

ft.app(target=main, view=ft.WEB_BROWSER, port=8080)