import flet as ft
import httpx


class DashboardPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.cimetiere_id = self.user.get("cimetiere_id")

        # Sélecteur de cimetière
        self.cimetiere_selector = ft.Dropdown(
            label="Sélectionner un cimetière",
            border_radius=10,
            bgcolor="white",
            options=[],
            on_change=self.on_cimetiere_change,
        )

    def get_colors(self):
        if self.is_dark:
            return {
                "bg": "#121212",
                "sidebar": "#1E1E1E",
                "card": "#2C2C2C",
                "text": "#FFFFFF",
                "subtext": "#AAAAAA",
                "border": "#333333",
                "primary": "#4CAF50",
            }
        else:
            return {
                "bg": "#F5F5F5",
                "sidebar": "#1B5E20",
                "card": "#FFFFFF",
                "text": "#1B5E20",
                "subtext": "#888888",
                "border": "#E0E0E0",
                "primary": "#1B5E20",
            }

    def get_statistiques(self):
        try:
            url = f"{self.api_url}/caveaux/statistiques"
            if self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
                url += f"?cimetiere_id={self.cimetiere_id}"
            response = httpx.get(url, timeout=10)
            return response.json()
        except:
            return {}

    def get_stats_finances(self):
        try:
            response = httpx.get(f"{self.api_url}/finances/statistiques", timeout=10)
            return response.json()
        except:
            return {}

    def get_mon_cimetiere(self):
        if not self.cimetiere_id:
            return None
        try:
            response = httpx.get(f"{self.api_url}/etablissements/", timeout=10)
            cimetieres = response.json()
            for c in cimetieres:
                if str(c.get("id")) == self.cimetiere_id:
                    return c
        except:
            pass
        return None

    def charger_mes_cimetieres(self):
        """Charge la liste des cimetières de l'admin"""
        if self.role not in ["admin", "superadmin"]:
            return
        try:
            response = httpx.get(
                f"{self.api_url}/etablissements/mes-cimetieres",
                params={"admin_email": self.user.get("email")},
                timeout=10,
            )
            cimetieres = response.json()
            self.cimetiere_selector.options = [
                ft.dropdown.Option(str(c.get("id")), c.get("nom"))
                for c in cimetieres
            ]
            self.cimetiere_selector.value = self.cimetiere_id
        except Exception as ex:
            print(f"Erreur chargement cimetières: {ex}")

    def on_cimetiere_change(self, e):
        """Change le cimetière actif"""
        nouveau_cimetiere_id = self.cimetiere_selector.value
        if not nouveau_cimetiere_id:
            return
        try:
            response = httpx.post(
                f"{self.api_url}/etablissements/changer-cimetiere",
                json={
                    "admin_email": self.user.get("email"),
                    "cimetiere_id": nouveau_cimetiere_id,
                },
                timeout=10,
            )
            data = response.json()
            if "error" in data:
                print(f"Erreur: {data['error']}")
            else:
                self.page.session_data["user"]["cimetiere_id"] = nouveau_cimetiere_id
                self.cimetiere_id = nouveau_cimetiere_id
                self.page.go("/dashboard")
        except Exception as ex:
            print(f"Erreur changement cimetière: {ex}")

    def toggle_theme(self, e):
        self.is_dark = not self.is_dark
        self.page.session_data["dark_mode"] = self.is_dark
        self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        self.page.go("/dashboard")

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def menu_item(self, texte, route, selected=False):
        def on_click(e):
            self.page.go(route)
        bgcolor = ft.colors.with_opacity(0.2, "white") if selected else None
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=10,
            bgcolor=bgcolor,
            on_click=on_click,
            content=ft.Text(
                texte,
                color="white",
                size=14,
                weight=ft.FontWeight.BOLD if selected else ft.FontWeight.W_500,
            ),
        )

    def build_sidebar(self):
        c = self.get_colors()
        user = self.user
        theme_icon = "" if not self.is_dark else "☀️"
        theme_label = "Mode sombre" if not self.is_dark else "Mode clair"
        return ft.Container(
            width=230,
            bgcolor=c["sidebar"],
            padding=20,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=15),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=65,
                                    height=65,
                                    bgcolor=ft.colors.with_opacity(0.2, "white"),
                                    border_radius=32,
                                    alignment=ft.alignment.center,
                                    content=ft.Text("🏛️", size=32),
                                ),
                                ft.Container(height=8),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text(
                                            "Gestion Cimetière",
                                            color="white",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.DARK_MODE if not self.is_dark else ft.icons.LIGHT_MODE,
                                            icon_color="white",
                                            tooltip="Changer le thème",
                                            on_click=self.toggle_theme,
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    "République du Congo",
                                    color=ft.colors.with_opacity(0.6, "white"),
                                    size=11,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                    ),
                    ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                    ft.Container(height=8),
                    ft.Container(
                        padding=10,
                        bgcolor=ft.colors.with_opacity(0.15, "white"),
                        border_radius=10,
                        content=ft.Column(
                            spacing=3,
                            controls=[
                                ft.Text(
                                    f"{user.get('prenom', '')} {user.get('nom', '')}",
                                    color="white",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    user.get('role', '').upper(),
                                    color=ft.colors.with_opacity(0.7, "white"),
                                    size=11,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(height=15),
                    ft.Text("MENU PRINCIPAL", color=ft.colors.with_opacity(0.5, "white"), size=10),
                    ft.Container(height=5),
                    self.menu_item("🏠  Tableau de bord", "/dashboard", selected=True),
                    self.menu_item("🗺️  Carte des caveaux", "/carte"),
                    self.menu_item("📋  Réservations", "/reservations"),
                    self.menu_item("💰  Paiements", "/paiement"),
                    ft.Container(height=10),
                    ft.Text("ADMINISTRATION", color=ft.colors.with_opacity(0.5, "white"), size=10),
                    ft.Container(height=5),
                    self.menu_item("👥  Utilisateurs", "/utilisateurs"),
                    self.menu_item("📜  Concessions", "/concessions"),
                    self.menu_item("⚰️  Exhumations", "/exhumations"),
                    ft.Container(expand=True),
                    ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        border_radius=10,
                        on_click=self.toggle_theme,
                        content=ft.Text(
                            f"{theme_icon}  {theme_label}",
                            color="white",
                            size=14,
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        border_radius=10,
                        on_click=self.handle_logout,
                        content=ft.Text(
                            "🚪  Déconnexion",
                            color="#FF6B6B",
                            size=14,
                            weight=ft.FontWeight.W_500,
                        ),
                    ),
                ],
            ),
        )

    def build_stat_card(self, titre, valeur, couleur, emoji):
        c = self.get_colors()
        return ft.Container(
            expand=True,
            padding=20,
            bgcolor=c["card"],
            border_radius=15,
            border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.colors.with_opacity(0.08, "black"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(titre, size=12, color=c["subtext"]),
                            ft.Container(
                                width=35,
                                height=35,
                                bgcolor=ft.colors.with_opacity(0.15, couleur),
                                border_radius=10,
                                alignment=ft.alignment.center,
                                content=ft.Text(emoji, size=18),
                            ),
                        ],
                    ),
                    ft.Text(
                        str(valeur),
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=couleur,
                    ),
                ],
            ),
        )

    def build_caveau_bar(self, label, valeur, total, couleur):
        c = self.get_colors()
        pourcentage = (valeur / total * 100) if total > 0 else 0
        return ft.Column(
            spacing=5,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(label, size=13, color=c["text"]),
                        ft.Text(
                            f"{valeur} ({pourcentage:.0f}%)",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=couleur,
                        ),
                    ],
                ),
                ft.ProgressBar(
                    value=pourcentage / 100,
                    bgcolor=ft.colors.with_opacity(0.2, couleur),
                    color=couleur,
                    height=12,
                ),
            ],
        )

    def build_dashboard_content(self):
        c = self.get_colors()
        stats = self.get_statistiques()
        finances = self.get_stats_finances()
        total = stats.get("total", 0)

        # Charger les cimetières pour le sélecteur
        self.charger_mes_cimetieres()

        # Bandeau info selon le rôle
        if self.role == "client":
            info_role = ft.Container(
                padding=15,
                bgcolor="#E3F2FD",
                border_radius=12,
                border=ft.border.all(2, "#2196F3"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.VISIBILITY, color="#1565C0"),
                        ft.Text(
                            "👤 Vous visualisez les statistiques de tous les cimetières",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color="#1565C0",
                        ),
                    ],
                ),
            )
        elif self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
            mon_cim = self.get_mon_cimetiere()
            nom_cim = mon_cim.get("nom", "Mon cimetière") if mon_cim else "Mon cimetière"
            info_role = ft.Container(
                padding=15,
                bgcolor="#E8F5E9",
                border_radius=12,
                border=ft.border.all(2, "#1B5E20"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.PARK, color="#1B5E20"),
                        ft.Text(
                            f"🔒 Statistiques du cimetière : {nom_cim}",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color="#1B5E20",
                        ),
                    ],
                ),
            )
        else:
            info_role = ft.Container()

        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[
                ft.Container(
                    padding=ft.padding.only(bottom=25),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "Tableau de bord",
                                        size=26,
                                        weight=ft.FontWeight.BOLD,
                                        color=c["text"],
                                    ),
                                    ft.Text(
                                        "Vue d'ensemble de la gestion du cimetière",
                                        size=13,
                                        color=c["subtext"],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                info_role,
                ft.Container(height=15),

                # ✅ SÉLECTEUR DE CIMETIÈRE (pour admin)
                ft.Container(
                    padding=20,
                    bgcolor="#FFF3E0",
                    border_radius=15,
                    border=ft.border.all(2, "#FF9800"),
                    content=ft.Column(
                        controls=[
                            ft.Text("️ Sélectionner un cimetière", size=16, weight=ft.FontWeight.BOLD, color="#E65100"),
                            ft.Text("Choisissez le cimetière que vous souhaitez gérer", size=12, color="#666666"),
                            ft.Container(height=10),
                            self.cimetiere_selector,
                        ],
                    ),
                ) if self.role in ["admin", "superadmin"] else ft.Container(),
                ft.Container(height=20),

                # ✅ BOUTON NOUVEAU CIMETIÈRE
                ft.Container(
                    padding=20,
                    bgcolor="#E8F5E9",
                    border_radius=15,
                    border=ft.border.all(2, "#1B5E20"),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("🏛️ Créer un nouveau cimetière", size=16, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                    ft.Text("Ajoutez un nouveau cimetière à votre gestion", size=12, color="#666666"),
                                ],
                            ),
                            ft.FilledButton(
                                "➕ Nouveau cimetière",
                                on_click=lambda e: self.page.go("/nouveau-cimetiere"),
                                style=ft.ButtonStyle(bgcolor="#1B5E20", color="white"),
                            ),
                        ],
                    ),
                ) if self.role in ["admin", "superadmin"] else ft.Container(),
                ft.Container(height=20),

                # Cartes caveaux
                ft.Row(
                    spacing=15,
                    controls=[
                        self.build_stat_card("Total Caveaux", total, c["primary"], "🏛️"),
                        self.build_stat_card("Disponibles", stats.get("disponibles", 0), "#4CAF50", "✅"),
                        self.build_stat_card("Réservés", stats.get("reserves", 0), "#FF9800", "⏳"),
                        self.build_stat_card("Occupés", stats.get("occupes", 0), "#F44336", "❌"),
                    ],
                ),
                ft.Container(height=20),
                ft.Container(
                    padding=25,
                    bgcolor=c["card"],
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.08, "black"),
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Column(
                        spacing=15,
                        controls=[
                            ft.Text(
                                "📊 État des caveaux",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=c["text"],
                            ),
                            ft.Row(
                                wrap=True,
                                controls=[
                                    ft.Row(controls=[ft.Container(width=12, height=12, bgcolor="#4CAF50", border_radius=3), ft.Text("Disponible", size=12, color=c["subtext"])]),
                                    ft.Container(width=15),
                                    ft.Row(controls=[ft.Container(width=12, height=12, bgcolor="#FF9800", border_radius=3), ft.Text("Réservé", size=12, color=c["subtext"])]),
                                    ft.Container(width=15),
                                    ft.Row(controls=[ft.Container(width=12, height=12, bgcolor="#F44336", border_radius=3), ft.Text("Occupé", size=12, color=c["subtext"])]),
                                    ft.Container(width=15),
                                    ft.Row(controls=[ft.Container(width=12, height=12, bgcolor="#9E9E9E", border_radius=3), ft.Text("Inexploitable", size=12, color=c["subtext"])]),
                                ],
                            ),
                            self.build_caveau_bar("🟢 Disponibles", stats.get("disponibles", 0), max(total, 1), "#4CAF50"),
                            self.build_caveau_bar("🟠 Réservés", stats.get("reserves", 0), max(total, 1), "#FF9800"),
                            self.build_caveau_bar(" Occupés", stats.get("occupes", 0), max(total, 1), "#F44336"),
                            self.build_caveau_bar("⚫ Inexploitables", stats.get("inexploitables", 0), max(total, 1), "#9E9E9E"),
                        ],
                    ),
                ),
                ft.Container(height=20),
                ft.Row(
                    spacing=15,
                    controls=[
                        self.build_stat_card("Total Revenus (FCFA)", finances.get("total_revenus", 0), c["primary"], "💰"),
                        self.build_stat_card("Factures Payées", finances.get("factures_payees", 0), "#4CAF50", "✅"),
                        self.build_stat_card("Paiements Partiels", finances.get("factures_partielles", 0), "#2196F3", ""),
                        self.build_stat_card("En Attente", finances.get("factures_en_attente", 0), "#FF9800", "⏳"),
                    ],
                ),
                ft.Container(height=20),
                ft.Container(
                    padding=25,
                    bgcolor=c["card"],
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.08, "black"),
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "📈 Taux d'occupation global",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=c["text"],
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=15, vertical=5),
                                        bgcolor=c["primary"],
                                        border_radius=20,
                                        content=ft.Text(
                                            f"{stats.get('taux_occupation', 0)}%",
                                            color="white",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ),
                                ],
                            ),
                            ft.ProgressBar(
                                value=stats.get("taux_occupation", 0) / 100,
                                bgcolor=ft.colors.with_opacity(0.15, c["primary"]),
                                color=c["primary"],
                                height=18,
                            ),
                        ],
                    ),
                ),
                ft.Container(height=30),
            ],
        )

    def build(self):
        c = self.get_colors()
        return ft.View(
            route="/dashboard",
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
                            padding=30,
                            bgcolor=c["bg"],
                            content=self.build_dashboard_content(),
                        ),
                    ],
                )
            ],
        )