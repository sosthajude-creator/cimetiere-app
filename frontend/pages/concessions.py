import flet as ft
import httpx

class ConcessionsPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.message = ft.Text("", size=13)

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888"}

    def get_concessions(self):
        try:
            response = httpx.get(self.api_url + "/reservations/concessions", timeout=10)
            return response.json()
        except:
            return []

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def handle_renouveler(self, reservation_id):
        # ✅ Ajout de l'appel API manquant
        try:
            response = httpx.put(
                self.api_url + "/reservations/" + reservation_id + "/renouveler",
                json={"admin_email": self.user.get("email")},
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Concession renouvelee avec succes !"
                self.message.color = "green"
                self.page.go("/concessions")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_resilier(self, reservation_id):
        try:
            response = httpx.put(
                self.api_url + "/reservations/" + reservation_id + "/valider",
                json={"admin_email": self.user.get("email"), "statut": "annulee"},
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Concession resiliee avec succes !"
                self.message.color = "green"
                self.page.go("/concessions")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

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
            is_active = route == "/concessions"
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
                            ft.Container(width=65, height=65, bgcolor=ft.colors.with_opacity(0.2, "white"), border_radius=32, alignment=ft.alignment.center, content=ft.Text("️", size=32)),
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

    def build_concession_card(self, c):
        type_couleur = "#1B5E20" if c.get("type_concess") == "perpetuelle" else "#2196F3"
        type_label = "PERPETUELLE" if c.get("type_concess") == "perpetuelle" else "TEMPORAIRE"

        actions = []
        if self.role in ["superadmin", "admin", "secretariat"]:
            actions = [
                ft.FilledButton(
                    "Renouveler",
                    on_click=lambda e, rid=c["reservation_id"]: self.handle_renouveler(rid),
                ),
                ft.OutlinedButton(
                    "Resilier",
                    on_click=lambda e, rid=c["reservation_id"]: self.handle_resilier(rid),
                ),
            ]

        card_controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Caveau N° " + c.get("caveau", ""), size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=type_couleur,
                        border_radius=20,
                        content=ft.Text(type_label, size=11, color="white", weight=ft.FontWeight.BOLD),
                    ),
                ],
            ),
            ft.Text("Defunt : " + c.get("defunt_prenom", "") + " " + c.get("defunt_nom", ""), size=13, color="#444444"),
            ft.Text("Client : " + c.get("client", ""), size=12, color="#666666"),
            ft.Text("Debut : " + c.get("date_debut", ""), size=11, color="#888888"),
            ft.Text("Fin : " + c.get("date_fin", "Perpetuelle"), size=11, color="#888888"),
        ]

        if actions:
            card_controls.append(ft.Row(controls=actions, spacing=10))

        return ft.Container(
            padding=15,
            margin=ft.margin.only(bottom=10),
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(2, type_couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Column(spacing=8, controls=card_controls),
        )

    def build(self):
        c = self.get_colors()
        concessions = self.get_concessions()

        if concessions:
            liste = [self.build_concession_card(con) for con in concessions]
        else:
            liste = [
                ft.Container(
                    padding=40,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("", size=50),
                            ft.Text("Aucune concession active", size=16, color="#999999"),
                            ft.Text("Les concessions apparaissent apres validation des reservations", size=13, color="#BBBBBB", text_align=ft.TextAlign.CENTER),
                        ],
                    ),
                )
            ]

        return ft.View(
            route="/concessions",
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
                                    ft.Text("Gestion des Concessions", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Text(str(len(concessions)) + " concession(s) active(s)", size=13, color=c["subtext"]),
                                    ft.Container(height=15),
                                    ft.Container(
                                        padding=20,
                                        bgcolor=c["card"],
                                        border_radius=15,
                                        content=ft.Column(
                                            controls=[
                                                ft.Text("Types de concessions", size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                                ft.Container(height=8),
                                                ft.Row(
                                                    controls=[
                                                        ft.Container(
                                                            expand=True,
                                                            padding=15,
                                                            bgcolor="#E8F5E9",
                                                            border_radius=10,
                                                            content=ft.Column(
                                                                controls=[
                                                                    ft.Text("Temporaire", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                                                    ft.Text("Duree limitee avec date d'echeance", size=12, color="#666666"),
                                                                ],
                                                            ),
                                                        ),
                                                        ft.Container(
                                                            expand=True,
                                                            padding=15,
                                                            bgcolor="#E3F2FD",
                                                            border_radius=10,
                                                            content=ft.Column(
                                                                controls=[
                                                                    ft.Text("Perpetuelle", size=14, weight=ft.FontWeight.BOLD, color="#1565C0"),
                                                                    ft.Text("Sans limite de duree", size=12, color="#666666"),
                                                                ],
                                                            ),
                                                        ),
                                                    ],
                                                    spacing=15,
                                                ),
                                            ],
                                        ),
                                    ),
                                    ft.Container(height=15),
                                    self.message,
                                    ft.Text("Liste des concessions actives", size=18, weight=ft.FontWeight.BOLD, color=c["text"]),
                                    ft.Container(height=10),
                                ] + liste,
                            ),
                        ),
                    ],
                )
            ],
        )