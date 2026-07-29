import flet as ft
import httpx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import valider_email, valider_telephone_congo

# ✅ Liste des villes du Congo avec leurs coordonnées GPS
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


class InscriptionPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.role_selectionne = "client"
        self.message = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)

        # Champs communs
        self.nom = ft.TextField(label="Nom *", border_radius=30, bgcolor="#F5F5F5", border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"))
        self.prenom = ft.TextField(label="Prenom *", border_radius=30, bgcolor="#F5F5F5", border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"))
        self.email = ft.TextField(label="Email *", border_radius=30, bgcolor="#F5F5F5", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"))
        self.telephone = ft.TextField(label="Telephone", border_radius=30, bgcolor="#F5F5F5", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"), keyboard_type=ft.KeyboardType.PHONE)
        self.password = ft.TextField(label="Mot de passe *", password=True, can_reveal_password=True, border_radius=30, bgcolor="#F5F5F5", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"))
        self.password_confirm = ft.TextField(label="Confirmer mot de passe *", password=True, can_reveal_password=True, border_radius=30, bgcolor="#F5F5F5", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"))

        # Dropdown cimetière pour agent/secrétariat
        self.cimetiere_dropdown = ft.Dropdown(
            label="Choisir un cimetiere *",
            border_radius=30,
            bgcolor="#FFF3E0",
            width=400,
            border_color="#FF9800",
            focused_border_color="#FF9800",
            label_style=ft.TextStyle(color="#FF9800"),
            visible=False,
            options=[],
            hint_text="Sélectionnez le cimetière",
        )
        self.cimetieres_data = {}

        # Champs admin
        self.nom_cimetiere = ft.TextField(label="Nom du cimetiere *", border_radius=30, bgcolor="#E8F5E9", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"), visible=False)
        self.adresse_cimetiere = ft.TextField(label="Adresse du cimetiere *", border_radius=30, bgcolor="#E8F5E9", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"), visible=False)
        self.email_cimetiere_admin = ft.TextField(label="Email officiel du cimetiere *", border_radius=30, bgcolor="#E8F5E9", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"), visible=False)
        
        self.ville_dropdown = ft.Dropdown(
            label="Ville du cimetiere *",
            border_radius=30,
            bgcolor="#E8F5E9",
            width=400,
            border_color="#1B5E20",
            focused_border_color="#1B5E20",
            label_style=ft.TextStyle(color="#1B5E20"),
            visible=False,
            options=[ft.dropdown.Option(ville, ville) for ville in VILLES_CONGO.keys()],
            value="Brazzaville",
            on_change=self.on_ville_change,
        )
        
        self.latitude_cimetiere = ft.TextField(label="Latitude GPS (automatique)", border_radius=30, bgcolor="#F5F5F5", width=400, visible=False, read_only=True)
        self.longitude_cimetiere = ft.TextField(label="Longitude GPS (automatique)", border_radius=30, bgcolor="#F5F5F5", width=400, visible=False, read_only=True)
        self.superficie_cimetiere = ft.TextField(label="Superficie (m²) *", border_radius=30, bgcolor="#E8F5E9", width=400, border_color="#1B5E20", focused_border_color="#1B5E20", label_style=ft.TextStyle(color="#1B5E20"), visible=False, keyboard_type=ft.KeyboardType.NUMBER)
        
        self.info_ville = ft.Container(
            padding=12,
            bgcolor="#E3F2FD",
            border_radius=10,
            width=400,
            visible=False,
            content=ft.Text(
                " Coordonnées GPS : -4.2634, 15.2429 (Brazzaville)",
                size=12,
                color="#1565C0",
                text_align=ft.TextAlign.CENTER,
            ),
        )

        # Sélection du rôle
        self.role_buttons = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            wrap=True,
            controls=[
                self.build_role_btn("👤 Client", "client", True),
                self.build_role_btn("🏢 Admin", "admin", False),
                self.build_role_btn(" Secrétariat", "secretariat", False),
                self.build_role_btn("🚶 Agent", "agent", False),
            ],
        )
        self.info_role = ft.Container(
            padding=12,
            bgcolor="#E8F5E9",
            border_radius=10,
            width=400,
            content=ft.Text(
                "ℹ️ Le compte client permet de faire des reservations de caveaux.",
                size=12,
                color="#1B5E20",
                text_align=ft.TextAlign.CENTER,
            ),
        )
        
        self.champs_agent = ft.Column(
            visible=False,
            controls=[
                ft.Container(
                    padding=12,
                    bgcolor="#FFF3E0",
                    border_radius=10,
                    width=400,
                    content=ft.Text(
                        "️ Sélectionnez le cimetiere pour lequel vous souhaitez travailler.",
                        size=12,
                        color="#E65100",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                self.cimetiere_dropdown,
            ],
            spacing=10,
        )
        
        self.champs_admin = ft.Column(
            visible=False,
            controls=[
                ft.Container(
                    padding=12,
                    bgcolor="#E8F5E9",
                    border_radius=10,
                    width=400,
                    content=ft.Text(
                        "🏢 En tant qu'administrateur, vous devez renseigner les informations de votre cimetiere.",
                        size=12,
                        color="#1B5E20",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                self.nom_cimetiere,
                self.adresse_cimetiere,
                self.email_cimetiere_admin,
                self.ville_dropdown,
                self.info_ville,
                self.latitude_cimetiere,
                self.longitude_cimetiere,
                self.superficie_cimetiere,
            ],
            spacing=10,
        )

    def charger_cimetieres_disponibles(self):
        try:
            response = httpx.get(f"{self.api_url}/etablissements/", timeout=10)
            cimetieres = response.json()
            self.cimetiere_dropdown.options = []
            for c in cimetieres:
                cid = str(c.get("id"))
                nom = c.get("nom", "Sans nom")
                self.cimetieres_data[cid] = c.get("email_cimetiere", "")
                self.cimetiere_dropdown.options.append(ft.dropdown.Option(cid, nom))
            self.page.update()
        except Exception as e:
            print("Erreur chargement cimetières:", e)

    def on_ville_change(self, e):
        ville = self.ville_dropdown.value
        if ville in VILLES_CONGO:
            lat, lng = VILLES_CONGO[ville]
            self.latitude_cimetiere.value = str(lat)
            self.longitude_cimetiere.value = str(lng)
            self.info_ville.content.value = f"📍 Coordonnées GPS : {lat}, {lng} ({ville})"
            self.info_ville.visible = True
            self.page.update()

    def build_role_btn(self, label, role, selected):
        bgcolor = "#1B5E20" if selected else "#F5F5F5"
        color = "white" if selected else "#333333"
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=bgcolor,
            border_radius=20,
            border=ft.border.all(1, "#1B5E20"),
            on_click=lambda e, r=role: self.select_role(r),
            content=ft.Text(label, size=13, color=color, weight=ft.FontWeight.BOLD),
        )

    def select_role(self, role):
        self.role_selectionne = role
        infos = {
            "client": "ℹ️ Le compte client permet de faire des reservations de caveaux.",
            "admin": "🏢 En tant qu'administrateur, vous gerez un ou plusieurs cimetieres.",
            "secretariat": " Le secretariat gere les reservations et les paiements d'un cimetiere.",
            "agent": " L'agent de terrain gere les caveaux sur le terrain.",
        }
        self.info_role.content.value = infos.get(role, "")
        
        self.champs_agent.visible = role in ['agent', 'secretariat']
        self.cimetiere_dropdown.visible = role in ['agent', 'secretariat']
        
        if role in ['agent', 'secretariat'] and len(self.cimetiere_dropdown.options) == 0:
            self.charger_cimetieres_disponibles()

        self.champs_admin.visible = role == 'admin'
        self.nom_cimetiere.visible = role == 'admin'
        self.adresse_cimetiere.visible = role == 'admin'
        self.email_cimetiere_admin.visible = role == 'admin'
        self.ville_dropdown.visible = role == 'admin'
        self.info_ville.visible = role == 'admin'
        self.latitude_cimetiere.visible = False
        self.longitude_cimetiere.visible = False
        self.superficie_cimetiere.visible = role == 'admin'
        
        if role == 'admin':
            self.on_ville_change(None)
        
        self.role_buttons.controls = [
            self.build_role_btn("👤 Client", "client", role == "client"),
            self.build_role_btn("🏢 Admin", "admin", role == "admin"),
            self.build_role_btn("📋 Secrétariat", "secretariat", role == "secretariat"),
            self.build_role_btn("🚶 Agent", "agent", role == "agent"),
        ]
        self.page.update()

    def handle_inscription(self, e):
        # Validation champs obligatoires
        if not all([self.nom.value, self.prenom.value, self.email.value, self.password.value, self.password_confirm.value]):
            self.message.value = "Veuillez remplir tous les champs obligatoires (*)"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation email
        if not valider_email(self.email.value):
            self.message.value = "Adresse email invalide (ex: nom@domaine.com)"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation téléphone
        if self.telephone.value and not valider_telephone_congo(self.telephone.value):
            self.message.value = "Numero de telephone invalide. Format : (+242) XXXXXXXXX (9 chiffres)"
            self.message.color = "red"
            self.page.update()
            return
        
        if self.password.value != self.password_confirm.value:
            self.message.value = "Les mots de passe ne correspondent pas"
            self.message.color = "red"
            self.page.update()
            return
        
        if len(self.password.value) < 6:
            self.message.value = "Le mot de passe doit contenir au moins 6 caracteres"
            self.message.color = "red"
            self.page.update()
            return
        
        try:
            if self.role_selectionne == 'admin':
                if not all([self.nom_cimetiere.value, self.adresse_cimetiere.value, self.email_cimetiere_admin.value, self.ville_dropdown.value, self.superficie_cimetiere.value]):
                    self.message.value = "Veuillez remplir toutes les informations du cimetiere"
                    self.message.color = "red"
                    self.page.update()
                    return
                
                # ✅ Validation email cimetière
                if not valider_email(self.email_cimetiere_admin.value):
                    self.message.value = "Email du cimetiere invalide"
                    self.message.color = "red"
                    self.page.update()
                    return
                
                # ✅ Validation superficie
                try:
                    superficie = float(self.superficie_cimetiere.value)
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
                
                ville = self.ville_dropdown.value
                lat, lng = VILLES_CONGO[ville]
                
                response = httpx.post(
                    self.api_url + "/auth/register-admin",
                    json={
                        "email": self.email.value,
                        "password": self.password.value,
                        "nom": self.nom.value,
                        "prenom": self.prenom.value,
                        "telephone": self.telephone.value or "",
                        "email_cimetiere": self.email_cimetiere_admin.value,
                        "nom_cimetiere": self.nom_cimetiere.value,
                        "adresse_cimetiere": self.adresse_cimetiere.value,
                        "ville_cimetiere": ville,
                        "latitude_cimetiere": lat,
                        "longitude_cimetiere": lng,
                        "superficie_cimetiere": superficie,
                    },
                    timeout=60,  # ✅ CORRIGÉ : 15 → 60
                )
            else:
                if self.role_selectionne in ['agent', 'secretariat'] and not self.cimetiere_dropdown.value:
                    self.message.value = "Veuillez sélectionner un cimetiere dans la liste"
                    self.message.color = "red"
                    self.page.update()
                    return
                
                response = httpx.post(
                    self.api_url + "/auth/register",
                    json={
                        "email": self.email.value,
                        "password": self.password.value,
                        "nom": self.nom.value,
                        "prenom": self.prenom.value,
                        "telephone": self.telephone.value or "",
                        "role": self.role_selectionne,
                        "cimetiere_id": self.cimetiere_dropdown.value if self.role_selectionne in ['agent', 'secretariat'] else None,
                    },
                    timeout=60,  # ✅ CORRIGÉ : 15 → 60
                )
            data = response.json()
            if "error" in data:
                self.message.value = data["error"]
                self.message.color = "red"
            else:
                self.message.value = data.get("message", "Compte cree avec succes !")
                self.message.color = "#1B5E20"
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def build(self):
        return ft.View(
            route="/inscription",
            bgcolor="#FFFFFF",
            controls=[
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        # Partie gauche
                        ft.Container(
                            expand=1,
                            bgcolor="#1B5E20",
                            alignment=ft.alignment.center,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=20,
                                controls=[
                                    ft.Container(width=120, height=120, bgcolor=ft.colors.with_opacity(0.2, "white"), border_radius=60, alignment=ft.alignment.center, content=ft.Text("️", size=60)),
                                    ft.Text("Rejoignez-nous !", size=28, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                                    ft.Text("Creez votre compte pour\nacceder aux services", size=14, color=ft.colors.with_opacity(0.8, "white"), text_align=ft.TextAlign.CENTER),
                                    ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                                    ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=10,
                                        controls=[
                                            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Container(width=8, height=8, bgcolor="white", border_radius=4), ft.Text("Reservation de caveaux", color="white", size=13)], spacing=10),
                                            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Container(width=8, height=8, bgcolor="white", border_radius=4), ft.Text("Suivi de vos dossiers", color="white", size=13)], spacing=10),
                                            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Container(width=8, height=8, bgcolor="white", border_radius=4), ft.Text("Paiements securises", color="white", size=13)], spacing=10),
                                            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Container(width=8, height=8, bgcolor="white", border_radius=4), ft.Text("Gestion multi-cimetières", color="white", size=13)], spacing=10),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        # Partie droite
                        ft.Container(
                            expand=1,
                            bgcolor="white",
                            alignment=ft.alignment.center,
                            padding=30,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                scroll=ft.ScrollMode.AUTO,
                                spacing=15,
                                controls=[
                                    ft.Text("Creer un compte", size=26, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                    ft.Text("Choisissez votre role", size=13, color="#888888"),
                                    self.role_buttons,
                                    self.info_role,
                                    ft.Container(height=5),
                                    ft.Row(controls=[ft.Container(expand=True, content=self.nom), ft.Container(expand=True, content=self.prenom)], spacing=10, width=400),
                                    self.email,
                                    self.telephone,
                                    self.password,
                                    self.password_confirm,
                                    self.champs_agent,
                                    self.champs_admin,
                                    self.message,
                                    ft.Container(
                                        width=400,
                                        height=50,
                                        bgcolor="#1B5E20",
                                        border_radius=30,
                                        alignment=ft.alignment.center,
                                        on_click=self.handle_inscription,
                                        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.3, "#1B5E20"), offset=ft.Offset(0, 4)),
                                        content=ft.Text("Creer mon compte", color="white", size=16, weight=ft.FontWeight.BOLD),
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text("Deja un compte ?", size=13, color="#666666"),
                                            ft.TextButton("Se connecter", style=ft.ButtonStyle(color="#1B5E20"), on_click=lambda e: self.page.go("/login")),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                )
            ],
        )