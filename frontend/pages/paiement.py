import flet as ft
import httpx
import webbrowser


class PaiementPage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.is_dark = page.session_data.get("dark_mode", False)
        self.role = self.user.get("role", "")
        self.cimetiere_id = self.user.get("cimetiere_id")
        
        # ✅ Client peut payer SES factures, Admin/Secretariat peuvent tout faire
        self.can_create_payment = self.role in ["superadmin", "secretariat", "admin", "client"]
        
        self.facture_id = ft.TextField(label="ID de la facture", border_radius=10, bgcolor="white", read_only=(self.role == "client"))
        self.montant = ft.TextField(label="Montant (FCFA)", border_radius=10, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)
        self.canal = ft.Dropdown(
            label="Mode de paiement", border_radius=10, bgcolor="white",
            options=[
                ft.dropdown.Option("mobile_money", " MTN Mobile Money"),
                ft.dropdown.Option("airtel_money", "📱 Airtel Money"),
                ft.dropdown.Option("wave", " Wave"),
                ft.dropdown.Option("orange_money", "📱 Orange Money"),
                ft.dropdown.Option("especes", "💵 Especes"),
                ft.dropdown.Option("virement", " Virement bancaire"),
                ft.dropdown.Option("carte_bancaire", "💳 Carte bancaire"),
            ],
            value="mobile_money", on_change=self.on_canal_change,
        )
        self.numero_telephone = ft.TextField(label="Numero de telephone", border_radius=10, bgcolor="white", visible=True)
        self.numero_carte = ft.TextField(label="Numero de carte", border_radius=10, bgcolor="white", visible=False, password=True)
        self.message = ft.Text("", size=13)
        self.loading = ft.ProgressRing(visible=False, color="#1B5E20")
        self.resultat_container = ft.Column(visible=False, controls=[])

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888"}

    def on_canal_change(self, e):
        canal = self.canal.value
        self.numero_telephone.visible = canal in ["mobile_money", "airtel_money", "wave", "orange_money"]
        self.numero_carte.visible = canal == "carte_bancaire"
        self.page.update()

    def get_factures(self, include_payees=False):
        """Récupère les factures selon le rôle"""
        try:
            url = f"{self.api_url}/finances/"
            params = {}
            
            # ✅ Client voit seulement ses factures
            if self.role == "client":
                params["client_email"] = self.user.get('email')
            # ✅ Admin/Agent/Secretariat voient toutes les factures de leur cimetière
            elif self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
                params["cimetiere_id"] = self.cimetiere_id
            
            # ✅ Option pour exclure les factures payées
            if not include_payees:
                params["include_payees"] = "false"
            
            response = httpx.get(url, params=params, timeout=10)
            return response.json()
        except:
            return []

    def pre_remplir_paiement(self, facture_id, montant_restant):
        """Pré-remplit le formulaire avec les infos de la facture"""
        self.facture_id.value = facture_id
        self.montant.value = str(montant_restant)
        self.message.value = ""
        self.resultat_container.visible = False
        self.page.update()

    def handle_paiement(self, e):
        if not self.facture_id.value or not self.montant.value:
            self.message.value = "⚠️ Veuillez remplir tous les champs"
            self.message.color = "red"
            self.page.update()
            return
        
        self.loading.visible = True
        self.message.value = "⏳ Traitement du paiement en cours..."
        self.message.color = "#1B5E20"
        self.page.update()
        
        try:
            response = httpx.post(
                f"{self.api_url}/finances/simuler-paiement",
                json={
                    "facture_id": self.facture_id.value,
                    "montant": float(self.montant.value),
                    "canal": self.canal.value,
                    "numero_telephone": self.numero_telephone.value or None,
                    "numero_carte": self.numero_carte.value or None,
                    "enregistre_par_email": self.user.get("email"),
                },
                timeout=15,
            )
            data = response.json()
            self.loading.visible = False
            
            if "error" in data:
                self.message.value = f"❌ {data['error']}"
                self.message.color = "red"
                self.resultat_container.visible = False
            else:
                self.message.value = ""
                self.resultat_container.visible = True
                self.resultat_container.controls = [
                    ft.Container(padding=20, bgcolor="#E8F5E9", border_radius=12, border=ft.border.all(2, "#4CAF50"), content=ft.Column(spacing=8, controls=[
                        ft.Text("✅ Paiement reussi !", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                        ft.Divider(),
                        ft.Text(f"✅ {data.get('message')}", size=13),
                        ft.Text(f" Reference : {data.get('reference')}", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(f"💰 Montant paye : {data.get('montant_paye')} FCFA", size=13),
                        ft.Text(f" Reste a payer : {data.get('montant_restant')} FCFA", size=13),
                        ft.Text(f"📋 Statut : {data.get('statut_facture', '').upper()}", size=13, color="#1B5E20", weight=ft.FontWeight.BOLD),
                    ]))
                ]
                
                # ✅ Vider le formulaire
                self.facture_id.value = ""
                self.montant.value = ""
                
                # ✅ Recharger la page après 2 secondes pour voir les mises à jour
                import threading
                import time
                def reload_after_delay():
                    time.sleep(2)
                    self.page.go("/paiement")
                threading.Thread(target=reload_after_delay, daemon=True).start()
                
        except Exception as ex:
            self.loading.visible = False
            self.message.value = f"❌ Erreur : {str(ex)}"
            self.message.color = "red"
        
        self.page.update()

    def handle_telecharger_pdf(self, facture_id):
        try:
            response = httpx.post(f"{self.api_url}/finances/{facture_id}/generer-pdf", timeout=15)
            data = response.json()
            if "error" in data:
                self.message.value = f" {data['error']}"
                self.message.color = "red"
                self.page.update()
                return
            webbrowser.open(f"{self.api_url}/finances/{facture_id}/telecharger-pdf")
            self.message.value = "✅ Facture PDF telechargee !"
            self.message.color = "green"
            self.page.update()
        except Exception as ex:
            self.message.value = f"❌ Erreur : {str(ex)}"
            self.message.color = "red"
            self.page.update()

    def build_facture_card(self, f):
        statut_couleurs = {"en_attente": "#FF9800", "partielle": "#2196F3", "payee": "#4CAF50"}
        emoji = {"en_attente": "", "partielle": "📊", "payee": "✅"}
        couleur = statut_couleurs.get(f.get("statut"), "#9E9E9E")
        
        # ✅ Boutons selon le statut et le rôle
        boutons = []
        
        # Télécharger PDF (tout le monde)
        boutons.append(ft.FilledButton("📄 Telecharger PDF", on_click=lambda e, fid=f.get("id"): self.handle_telecharger_pdf(fid), style=ft.ButtonStyle(bgcolor="#1B5E20", color="white")))
        
        # ✅ Bouton Payer (seulement si facture non payée ET client ou admin)
        if f.get("statut") in ["en_attente", "partielle"] and self.can_create_payment:
            boutons.append(
                ft.FilledButton(
                    "💳 Payer",
                    on_click=lambda e, fid=f.get("id"), montant=f.get("montant_restant"): self.pre_remplir_paiement(fid, montant),
                    style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"),
                )
            )
        
        return ft.Container(
            padding=15, margin=ft.margin.only(bottom=10), bgcolor="white", border_radius=12,
            border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Column(spacing=6, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(f"👤 {f.get('client')}", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=4), bgcolor=couleur, border_radius=20, content=ft.Text(f"{emoji.get(f.get('statut'), '')} {f.get('statut', '').upper()}", size=11, color="white", weight=ft.FontWeight.BOLD)),
                ]),
                ft.Text(f"💰 Montant total : {f.get('montant')} FCFA", size=13),
                ft.Text(f"✅ Montant paye : {f.get('montant_paye')} FCFA", size=13, color="#4CAF50"),
                ft.Text(f"⏳ Reste : {f.get('montant_restant')} FCFA", size=13, color="#F44336"),
                ft.Text(f"🔖 ID : {f.get('id')}", size=11, color="#888888", selectable=True),
                ft.Container(height=5),
                ft.Row(controls=boutons, spacing=10),
            ]),
        )

    def build_sidebar(self):
        return ft.Container(
            width=230, bgcolor="#1B5E20", padding=20,
            content=ft.Column(controls=[
                ft.Container(padding=ft.padding.only(bottom=15), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Container(width=65, height=65, bgcolor=ft.colors.with_opacity(0.2, "white"), border_radius=32, alignment=ft.alignment.center, content=ft.Text("🏛️", size=32)),
                    ft.Container(height=8),
                    ft.Text("Gestion Cimetiere", color="white", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("Republique du Congo", color=ft.colors.with_opacity(0.6, "white"), size=11, text_align=ft.TextAlign.CENTER),
                ])),
                ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                ft.Container(height=10),
                ft.Text("MENU PRINCIPAL", color=ft.colors.with_opacity(0.5, "white"), size=10),
                ft.Container(height=5),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/dashboard"), content=ft.Text("🏠  Tableau de bord", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/carte"), content=ft.Text("🗺️  Carte des caveaux", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/reservations"), content=ft.Text("📋  Reservations", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, bgcolor=ft.colors.with_opacity(0.2, "white"), content=ft.Text("💰  Paiements", color="white", size=14, weight=ft.FontWeight.BOLD)),
                ft.Container(height=10),
                ft.Divider(color=ft.colors.with_opacity(0.3, "white")),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=self.handle_logout, content=ft.Text("  Deconnexion", color="#FF6B6B", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/concessions"), content=ft.Text("📜  Concessions", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/exhumations"), content=ft.Text("⚰️  Exhumations", color="white", size=14)),
            ]),
        )

    def handle_logout(self, e):
        self.page.session_data = {}
        self.page.go("/login")

    def build(self):
        c = self.get_colors()
        
        # ✅ Récupérer les factures NON payées pour le formulaire
        factures_non_payees = self.get_factures(include_payees=False)
        # ✅ Récupérer TOUTES les factures pour l'affichage
        toutes_factures = self.get_factures(include_payees=True)
        
        if toutes_factures:
            liste_factures = [self.build_facture_card(f) for f in toutes_factures]
        else:
            liste_factures = [ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("💰", size=50), ft.Text("Aucune facture disponible", size=16, color="#999999")]))]
        
        # ✅ Formulaire de paiement (visible pour client ET admin/secretariat)
        formulaire = ft.Container(
            padding=25, bgcolor=c["card"], border_radius=15,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.colors.with_opacity(0.08, "black")),
            content=ft.Column(spacing=15, controls=[
                ft.Text("💳 Effectuer un paiement", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                ft.Divider(),
                ft.Text("💡 Cliquez sur 'Payer' sur une facture pour remplir automatiquement", size=12, color="#666666"),
                ft.Container(height=10),
                self.facture_id, self.montant, self.canal,
                self.numero_telephone, self.numero_carte,
                self.loading, self.message,
                ft.FilledButton("💳 Confirmer le paiement", on_click=self.handle_paiement),
                self.resultat_container,
            ]),
        ) if self.can_create_payment else ft.Container()
        
        return ft.View(
            route="/paiement", bgcolor=c["bg"], padding=0,
            controls=[ft.Row(expand=True, spacing=0, controls=[
                self.build_sidebar(),
                ft.Container(expand=True, padding=25, bgcolor=c["bg"], content=ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, controls=[
                    ft.Text("Paiements", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
                    ft.Text("Gestion des paiements et factures", size=13, color=c["subtext"]),
                    ft.Container(height=15),
                    formulaire,
                    ft.Container(height=20),
                    ft.Text("📋 Liste des factures", size=18, weight=ft.FontWeight.BOLD, color=c["text"]),
                    ft.Container(height=10),
                ] + liste_factures))
            ])]
        )