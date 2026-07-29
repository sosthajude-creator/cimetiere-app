import flet as ft
import httpx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import valider_email

# Liste des villes du Congo avec coordonnées GPS
VILLES_CONGO = {
    "Brazzaville": (-4.2634, 15.2429),
    "Pointe-Noire": (-4.7692, 11.8636),
    "Dolisie": (-4.1989, 12.6667),
    "Nkayi": (-4.1833, 13.2833),
    "Owando": (-0.4833, 15.9000),
    "Impfondo": (3.1167, 18.0667),
    "Ouesso": (1.6167, 16.0500),
    "Mossendjo": (-2.9833, 12.7167),
    "Kinkala": (-4.3667, 14.7667),
    "Madingou": (-4.1833, 13.5500),
    "Sibiti": (-3.6833, 13.3500),
    "Gamboma": (-1.8833, 15.8667),
    "Makoua": (0.0000, 15.6167),
    "Ewo": (-0.8667, 14.7833),
    "Kellé": (0.2000, 14.9833),
}


class NouveauCimetierePage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.message = ft.Text("", size=13)
        
        self.nom = ft.TextField(label="Nom du cimetiere", border_radius=10, bgcolor="white")
        self.adresse = ft.TextField(label="Adresse", border_radius=10, bgcolor="white")
        self.email = ft.TextField(label="Email du cimetiere", border_radius=10, bgcolor="white")
        
        self.ville_dropdown = ft.Dropdown(
            label="Ville du cimetiere",
            border_radius=10,
            bgcolor="white",
            options=[ft.dropdown.Option(ville, ville) for ville in VILLES_CONGO.keys()],
            value="Brazzaville",
            on_change=self.on_ville_change,
        )
        
        self.latitude = ft.TextField(
            label="Latitude (automatique)",
            border_radius=10,
            bgcolor="#F5F5F5",
            read_only=True,
            visible=False,
        )
        self.longitude = ft.TextField(
            label="Longitude (automatique)",
            border_radius=10,
            bgcolor="#F5F5F5",
            read_only=True,
            visible=False,
        )
        
        self.superficie = ft.TextField(
            label="Superficie (m²)",
            border_radius=10,
            bgcolor="white",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        self.info_ville = ft.Container(
            padding=12,
            bgcolor="#E3F2FD",
            border_radius=10,
            content=ft.Text(
                " Coordonnées GPS : -4.2634, 15.2429 (Brazzaville)",
                size=12,
                color="#1565C0",
                text_align=ft.TextAlign.CENTER,
            ),
        )
    
    def on_ville_change(self, e):
        ville = self.ville_dropdown.value
        if ville in VILLES_CONGO:
            lat, lng = VILLES_CONGO[ville]
            self.latitude.value = str(lat)
            self.longitude.value = str(lng)
            self.info_ville.content.value = f"📍 Coordonnées GPS : {lat}, {lng} ({ville})"
            self.page.update()
    
    def handle_creer(self, e):
        if not all([self.nom.value, self.adresse.value, self.email.value, self.ville_dropdown.value, self.superficie.value]):
            self.message.value = "Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation email
        if not valider_email(self.email.value):
            self.message.value = "Email du cimetiere invalide"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation superficie
        try:
            superficie = float(self.superficie.value)
            if superficie <= 0:
                self.message.value = "La superficie doit etre superieure a 0"
                self.message.color = "red"
                self.page.update()
                return
        except ValueError:
            self.message.value = "Superficie invalide"
            self.message.color = "red"
            self.page.update()
            return
        
        try:
            ville = self.ville_dropdown.value
            lat, lng = VILLES_CONGO[ville]
            
            response = httpx.post(
                f"{self.api_url}/etablissements/nouveau-cimetiere",
                json={
                    "nom": self.nom.value,
                    "adresse": self.adresse.value,
                    "latitude": lat,
                    "longitude": lng,
                    "superficie": superficie,
                    "email_cimetiere": self.email.value,
                    "admin_email": self.user.get("email"),
                },
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Nouveau cimetiere cree avec succes !"
                self.message.color = "green"
                self.page.go("/dashboard")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()
    
    def build_sidebar(self):
        return ft.Container(
            width=230,
            bgcolor="#1B5E20",
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=15),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=65, height=65, bgcolor=ft.colors.with_opacity(0.2, "white"), border_radius=32, alignment=ft.alignment.center, content=ft.Text("🏛️", size=32)),
                                ft.Container(height=8),
                                ft.Text("Gestion Cimetiere", color="white", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                ft.Text("Republique du Congo", color=ft.colors.with_opacity(0.6, "white"), size=11, text_align=ft.TextAlign.CENTER),
                            ],
                        ),
                    ),
                    ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                    ft.Container(height=10),
                    ft.Text("MENU PRINCIPAL", color=ft.colors.with_opacity(0.5, "white"), size=10),
                    ft.Container(height=5),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/dashboard"), content=ft.Text("  Tableau de bord", color="white", size=14)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/carte"), content=ft.Text("  Carte des caveaux", color="white", size=14)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/reservations"), content=ft.Text("📋  Reservations", color="white", size=14)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/paiement"), content=ft.Text("💰  Paiements", color="white", size=14)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/utilisateurs"), content=ft.Text("👥  Utilisateurs", color="white", size=14)),
                    ft.Container(height=10),
                    ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                    ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=self.handle_logout, content=ft.Text("🚪  Deconnexion", color="#FF6B6B", size=14)),
                ],
            ),
        )
    
    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")
    
    def build(self):
        return ft.View(
            route="/nouveau-cimetiere",
            bgcolor="#F5F5F5",
            padding=0,
            controls=[
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        self.build_sidebar(),
                        ft.Container(
                            expand=True,
                            padding=25,
                            bgcolor="#F5F5F5",
                            content=ft.Column(
                                scroll=ft.ScrollMode.ALWAYS,
                                expand=True,
                                controls=[
                                    ft.Text("Créer un nouveau cimetière", size=24, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                    ft.Container(height=20),
                                    self.nom,
                                    self.adresse,
                                    self.email,
                                    self.ville_dropdown,
                                    self.info_ville,
                                    self.latitude,
                                    self.longitude,
                                    self.superficie,
                                    self.message,
                                    ft.Row(
                                        controls=[
                                            ft.FilledButton("Créer le cimetière", on_click=self.handle_creer),
                                            ft.OutlinedButton("Retour au menu principal", on_click=lambda e: self.page.go("/dashboard")),
                                        ],
                                        spacing=10,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        )