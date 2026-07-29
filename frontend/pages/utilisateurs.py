import flet as ft
import httpx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import valider_email, valider_telephone_congo


class UtilisateursPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.message = ft.Text("", size=13)
        self.nom = ft.TextField(label="Nom", border_radius=10, bgcolor="white")
        self.prenom = ft.TextField(label="Prenom", border_radius=10, bgcolor="white")
        self.email = ft.TextField(label="Email", border_radius=10, bgcolor="white")
        self.telephone = ft.TextField(label="Telephone", border_radius=10, bgcolor="white")
        self.password = ft.TextField(label="Mot de passe", password=True, can_reveal_password=True, border_radius=10, bgcolor="white")
        self.role_dropdown = ft.Dropdown(
            label="Role", border_radius=10, bgcolor="white",
            options=[
                ft.dropdown.Option("admin", "Administrateur"),
                ft.dropdown.Option("agent", "Agent de terrain"),
                ft.dropdown.Option("secretariat", "Secretariat"),
                ft.dropdown.Option("client", "Client"),
            ],
            value="client",
        )

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888"}

    def get_utilisateurs(self):
        try:
            response = httpx.get(self.api_url + "/auth/users", timeout=10)
            return response.json()
        except:
            return []

    def get_users_en_attente(self):
        try:
            url = self.api_url + "/auth/en-attente"
            cimetiere_id = self.user.get("cimetiere_id")
            if cimetiere_id:
                url += "?cimetiere_id=" + cimetiere_id
            response = httpx.get(url, timeout=10)
            return response.json()
        except:
            return []

    def handle_creer(self, e):
        if not all([self.nom.value, self.prenom.value, self.email.value, self.password.value]):
            self.message.value = "Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation email
        if not valider_email(self.email.value):
            self.message.value = "Email invalide"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation téléphone
        if self.telephone.value and not valider_telephone_congo(self.telephone.value):
            self.message.value = "Numero de telephone invalide. Format : (+242) XXXXXXXXX"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation mot de passe
        if len(self.password.value) < 6:
            self.message.value = "Le mot de passe doit contenir au moins 6 caracteres"
            self.message.color = "red"
            self.page.update()
            return

        try:
            response = httpx.post(self.api_url + "/auth/register", json={"email": self.email.value, "password": self.password.value, "nom": self.nom.value, "prenom": self.prenom.value, "telephone": self.telephone.value or "", "role": self.role_dropdown.value}, timeout=10)
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Utilisateur cree !"
                self.message.color = "green"
                self.nom.value = ""
                self.prenom.value = ""
                self.email.value = ""
                self.telephone.value = ""
                self.password.value = ""
                self.page.go("/utilisateurs")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_toggle_actif(self, user_id):
        try:
            response = httpx.put(self.api_url + "/auth/users/" + user_id + "/activer", timeout=10)
            data = response.json()
            self.message.value = data.get("message", "")
            self.message.color = "green"
            self.page.go("/utilisateurs")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_valider_demande(self, user_id, statut):
        try:
            response = httpx.put(self.api_url + "/auth/users/" + user_id + "/valider?statut=" + statut, timeout=10)
            data = response.json()
            if "error" in data:
                self.message.value = "Erreur : " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "Utilisateur " + statut + " !"
                self.message.color = "green"
                self.page.go("/utilisateurs")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def build_demande_card(self, u):
        couleur = {"agent": "#2196F3", "secretariat": "#FF9800"}.get(u.get("role", ""), "#607D8B")
        return ft.Container(
            padding=15, margin=ft.margin.only(bottom=10), bgcolor="#FFF8E1", border_radius=12, border=ft.border.all(2, "#FF9800"),
            content=ft.Column(spacing=8, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(u.get("prenom", "") + " " + u.get("nom", ""), size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=3), bgcolor=couleur, border_radius=20, content=ft.Text("⏳ " + u.get("role", "").upper(), size=10, color="white", weight=ft.FontWeight.BOLD)),
                ]),
                ft.Text("📧 " + u.get("email", ""), size=12, color="#666666"),
                ft.Row(controls=[
                    ft.FilledButton("✅ Valider", on_click=lambda e, uid=u["id"]: self.handle_valider_demande(uid, "valide"), style=ft.ButtonStyle(color="white", bgcolor="#4CAF50")),
                    ft.OutlinedButton("❌ Rejeter", on_click=lambda e, uid=u["id"]: self.handle_valider_demande(uid, "rejete"), style=ft.ButtonStyle(color="#F44336")),
                ], spacing=10),
            ]),
        )

    def build_user_card(self, u):
        role_couleurs = {"superadmin": "#9C27B0", "admin": "#1B5E20", "agent": "#2196F3", "secretariat": "#FF9800", "client": "#607D8B"}
        couleur = role_couleurs.get(u.get("role", ""), "#607D8B")
        is_active = u.get("is_active", True)
        return ft.Container(
            padding=15, margin=ft.margin.only(bottom=10), bgcolor="white", border_radius=12, border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Column(spacing=4, controls=[
                    ft.Text(u.get("prenom", "") + " " + u.get("nom", ""), size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Text(u.get("email", ""), size=12, color="#666666"),
                    ft.Row(controls=[
                        ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=3), bgcolor=couleur, border_radius=20, content=ft.Text(u.get("role", "").upper(), size=10, color="white", weight=ft.FontWeight.BOLD)),
                        ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=3), bgcolor="#4CAF50" if is_active else "#F44336", border_radius=20, content=ft.Text("ACTIF" if is_active else "INACTIF", size=10, color="white", weight=ft.FontWeight.BOLD)),
                    ], spacing=8),
                ]),
                ft.FilledButton("Desactiver" if is_active else "Activer", on_click=lambda e, uid=u["id"]: self.handle_toggle_actif(uid)) if self.role in ["superadmin", "admin"] else ft.Container(),
            ]),
        )

    def build_sidebar(self):
        menu_items = [
            ("  Tableau de bord", "/dashboard"),
            ("🗺️  Carte des caveaux", "/carte"),
            ("📋  Reservations", "/reservations"),
            ("💰  Paiements", "/paiement"),
        ]
        if self.role in ["superadmin", "admin", "agent", "secretariat"]:
            menu_items.append(("  Utilisateurs", "/utilisateurs"))

        menu_controls = []
        for texte, route in menu_items:
            is_active = route == "/utilisateurs"
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
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/concessions"), content=ft.Text("📜  Concessions", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/exhumations"), content=ft.Text("⚰️  Exhumations", color="white", size=14)),
            ]),
        )

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def build(self):
        c = self.get_colors()
        can_manage = self.role in ["superadmin", "admin"]

        if self.role == "client":
            return ft.View(
                route="/utilisateurs", bgcolor=c["bg"], padding=0,
                controls=[ft.Row(expand=True, spacing=0, controls=[
                    self.build_sidebar(),
                    ft.Container(expand=True, padding=25, bgcolor=c["bg"], alignment=ft.alignment.center, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, controls=[
                        ft.Text("🔒", size=80),
                        ft.Text("Acces interdit", size=28, weight=ft.FontWeight.BOLD, color="#F44336"),
                        ft.Text("Vous n'avez pas la permission d'acceder a cette page.", size=14, color="#666666", text_align=ft.TextAlign.CENTER),
                        ft.Text("La gestion des utilisateurs est reservee aux administrateurs.", size=13, color="#888888", text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("🏠 Retour au tableau de bord", on_click=lambda e: self.page.go("/dashboard"), style=ft.ButtonStyle(bgcolor="#1B5E20")),
                    ]))
                ])]
            )

        utilisateurs = self.get_utilisateurs()
        
        # ✅ CORRECTION : 'in' au lieu de '=='
        if self.role in ['admin', 'secretariat']:
            utilisateurs = [u for u in utilisateurs if u.get('role') != 'superadmin']
            
        demandes = self.get_users_en_attente()
        if utilisateurs:
            liste_users = [self.build_user_card(u) for u in utilisateurs]
        else:
            liste_users = [ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("Aucun utilisateur", size=16, color="#999999"))]

        controls_content = [
            ft.Text("Gestion des Utilisateurs", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
            ft.Text(str(len(utilisateurs)) + " utilisateur(s) enregistre(s)", size=13, color=c["subtext"]),
            ft.Container(height=15),
        ]

        if can_manage and demandes:
            controls_content.append(ft.Container(padding=20, bgcolor="#FFF8E1", border_radius=15, border=ft.border.all(2, "#FF9800"), content=ft.Column([ft.Text("⏳ " + str(len(demandes)) + " demande(s) en attente", size=16, weight=ft.FontWeight.BOLD, color="#E65100"), ft.Container(height=10)] + [self.build_demande_card(d) for d in demandes])))
            controls_content.append(ft.Container(height=20))

        if can_manage:
            controls_content.append(ft.Container(padding=25, bgcolor=c["card"], border_radius=15, shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.colors.with_opacity(0.08, "black")), content=ft.Column(spacing=15, controls=[
                ft.Text("➕ Ajouter un utilisateur", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                ft.Row(controls=[ft.Container(expand=True, content=self.nom), ft.Container(expand=True, content=self.prenom)], spacing=15),
                ft.Row(controls=[ft.Container(expand=True, content=self.email), ft.Container(expand=True, content=self.telephone)], spacing=15),
                ft.Row(controls=[ft.Container(expand=True, content=self.password), ft.Container(expand=True, content=self.role_dropdown)], spacing=15),
                self.message,
                ft.FilledButton("Creer l'utilisateur", on_click=self.handle_creer),
            ])))
            controls_content.append(ft.Container(height=20))

        controls_content.append(ft.Text("Liste des utilisateurs", size=18, weight=ft.FontWeight.BOLD, color=c["text"]))
        controls_content.append(ft.Container(height=10))
        controls_content.extend(liste_users)

        return ft.View(
            route="/utilisateurs", bgcolor=c["bg"], padding=0,
            controls=[ft.Row(expand=True, spacing=0, controls=[
                self.build_sidebar(),
                ft.Container(expand=True, padding=25, bgcolor=c["bg"], content=ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, controls=controls_content))
            ])]
        )