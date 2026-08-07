import flet as ft
import httpx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import valider_date, valider_nom


class ReservationsPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.cimetiere_id = self.user.get("cimetiere_id")
        self.caveaux_disponibles = []
        self.message = ft.Text("", color="red", size=13)

        # ✅ Récupérer le cimetière pré-sélectionné depuis la carte (pour les clients)
        self.cimetiere_selectionne = page.session_data.get("cimetiere_selectionne")
        self.cimetiere_nom = page.session_data.get("cimetiere_nom", "")

        self.cimetiere_dropdown = ft.Dropdown(
            label="Cimetiere",
            border_radius=10,
            bgcolor="white",
            options=[],
            on_change=self.on_cimetiere_change,
        )
        self.caveau_dropdown = ft.Dropdown(
            label="Selectionner un caveau disponible",
            border_radius=10,
            bgcolor="white",
            options=[],
        )
        self.defunt_nom = ft.TextField(label="Nom du défunt", border_radius=10, bgcolor="white")
        self.defunt_prenom = ft.TextField(label="Prénom du défunt", border_radius=10, bgcolor="white")
        self.defunt_deces = ft.TextField(label="Date de décès (AAAA-MM-JJ)", border_radius=10, bgcolor="white", hint_text="Ex: 2026-06-17")
        self.type_concession = ft.Dropdown(
            label="Type de concession",
            border_radius=10,
            bgcolor="white",
            options=[
                ft.dropdown.Option("temporaire", "Temporaire"),
                ft.dropdown.Option("perpetuelle", "Perpétuelle"),
            ],
            value="temporaire",
        )

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888"}

    def get_cimetieres(self):
        try:
            response = httpx.get(f"{self.api_url}/etablissements/", timeout=10)
            return response.json()
        except:
            return []

    def get_caveaux_disponibles(self, cimetiere_id=None):
        try:
            if cimetiere_id:
                response = httpx.get(f"{self.api_url}/etablissements/{cimetiere_id}/caveaux", timeout=10)
            elif self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
                response = httpx.get(f"{self.api_url}/etablissements/{self.cimetiere_id}/caveaux", timeout=10)
            else:
                response = httpx.get(f"{self.api_url}/caveaux/", timeout=10)
            caveaux = response.json()
            return [c for c in caveaux if c.get("statut") == "disponible"]
        except:
            return []

    def get_reservations(self, cimetiere_id=None):
        try:
            response = httpx.get(f"{self.api_url}/reservations/", timeout=10)
            reservations = response.json()
            if cimetiere_id:
                reservations = [r for r in reservations if r.get("cimetiere_id") == cimetiere_id]
            return reservations
        except:
            return []

    def on_cimetiere_change(self, e):
        cimetiere_id = self.cimetiere_dropdown.value
        self.caveaux_disponibles = self.get_caveaux_disponibles(cimetiere_id)
        self.caveau_dropdown.options = [
            ft.dropdown.Option(cv.get("id"), f"Caveau {cv.get('numero')} — Zone {cv.get('zone')} — {cv.get('cimetiere_nom', '')}")
            for cv in self.caveaux_disponibles
        ]
        self.page.go("/reservations")

    def handle_reservation(self, e):
        if not all([self.caveau_dropdown.value, self.defunt_nom.value, self.defunt_prenom.value, self.defunt_deces.value]):
            self.message.value = "⚠️ Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation date de décès
        if not valider_date(self.defunt_deces.value):
            self.message.value = "⚠️ Format de date invalide. Utilisez AAAA-MM-JJ (ex: 2026-06-17)"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation nom/prénom (pas de chiffres)
        if not valider_nom(self.defunt_nom.value) or not valider_nom(self.defunt_prenom.value):
            self.message.value = "⚠️ Les noms ne doivent pas contenir de chiffres"
            self.message.color = "red"
            self.page.update()
            return
        
        try:
            response = httpx.post(
                f"{self.api_url}/reservations/",
                json={
                    "client_email": self.user.get("email"),
                    "caveau_id": self.caveau_dropdown.value,
                    "defunt_nom": self.defunt_nom.value,
                    "defunt_prenom": self.defunt_prenom.value,
                    "defunt_deces": self.defunt_deces.value,
                    "type_concession": self.type_concession.value,
                }
            )
            data = response.json()
            if "error" in data:
                self.message.value = f"❌ {data['error']}"
                self.message.color = "red"
            else:
                self.message.value = "✅ Réservation créée avec succès !"
                self.message.color = "green"
                self.caveau_dropdown.value = None
                self.defunt_nom.value = ""
                self.defunt_prenom.value = ""
                self.defunt_deces.value = ""
                self.page.session_data.pop("cimetiere_selectionne", None)
                self.page.session_data.pop("cimetiere_nom", None)
                self.page.go("/reservations")
        except Exception as ex:
            self.message.value = f" Erreur : {str(ex)}"
        self.page.update()

    def handle_validation(self, reservation_id, statut):
        try:
            response = httpx.put(
                f"{self.api_url}/reservations/{reservation_id}/valider",
                json={"admin_email": self.user.get("email"), "statut": statut}
            )
            data = response.json()
            if "error" in data:
                self.message.value = f"❌ {data['error']}"
                self.message.color = "red"
            else:
                self.message.value = f"✅ Réservation {statut} !"
                self.message.color = "green"
                self.page.go("/reservations")
        except Exception as ex:
            self.message.value = f"❌ Erreur : {str(ex)}"
        self.page.update()

    def couleur_statut(self, statut):
        return {"en_attente": "#FF9800", "validee": "#4CAF50", "rejetee": "#F44336", "annulee": "#9E9E9E"}.get(statut, "#9E9E9E")

    def build_reservation_card(self, r):
        couleur = self.couleur_statut(r.get("statut"))
        emoji = {"en_attente": "⏳", "validee": "✅", "rejetee": "❌", "annulee": "🚫"}.get(r.get("statut"), "❓")
        is_admin = self.role in ["admin", "superadmin", "secretariat"]
        actions = []
        if is_admin and r.get("statut") == "en_attente":
            actions = [
                ft.FilledButton("✅ Valider", on_click=lambda e, rid=r["id"]: self.handle_validation(rid, "validee")),
                ft.OutlinedButton(" Rejeter", on_click=lambda e, rid=r["id"]: self.handle_validation(rid, "rejetee")),
            ]
        card_controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"Caveau N° {r.get('caveau')}", size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=couleur,
                        border_radius=20,
                        content=ft.Text(f"{emoji} {r.get('statut', '').upper()}", size=11, color="white", weight=ft.FontWeight.BOLD),
                    ),
                ],
            ),
            ft.Text(f"👤 Défunt : {r.get('defunt_prenom')} {r.get('defunt_nom')}", size=13, color="#444444"),
            ft.Text(f"📧 Client : {r.get('client')}", size=12, color="#666666"),
            ft.Text(f"📅 Date : {r.get('created_at', '')[:10]}", size=11, color="#888888"),
        ]
        if actions:
            card_controls.append(ft.Row(controls=actions, spacing=10))
        return ft.Container(
            padding=15,
            margin=ft.margin.only(bottom=10),
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.1, "black")),
            content=ft.Column(controls=card_controls, spacing=8),
        )

    def build_sidebar(self):
        menu_items = [
            ("🏠  Tableau de bord", "/dashboard"),
            ("🗺️  Carte des caveaux", "/carte"),
            ("  Reservations", "/reservations"),
            ("💰  Paiements", "/paiement"),
        ]
        if self.role in ["superadmin", "admin", "agent", "secretariat"]:
            menu_items.append(("👥  Utilisateurs", "/utilisateurs"))

        menu_controls = []
        for texte, route in menu_items:
            is_active = route == "/reservations"
            menu_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.2, "white") if is_active else None,
                    on_click=lambda e, r=route: self.page.go(r),
                    content=ft.Text(texte, color="white", size=14, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL),
                )
            )

        # ✅ CORRECTION : return sorti de la boucle
        return ft.Container(
            width=230, bgcolor="#1B5E20", padding=20,
            content=ft.Column(controls=[
                ft.Container(
                    padding=ft.padding.only(bottom=15),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(width=65, height=65, bgcolor=ft.Colors.with_opacity(0.2, "white"), border_radius=32, alignment=ft.alignment.center, content=ft.Text("🏛️", size=32)),
                            ft.Container(height=8),
                            ft.Text("Gestion Cimetiere", color="white", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text("Republique du Congo", color=ft.Colors.with_opacity(0.6, "white"), size=11, text_align=ft.TextAlign.CENTER),
                        ],
                    ),
                ),
                ft.Divider(color=ft.Colors.with_opacity(0.3, "white")),
                ft.Container(height=10),
                ft.Text("MENU PRINCIPAL", color=ft.Colors.with_opacity(0.5, "white"), size=10),
                ft.Container(height=5),
            ] + menu_controls + [
                ft.Container(height=10),
                ft.Divider(color=ft.Colors.with_opacity(0.3, "white")),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=self.handle_logout, content=ft.Text("🚪  Deconnexion", color="#FF6B6B", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/concessions"), content=ft.Text("📜  Concessions", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/exhumations"), content=ft.Text("⚰️  Exhumations", color="white", size=14)),
            ]),
        )

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def build(self):
        c = self.get_colors()
        cimetieres = self.get_cimetieres()

        show_cimetiere_dropdown = self.role == "client"

        self.cimetiere_dropdown.options = [
            ft.dropdown.Option(str(c.get("id")), c.get("nom", "Cimetiere"))
            for c in cimetieres
        ]

        if self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
            cimetiere_a_utiliser = self.cimetiere_id
            self.cimetiere_dropdown.value = self.cimetiere_id
        elif self.cimetiere_selectionne:
            cimetiere_a_utiliser = self.cimetiere_selectionne
            self.cimetiere_dropdown.value = self.cimetiere_selectionne
        else:
            cimetiere_a_utiliser = None

        self.caveaux_disponibles = self.get_caveaux_disponibles(cimetiere_a_utiliser)
        reservations = self.get_reservations(cimetiere_a_utiliser if self.role != "client" else None)

        self.caveau_dropdown.options = [
            ft.dropdown.Option(
                cv.get("id"),
                f"Caveau {cv.get('numero')} — Zone {cv.get('zone')}" + (f" — {cv.get('cimetiere_nom', '')}" if self.role == "client" else "")
            )
            for cv in self.caveaux_disponibles
        ]

        if reservations:
            liste_reservations = [self.build_reservation_card(r) for r in reservations]
        else:
            liste_reservations = [
                ft.Container(
                    padding=40,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[ft.Text("📋", size=50), ft.Text("Aucune réservation", size=16, color="#999999")],
                    ),
                )
            ]

        bandeau_info = []
        if self.role == "client":
            if self.cimetiere_selectionne:
                nom_cim = next((c.get("nom") for c in cimetieres if str(c.get("id")) == self.cimetiere_selectionne), "Cimetiere")
                bandeau_info = [
                    ft.Container(
                        padding=15,
                        bgcolor="#E8F5E9",
                        border_radius=12,
                        border=ft.border.all(2, "#1B5E20"),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(controls=[ft.Icon(ft.Icons.PARK, color="#1B5E20"), ft.Text(f"Cimetiere selectionne : {nom_cim}", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20")]),
                                ft.TextButton("✕ Changer de cimetiere", style=ft.ButtonStyle(color="#F44336"), on_click=lambda e: self.changer_cimetiere()),
                            ],
                        ),
                    ),
                    ft.Container(height=15),
                ]
            else:
                bandeau_info = [
                    ft.Container(
                        padding=15,
                        bgcolor="#E3F2FD",
                        border_radius=12,
                        border=ft.border.all(2, "#2196F3"),
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.VISIBILITY, color="#1565C0"),
                                ft.Text(" Vous pouvez réserver dans n'importe quel cimetière", size=13, weight=ft.FontWeight.BOLD, color="#1565C0"),
                            ],
                        ),
                    ),
                    ft.Container(height=15),
                ]
        elif self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
            nom_cim = next((c.get("nom") for c in cimetieres if str(c.get("id")) == self.cimetiere_id), "Mon cimetière")
            bandeau_info = [
                ft.Container(
                    padding=15,
                    bgcolor="#E8F5E9",
                    border_radius=12,
                    border=ft.border.all(2, "#1B5E20"),
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PARK, color="#1B5E20"),
                            ft.Text(f"🔒 Cimetière : {nom_cim} — Réservations limitées à ce cimetière", size=13, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                        ],
                    ),
                ),
                ft.Container(height=15),
            ]

        form_controls = [
            ft.Text("📋 Nouvelle réservation", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
        ]
        if show_cimetiere_dropdown:
            form_controls.append(self.cimetiere_dropdown)
        form_controls.extend([
            ft.Text(f" {len(self.caveaux_disponibles)} caveau(x) disponible(s)", size=13, color="#4CAF50"),
            self.caveau_dropdown,
            ft.Row(controls=[ft.Container(expand=True, content=self.defunt_nom), ft.Container(expand=True, content=self.defunt_prenom)], spacing=15),
            ft.Row(controls=[ft.Container(expand=True, content=self.defunt_deces), ft.Container(expand=True, content=self.type_concession)], spacing=15),
            self.message,
            ft.FilledButton("Soumettre la réservation", on_click=self.handle_reservation),
        ])

        return ft.View(
            route="/reservations",
            bgcolor=c["bg"],
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
                            bgcolor=c["bg"],
                            content=ft.Column(
                                scroll=ft.ScrollMode.ALWAYS,
                                expand=True,
                                controls=[
                                    ft.Text("Réservations", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Text("Gérez les demandes de réservation", size=13, color=c["subtext"]),
                                    ft.Container(height=15),
                                ] + bandeau_info + [
                                    ft.Container(
                                        padding=25,
                                        bgcolor=c["card"],
                                        border_radius=15,
                                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.Colors.with_opacity(0.08, "black")),
                                        content=ft.Column(spacing=15, controls=form_controls),
                                    ),
                                    ft.Container(height=20),
                                    ft.Text("Liste des réservations", size=18, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Container(height=10),
                                ] + liste_reservations,
                            ),
                        ),
                    ],
                )
            ],
        )

    def changer_cimetiere(self):
        self.page.session_data.pop("cimetiere_selectionne", None)
        self.page.session_data.pop("cimetiere_nom", None)
        self.page.go("/reservations")