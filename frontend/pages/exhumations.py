import flet as ft
import httpx

class ExhumationsPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.message = ft.Text("", size=13)

        # Champs formulaire
        self.concession_id = ft.TextField(label="ID de la concession", border_radius=10, bgcolor="white")
        self.motif = ft.TextField(label="Motif de l'exhumation", border_radius=10, bgcolor="white", multiline=True, min_lines=3)

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888"}

    def get_exhumations(self):
        try:
            response = httpx.get(self.api_url + "/reservations/exhumations", timeout=10)
            return response.json()
        except:
            return []

    def handle_demande(self, e):
        if not self.concession_id.value or not self.motif.value:
            self.message.value = "Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return

        # ✅ Validation motif
        if not self.motif.value.strip():
            self.message.value = "Le motif ne peut pas etre vide"
            self.message.color = "red"
            self.page.update()
            return
        
        if len(self.motif.value.strip()) < 10:
            self.message.value = "Le motif doit contenir au moins 10 caracteres"
            self.message.color = "red"
            self.page.update()
            return

        try:
            response = httpx.post(
                self.api_url + "/reservations/exhumations",
                json={
                    "concession_id": self.concession_id.value,
                    "demandeur_email": self.user.get("email"),
                    "motif": self.motif.value,
                },
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Demande d'exhumation soumise avec succes !"
                self.message.color = "green"
                self.concession_id.value = ""
                self.motif.value = ""
                self.page.go("/exhumations")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_validation(self, exhumation_id, statut):
        try:
            response = httpx.put(
                self.api_url + "/reservations/exhumations/" + exhumation_id + "/valider",
                json={
                    "admin_email": self.user.get("email"),
                    "statut": statut,
                },
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Exhumation " + statut + " avec succes !"
                self.message.color = "green"
                self.page.go("/exhumations")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def build_sidebar(self):
        menu_items = [
            ("🏠  Tableau de bord", "/dashboard"),
            ("🗺️  Carte des caveaux", "/carte"),
            ("📋  Reservations", "/reservations"),
            ("💰  Paiements", "/paiement"),
        ]
        if self.role in ["superadmin", "admin", "agent", "secretariat"]:
            menu_items.append(("👥  Utilisateurs", "/utilisateurs"))

        menu_controls = []
        for texte, route in menu_items:
            is_active = route == "/exhumations"
            menu_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=10,
                    bgcolor=ft.colors.with_opacity(0.2, "white") if is_active else None,
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
            ] + menu_controls + [
                ft.Container(height=10),
                ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=self.handle_logout, content=ft.Text("🚪  Deconnexion", color="#FF6B6B", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/concessions"), content=ft.Text("  Concessions", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/exhumations"), content=ft.Text("️  Exhumations", color="white", size=14)),
            ]),
        )
        
    def build_exhumation_card(self, ex):
        statut_couleurs = {
            "en_attente": "#FF9800",
            "validee": "#4CAF50",
            "rejetee": "#F44336",
        }
        emoji = {"en_attente": "⏳", "validee": "✅", "rejetee": "❌"}
        couleur = statut_couleurs.get(ex.get("statut", ""), "#9E9E9E")

        actions = []
        if self.role in ["superadmin", "admin"] and ex.get("statut") == "en_attente":
            actions = [
                ft.FilledButton(
                    "✅ Valider",
                    on_click=lambda e, eid=ex["id"]: self.handle_validation(eid, "validee"),
                ),
                ft.OutlinedButton(
                    "❌ Rejeter",
                    on_click=lambda e, eid=ex["id"]: self.handle_validation(eid, "rejetee"),
                ),
            ]

        card_controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        "Demande d'exhumation",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color="#1B5E20",
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=couleur,
                        border_radius=20,
                        content=ft.Text(
                            emoji.get(ex.get("statut", ""), "❓") + " " + ex.get("statut", "").upper(),
                            size=11, color="white", weight=ft.FontWeight.BOLD,
                        ),
                    ),
                ],
            ),
            ft.Text("Demandeur : " + ex.get("demandeur", ""), size=13, color="#444444"),
            ft.Text("Motif : " + ex.get("motif", ""), size=12, color="#666666"),
            ft.Text("Date : " + ex.get("created_at", "")[:10], size=11, color="#888888"),
        ]

        if ex.get("date_validation"):
            card_controls.append(ft.Text("Valide le : " + ex.get("date_validation", "")[:10], size=11, color="#4CAF50"))

        if actions:
            card_controls.append(ft.Row(controls=actions, spacing=10))

        return ft.Container(
            padding=15,
            margin=ft.margin.only(bottom=10),
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Column(spacing=8, controls=card_controls),
        )

    def build(self):
        c = self.get_colors()
        exhumations = self.get_exhumations()

        if exhumations:
            liste = [self.build_exhumation_card(ex) for ex in exhumations]
        else:
            liste = [
                ft.Container(
                    padding=40,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("⚰️", size=50),
                            ft.Text("Aucune demande d'exhumation", size=16, color="#999999"),
                        ],
                    ),
                )
            ]

        return ft.View(
            route="/exhumations",
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
                                    ft.Text("Gestion des Exhumations", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Text(str(len(exhumations)) + " demande(s) d'exhumation", size=13, color=c["subtext"]),
                                    ft.Container(height=15),

                                    # Info
                                    ft.Container(
                                        padding=15,
                                        bgcolor="#FFF3E0",
                                        border_radius=12,
                                        border=ft.border.all(1, "#FF9800"),
                                        content=ft.Text(
                                            "⚠️ Une exhumation necessite une autorisation administrative. Toute demande sera examinee par l'administration avant validation.",
                                            size=12,
                                            color="#E65100",
                                        ),
                                    ),
                                    ft.Container(height=15),

                                    # Formulaire
                                    ft.Container(
                                        padding=25,
                                        bgcolor=c["card"],
                                        border_radius=15,
                                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.colors.with_opacity(0.08, "black")),
                                        content=ft.Column(
                                            spacing=15,
                                            controls=[
                                                ft.Text("⚰️ Nouvelle demande d'exhumation", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                                self.concession_id,
                                                self.motif,
                                                self.message,
                                                ft.FilledButton("Soumettre la demande", on_click=self.handle_demande),
                                            ],
                                        ),
                                    ),
                                    ft.Container(height=20),

                                    ft.Text("Liste des demandes", size=18, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Container(height=10),
                                ] + liste,
                            ),
                        ),
                    ],
                )
            ],
        )