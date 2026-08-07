import flet as ft
import httpx
import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import valider_email


class LoginPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.compte_rebours = 0
        self.timer_actif = False

        self.email_field = ft.TextField(
            label="Email",
            border_radius=30,
            bgcolor="#F5F5F5",
            width=380,
            border_color="#1B5E20",
            focused_border_color="#1B5E20",
            label_style=ft.TextStyle(color="#1B5E20"),
        )
        self.password_field = ft.TextField(
            label="Mot de passe",
            password=True,
            can_reveal_password=True,
            border_radius=30,
            bgcolor="#F5F5F5",
            width=380,
            border_color="#1B5E20",
            focused_border_color="#1B5E20",
            label_style=ft.TextStyle(color="#1B5E20"),
        )
        self.mfa_field = ft.TextField(
            label="Code MFA (6 chiffres)",
            border_radius=30,
            bgcolor="#F5F5F5",
            width=380,
            visible=False,
            border_color="#1B5E20",
            focused_border_color="#1B5E20",
            label_style=ft.TextStyle(color="#1B5E20"),
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.message = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)

        self.login_btn = ft.Container(
            width=380,
            height=50,
            bgcolor="#1B5E20",
            border_radius=30,
            alignment=ft.alignment.center,
            on_click=self.handle_login,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.3, "#1B5E20"), offset=ft.Offset(0, 4)),
            content=ft.Text("Se connecter", color="white", size=16, weight=ft.FontWeight.BOLD),
        )

        self.mfa_btn = ft.Container(
            width=380,
            height=50,
            bgcolor="#2E7D32",
            border_radius=30,
            alignment=ft.alignment.center,
            on_click=self.handle_mfa,
            visible=False,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.3, "#1B5E20"), offset=ft.Offset(0, 4)),
            content=ft.Text("Verifier le code MFA", color="white", size=16, weight=ft.FontWeight.BOLD),
        )

        self.renvoyer_btn = ft.TextButton(
            " Renvoyer le code MFA",
            style=ft.ButtonStyle(color="#1B5E20", bgcolor="#E8F5E9", padding=ft.padding.symmetric(horizontal=20, vertical=10)),
            on_click=self.handle_renvoyer_code,
            visible=False,
        )

        self.compte_rebours_text = ft.Text(
            "",
            size=12,
            color="#888888",
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

    def handle_login(self, e):
        if not self.email_field.value or not self.password_field.value:
            self.message.value = "Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation email
        if not valider_email(self.email_field.value):
            self.message.value = "Adresse email invalide"
            self.message.color = "red"
            self.page.update()
            return
        
        try:
            self.message.value = "⏳ Connexion en cours (le serveur peut mettre 30-50 secondes à répondre)..."
            self.message.color = "#FF9800"
            self.page.update()
            
            response = httpx.post(
                self.api_url + "/auth/login",
                json={"email": self.email_field.value, "password": self.password_field.value},
                timeout=60,
            )
            
            # ✅ Vérifie si la réponse est du JSON
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                self.message.value = "⏳ Le serveur est en train de se réveiller. Réessaie dans 30 secondes."
                self.message.color = "#FF9800"
                self.page.update()
                return
            
            data = response.json()
            if "error" in data:
                self.message.value = data["error"]
                self.message.color = "red"
                self.mfa_field.visible = False
                self.mfa_btn.visible = False
                self.renvoyer_btn.visible = False
                self.compte_rebours_text.visible = False
                self.login_btn.visible = True
            else:
                self.message.value = "✅ Code MFA envoyé par email ! Vérifiez votre boîte de réception."
                self.message.color = "#1B5E20"
                self.mfa_field.visible = True
                self.mfa_btn.visible = True
                self.login_btn.visible = False
                self.page.session_data["email"] = self.email_field.value

                self.renvoyer_btn.visible = True
                self.compte_rebours_text.visible = True
                self.lancer_compte_rebours()

        except Exception as ex:
            self.message.value = "Erreur de connexion : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_mfa(self, e):
        if not self.mfa_field.value:
            self.message.value = "Veuillez entrer le code MFA"
            self.message.color = "red"
            self.page.update()
            return
        
        # ✅ Validation : exactement 6 chiffres
        if not self.mfa_field.value.isdigit() or len(self.mfa_field.value) != 6:
            self.message.value = "Le code MFA doit contenir exactement 6 chiffres"
            self.message.color = "red"
            self.page.update()
            return
        
        try:
            response = httpx.post(
                self.api_url + "/auth/verify-mfa",
                json={"email": self.page.session_data.get("email"), "code": self.mfa_field.value},
                timeout=60,
            )
            data = response.json()
            if "error" in data:
                self.message.value = data["error"]
                self.message.color = "red"
            else:
                self.page.session_data["token"] = data["access_token"]
                self.page.session_data["user"] = data["user"]
                self.timer_actif = False
                self.page.go("/dashboard")
        except Exception as ex:
            self.message.value = "Erreur : " + str(ex)
            self.message.color = "red"
        self.page.update()

    def handle_renvoyer_code(self, e):
        if self.compte_rebours > 0:
            self.message.value = f"⏳ Veuillez attendre {self.compte_rebours} secondes avant de renvoyer un nouveau code."
            self.message.color = "#FF9800"
            self.page.update()
            return

        if not self.page.session_data.get("email"):
            self.message.value = "Email non trouve. Veuillez vous reconnecter."
            self.message.color = "red"
            self.page.update()
            return

        try:
            self.renvoyer_btn.disabled = True
            self.message.value = " Envoi du nouveau code en cours..."
            self.message.color = "#1B5E20"
            self.page.update()

            response = httpx.post(
                self.api_url + "/auth/login",
                json={
                    "email": self.page.session_data.get("email"),
                    "password": self.password_field.value,
                },
                timeout=60,
            )
            data = response.json()

            if "error" in data:
                self.message.value = "❌ " + data["error"]
                self.message.color = "red"
            else:
                self.message.value = "✅ Nouveau code MFA envoye par email ! Verifiez votre boite de reception."
                self.message.color = "#1B5E20"
                self.lancer_compte_rebours()

        except Exception as ex:
            self.message.value = "❌ Erreur : " + str(ex)
            self.message.color = "red"
        finally:
            self.renvoyer_btn.disabled = False
        self.page.update()

    def lancer_compte_rebours(self):
        self.compte_rebours = 60
        self.timer_actif = True
        self.renvoyer_btn.disabled = True
        self.mettre_a_jour_compte_rebours()

    def mettre_a_jour_compte_rebours(self):
        if not self.page or not self.timer_actif:
            return
        
        try:
            if self.compte_rebours > 0 and self.timer_actif:
                self.compte_rebours_text.value = f" Nouveau code disponible dans {self.compte_rebours} secondes"
                self.compte_rebours -= 1
                
                if self.page:
                    self.page.update()
                
                threading.Timer(1.0, self.mettre_a_jour_compte_rebours).start()
            else:
                self.timer_actif = False
                self.compte_rebours_text.value = "✅ Vous pouvez maintenant renvoyer un nouveau code"
                self.compte_rebours_text.color = "#4CAF50"
                self.renvoyer_btn.disabled = False
                
                if self.page:
                    self.page.update()
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                print("️ Event loop fermé, arrêt du compte à rebours")
                self.timer_actif = False
                return
            raise
        except Exception as e:
            print(f"Erreur compte à rebours: {e}")
            self.timer_actif = False

    def build(self):
        return ft.View(
            route="/login",
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
                                    ft.Container(
                                        width=120,
                                        height=120,
                                        bgcolor=ft.colors.with_opacity(0.2, "white"),
                                        border_radius=60,
                                        alignment=ft.alignment.center,
                                        content=ft.Text("🏛️", size=60),
                                    ),
                                    ft.Text(
                                        "Gestion de\nCimetiere",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color="white",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Republique du Congo",
                                        size=16,
                                        color=ft.colors.with_opacity(0.8, "white"),
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Divider(color=ft.colors.with_opacity(0.3, "white"), thickness=1),
                                    ft.Text(
                                        "Systeme de gestion\ndes espaces funeraires",
                                        size=13,
                                        color=ft.colors.with_opacity(0.6, "white"),
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                            ),
                        ),
                        # Partie droite
                        ft.Container(
                            expand=1,
                            bgcolor="white",
                            alignment=ft.alignment.center,
                            padding=40,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=20,
                                controls=[
                                    ft.Text(
                                        "Connexion",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1B5E20",
                                    ),
                                    ft.Text(
                                        "Entrez vos identifiants pour acceder",
                                        size=13,
                                        color="#888888",
                                    ),
                                    ft.Container(height=10),
                                    self.email_field,
                                    self.password_field,
                                    self.mfa_field,
                                    self.message,
                                    self.login_btn,
                                    self.mfa_btn,
                                    self.compte_rebours_text,
                                    self.renvoyer_btn,
                                    ft.Container(height=5),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text("Pas encore de compte ?", size=13, color="#666666"),
                                            ft.TextButton(
                                                "S'inscrire",
                                                style=ft.ButtonStyle(color="#1B5E20"),
                                                on_click=lambda e: self.page.go("/inscription"),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                )
            ],
        )