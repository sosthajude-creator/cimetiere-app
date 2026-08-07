import flet as ft
import httpx
import json
import os
import webbrowser
import tempfile
import math


class CartePage:
    def __init__(self, page: ft.Page, api_url: str):
        self.page = page
        self.api_url = api_url
        self.user = page.session_data.get("user", {})
        self.caveaux = []
        self.is_dark = page.session_data.get("dark_mode", False)
        self.dialog = None
        self.role = self.user.get("role", "")
        self.cimetiere_id = self.user.get("cimetiere_id")
        self.message_creation = ft.Text("", size=13, weight=ft.FontWeight.BOLD)

    def get_colors(self):
        if self.is_dark:
            return {"bg": "#121212", "card": "#2C2C2C", "text": "#FFFFFF", "subtext": "#AAAAAA", "sidebar": "#1E1E1E"}
        else:
            return {"bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "subtext": "#888888", "sidebar": "#1B5E20"}

    def get_caveaux(self):
        try:
            url = f"{self.api_url}/caveaux/carte"
            if self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
                url += f"?cimetiere_id={self.cimetiere_id}"
            response = httpx.get(url, timeout=10)
            return response.json()
        except:
            return []

    def get_cimetieres(self):
        try:
            response = httpx.get(f"{self.api_url}/etablissements/", timeout=10)
            return response.json()
        except:
            return []

    def get_mon_cimetiere(self):
        if not self.cimetiere_id:
            return None
        try:
            cimetieres = self.get_cimetieres()
            for c in cimetieres:
                if str(c.get("id")) == self.cimetiere_id:
                    return c
        except:
            pass
        return None

    def get_zones(self):
        try:
            if not self.cimetiere_id:
                return []
            response = httpx.get(f"{self.api_url}/caveaux/zones?cimetiere_id={self.cimetiere_id}", timeout=10)
            return response.json()
        except:
            return []

    def get_blocs(self):
        try:
            if not self.cimetiere_id:
                return []
            response = httpx.get(f"{self.api_url}/caveaux/blocs?cimetiere_id={self.cimetiere_id}", timeout=10)
            return response.json()
        except:
            return []

    def afficher_infos_cimetiere(self, cimetiere_id, cimetiere_nom):
        try:
            response = httpx.get(f"{self.api_url}/etablissements/{cimetiere_id}/infos", timeout=10)
            infos = response.json()
            if "error" in infos:
                return
            response_cav = httpx.get(f"{self.api_url}/etablissements/{cimetiere_id}/caveaux-detail", timeout=10)
            caveaux = response_cav.json() if response_cav.status_code == 200 else []
            proprio = infos.get("proprietaire") or {}
            proprio_txt = f"{proprio.get('prenom', '')} {proprio.get('nom', '')}" if proprio else "Non renseigne"
            contenu = [
                ft.Text("🏛️ " + infos.get("nom", ""), size=20, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                ft.Divider(),
                ft.Row([ft.Icon(ft.icons.LOCATION_ON, color="#1B5E20"), ft.Text(infos.get("adresse", ""), size=13)], spacing=8),
                ft.Row([ft.Icon(ft.icons.EMAIL, color="#1B5E20"), ft.Text(infos.get("email", ""), size=13)], spacing=8),
                ft.Row([ft.Icon(ft.icons.PERSON, color="#1B5E20"), ft.Text("Proprietaire : " + proprio_txt, size=13)], spacing=8),
                ft.Row([ft.Icon(ft.icons.SQUARE_FOOT, color="#1B5E20"), ft.Text(f"Superficie : {infos.get('superficie', 0)} m²", size=13)], spacing=8),
                ft.Row([ft.Icon(ft.icons.PARK, color="#1B5E20"), ft.Text(f"{infos.get('total_zones', 0)} zone(s)", size=13)], spacing=8),
                ft.Row([ft.Icon(ft.icons.CONTROL_POINT, color="#1B5E20"), ft.Text(f"{infos.get('total_caveaux', 0)} caveau(x)", size=13)], spacing=8),
                ft.Container(height=15),
                ft.Text(" Caveaux disponibles pour reservation", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
            ]
            dispo = [c for c in caveaux if c.get("statut") == "disponible"]
            if dispo:
                for c in dispo[:5]:
                    contenu.append(
                        ft.Container(
                            padding=10, bgcolor="#E8F5E9", border_radius=8, margin=ft.margin.only(top=5),
                            content=ft.Row([
                                ft.Text(f"✅ N° {c.get('numero')} — Zone {c.get('zone')}", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{c.get('prix', 0):,.0f} FCFA", size=12, color="#1B5E20"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
                if len(dispo) > 5:
                    contenu.append(ft.Text(f"... et {len(dispo) - 5} autre(s) caveau(x)", size=11, color="#888888"))
            else:
                contenu.append(ft.Text("Aucun caveau disponible actuellement", size=12, color="#F44336"))
            contenu.append(ft.Container(height=15))
            contenu.append(
                ft.FilledButton(
                    "➡️ Faire une reservation",
                    on_click=lambda e, cid=cimetiere_id, cn=infos.get("nom", ""): self.aller_reservation(cid, cn),
                    style=ft.ButtonStyle(bgcolor="#1B5E20"),
                )
            )
            self.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Informations du cimetiere"),
                content=ft.Container(width=500, content=ft.Column(controls=contenu, scroll=ft.ScrollMode.AUTO, tight=True)),
                actions=[ft.TextButton("Fermer", on_click=self.close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.overlay.append(self.dialog)
            self.dialog.open = True
            self.page.update()
        except Exception as ex:
            print("Erreur:", ex)

    def aller_reservation(self, cimetiere_id, cimetiere_nom=""):
        self.page.session_data["cimetiere_selectionne"] = cimetiere_id
        self.page.session_data["cimetiere_nom"] = cimetiere_nom
        self.close_dialog(None)
        self.page.go("/reservations")

    def close_dialog(self, e):
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.open = False
            self.page.update()

    def ouvrir_carte(self, e):
        caveaux = self.get_caveaux()
        cimetieres = self.get_cimetieres()
        cimetiere_noms = {str(c.get("id")): c.get("nom", "Cimetiere") for c in cimetieres}
        mon_cimetiere = self.get_mon_cimetiere()
        markers = ""
    
        # ✅ Déterminer quels cimetières afficher selon le rôle
        cimetieres_a_afficher = []
    
        if self.role in ["superadmin", "client"]:
            # ✅ Superadmin (propriétaire) et Client : voient TOUS les cimetières
            cimetieres_a_afficher = cimetieres
        elif self.role in ["admin"]:
            # ✅ Admin : voit SES cimetières à lui
            try:
                response = httpx.get(
                    f"{self.api_url}/etablissements/mes-cimetieres",
                    params={"admin_email": self.user.get("email")},
                    timeout=10,
                )
                cimetieres_a_afficher = response.json()
            except Exception as ex:
                print(f"Erreur chargement mes cimetières: {ex}")
                cimetieres_a_afficher = []
        elif self.role in ["agent", "secretariat"] and self.cimetiere_id:
            # ✅ Agent/Secrétariat : voit SON cimetière
            cimetieres_a_afficher = [c for c in cimetieres if str(c.get("id")) == self.cimetiere_id]
        else:
            # Fallback : tous les cimetières
            cimetieres_a_afficher = cimetieres
    
        # ✅ Dessiner les limites des cimetières autorisés
        for c in cimetieres_a_afficher:
            lat_cim = c.get("latitude", 0)
            lng_cim = c.get("longitude", 0)
            superficie = c.get("superficie", 100)
            nom_cim = c.get("nom", "Cimetiere")
            adresse = c.get("adresse", "")
            cimetiere_id = str(c.get("id"))
        
            # ✅ Si superficie = 0 ou None, utiliser une valeur par défaut
            if not superficie or superficie <= 0:
                superficie = 100
        
            cote = math.sqrt(superficie)
            delta_lat = cote / 111139
            delta_lng = cote / (111139 * math.cos(math.radians(lat_cim)))
            coin_nw = [lat_cim + delta_lat/2, lng_cim - delta_lng/2]
            coin_ne = [lat_cim + delta_lat/2, lng_cim + delta_lng/2]
            coin_se = [lat_cim - delta_lat/2, lng_cim + delta_lng/2]
            coin_sw = [lat_cim - delta_lat/2, lng_cim - delta_lng/2]
        
            # ✅ Compter les caveaux de ce cimetière
            nb_caveaux = sum(1 for cav in caveaux if str(cav.get("cimetiere_id")) == cimetiere_id)
        
            markers += f"""
                var cimetierePolygon_{cimetiere_id.replace('-', '_')} = L.polygon([
                    {coin_nw}, {coin_ne}, {coin_se}, {coin_sw}
                ], {{
                    color: '#1B5E20',
                    fillColor: '#4CAF50',
                    fillOpacity: 0.15,
                    weight: 3,
                    dashArray: '5, 10'
                }}).addTo(map);
                cimetierePolygon_{cimetiere_id.replace('-', '_')}.bindPopup(`
                    <div style="text-align:center;min-width:200px;">
                        <h3 style="color:#1B5E20;margin:0 0 8px 0;">🏛️ {nom_cim}</h3>
                        <p style="margin:4px 0;font-size:12px;"> {adresse}</p>
                        <p style="margin:4px 0;font-size:12px;">📐 Superficie : {superficie} m²</p>
                        <p style="margin:4px 0;font-size:11px;color:#888;">{nb_caveaux} caveau(x) recensé(s)</p>
                    </div>
                `);
            """
    
        # ✅ Dessiner les caveaux
        for c in caveaux:
            couleur = {"disponible": "green", "reserve": "orange", "occupe": "red", "inexploitable": "gray"}.get(c.get("statut"), "gray")
            cimetiere_id = c.get("cimetiere_id", "")
            cimetiere_nom = cimetiere_noms.get(cimetiere_id, "Cimetiere")
            safe_id = c.get('id', '').replace('-', '')
            markers += f"""
                var marker{safe_id} = L.circleMarker([{c.get('latitude')}, {c.get('longitude')}], {{
                    radius: 10,
                    fillColor: '{couleur}',
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9
                }}).addTo(map);
                marker{safe_id}.bindPopup(`
                    <b>Caveau N° {c.get('numero')}</b><br>
                    Zone: {c.get('zone')}<br>
                    Statut: {c.get('statut', '').upper()}<br>
                    Cimetiere: {cimetiere_nom}<br>
                    {c.get('latitude')}, {c.get('longitude')}
                `);
            """
    
        # ✅ Centrer la carte
        if mon_cimetiere:
            center_lat = mon_cimetiere.get('latitude', -4.2667)
            center_lng = mon_cimetiere.get('longitude', 15.2833)
        elif cimetieres_a_afficher:
            center_lat = cimetieres_a_afficher[0].get('latitude', -4.2667)
            center_lng = cimetieres_a_afficher[0].get('longitude', 15.2833)
        elif caveaux:
            center_lat = caveaux[0].get('latitude', -4.2667)
            center_lng = caveaux[0].get('longitude', 15.2833)
        else:
            center_lat = -4.2667
            center_lng = 15.2833
    
        # ✅ Zoom adapté
        zoom_level = 15 if len(cimetieres_a_afficher) > 1 else 18
    
        # ✅ Message contextuel selon le rôle
        if self.role == "superadmin":
            nom_cim_affiche = f" Superadmin - {len(cimetieres_a_afficher)} cimetiere(s) total(aux)"
        elif self.role == "admin":
            nom_cim_affiche = f"🏢 {len(cimetieres_a_afficher)} cimetiere(s) sous votre gestion"
        elif self.role == "client":
            nom_cim_affiche = f"👤 {len(cimetieres_a_afficher)} cimetiere(s) disponible(s)"
        else:
            nom_cim_affiche = cimetieres_a_afficher[0].get('nom', '') if cimetieres_a_afficher else ''
    
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Carte des Cimetieres</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .info-panel {{
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: white; padding: 15px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2); max-width: 300px;
        }}
        .legend {{
            position: absolute; bottom: 10px; left: 10px; z-index: 1000;
            background: white; padding: 10px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3 style="margin:0 0 10px 0; color:#1B5E20;">️ Carte Interactive</h3>
        <p style="margin:0; font-size:13px;">{len(caveaux)} caveau(x) affiché(s)</p>
        <p style="margin:0; font-size:13px;">{len(cimetieres_a_afficher)} cimetiere(s) affiché(s)</p>
        {"<p style='margin:5px 0 0 0; font-size:12px; color:#1B5E20; font-weight:bold;'>🏛️ " + nom_cim_affiche + "</p>" if nom_cim_affiche else ""}
    </div>
    <div class="legend">
        <div style="font-size:12px;">
            <div style="margin:3px 0;"><span style="color:#1B5E20;">■</span> Cimetiere (Superficie)</div>
            <div style="margin:3px 0;"><span style="color:green;">●</span> Disponible</div>
            <div style="margin:3px 0;"><span style="color:orange;">●</span> Réservé</div>
            <div style="margin:3px 0;"><span style="color:red;">●</span> Occupé</div>
            <div style="margin:3px 0;"><span style="color:gray;">●</span> Inexploitable</div>
        </div>
    </div>
    <script>
        var map = L.map('map').setView([{center_lat}, {center_lng}], {zoom_level});
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }}).addTo(map);
        {markers}
    </script>
</body>
</html>"""
    
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
        tmp.write(html)
        tmp.close()
        webbrowser.open(f'file:///{tmp.name}')

    def build_formulaire_creation(self, c):
        if self.role not in ["admin", "superadmin"]:
            return ft.Container()
        if not self.cimetiere_id:
            return ft.Container(
                padding=20, bgcolor="#FFF3E0", border_radius=12, border=ft.border.all(2, "#FF9800"),
                content=ft.Text("️ Votre compte n'est pas lie a un cimetiere.", size=13, color="#E65100"),
            )
        
        # ✅ Charger les données fraîches à chaque affichage
        zones = self.get_zones()
        blocs = self.get_blocs()
        
        self.zone_nom = ft.TextField(label="Nom de la zone", border_radius=10, bgcolor="white")
        self.zone_superficie = ft.TextField(label="Superficie (m²)", border_radius=10, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)
        self.bloc_nom = ft.TextField(label="Nom du bloc", border_radius=10, bgcolor="white")
        
        # ✅ Dropdown des zones
        self.bloc_zone = ft.Dropdown(
            label="Zone (choisir une zone)",
            border_radius=10,
            bgcolor="white",
            options=[ft.dropdown.Option(str(z.get("id")), z.get("nom")) for z in zones],
            value=None,
        )
        
        self.caveau_numero = ft.TextField(label="Numero du caveau", border_radius=10, bgcolor="white")
        # ✅ SUPPRIMÉ : Champs latitude/longitude (plus besoin de les remplir)
        self.caveau_long = ft.TextField(label="Longueur (m)", border_radius=10, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)
        self.caveau_larg = ft.TextField(label="Largeur (m)", border_radius=10, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)
        self.caveau_prix = ft.TextField(label="Prix (FCFA)", border_radius=10, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER, value="75000")
        
        # ✅ Dropdown des blocs
        self.caveau_bloc = ft.Dropdown(
            label="Bloc (choisir un bloc)",
            border_radius=10,
            bgcolor="white",
            options=[ft.dropdown.Option(str(b.get("id")), f"{b.get('nom')} (Zone: {b.get('zone_nom')})") for b in blocs],
            value=None,
        )
        
        info_zones_blocs = ft.Container(
            padding=10,
            bgcolor="#E3F2FD",
            border_radius=8,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.INFO_OUTLINE, color="#1976D2", size=16),
                    ft.Text(
                        f" Actuellement : {len(zones)} zone(s) et {len(blocs)} bloc(s) créé(s)",
                        size=12,
                        color="#1565C0",
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
        )
        
        return ft.Container(
            padding=25, bgcolor=c["card"], border_radius=15,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.Colors.with_opacity(0.08, "black")),
            content=ft.Column(spacing=15, controls=[
                ft.Text("🏗️ Creer des zones, blocs et caveaux", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                info_zones_blocs,
                ft.Divider(),
                ft.Text("1️ Creer une zone", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                ft.Row(controls=[ft.Container(expand=True, content=self.zone_nom), ft.Container(expand=True, content=self.zone_superficie)], spacing=10),
                ft.FilledButton("➕ Creer la zone", on_click=self.handle_creer_zone, style=ft.ButtonStyle(bgcolor="#1B5E20")),
                ft.Divider(),
                ft.Text("2️ Creer un bloc", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                ft.Row(controls=[ft.Container(expand=True, content=self.bloc_nom), ft.Container(expand=True, content=self.bloc_zone)], spacing=10),
                ft.FilledButton("➕ Creer le bloc", on_click=self.handle_creer_bloc, style=ft.ButtonStyle(bgcolor="#1B5E20")),
                ft.Divider(),
                ft.Text("3️ Creer un caveau", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                self.caveau_numero,
                ft.Row(controls=[ft.Container(expand=True, content=self.caveau_long), ft.Container(expand=True, content=self.caveau_larg), ft.Container(expand=True, content=self.caveau_prix)], spacing=10),
                self.caveau_bloc,
                ft.FilledButton("➕ Creer le caveau", on_click=self.handle_creer_caveau, style=ft.ButtonStyle(bgcolor="#1B5E20")),
                self.message_creation,
            ]),
        )

    def handle_creer_zone(self, e):
        if not self.zone_nom.value or not self.zone_superficie.value:
            self.message_creation.value = "⚠️ Remplissez tous les champs"
            self.message_creation.color = "red"
            self.page.update()
            return
        try:
            response = httpx.post(
                f"{self.api_url}/caveaux/zones", 
                json={
                    "nom": self.zone_nom.value, 
                    "cimetiere_id": self.cimetiere_id, 
                    "superficie": float(self.zone_superficie.value), 
                    "exploitable": True
                }, 
                timeout=10
            )
            data = response.json()
            if "error" in data:
                self.message_creation.value = "❌ " + data["error"]
                self.message_creation.color = "red"
                self.page.update()
            else:
                # ✅ SUCCÈS : Mettre à jour directement le dropdown des zones
                self.message_creation.value = f"✅ Zone '{self.zone_nom.value}' creee avec succes !"
                self.message_creation.color = "green"
                
                nouvelles_zones = self.get_zones()
                self.bloc_zone.options = [ft.dropdown.Option(str(z.get("id")), z.get("nom")) for z in nouvelles_zones]
                self.bloc_zone.value = None  # Réinitialiser la sélection
                
                # Vider les champs pour la prochaine saisie
                self.zone_nom.value = ""
                self.zone_superficie.value = ""
                
                self.page.update()
        except Exception as ex:
            self.message_creation.value = "❌ Erreur : " + str(ex)
            self.message_creation.color = "red"
            self.page.update()

    def handle_creer_bloc(self, e):
        if not self.bloc_nom.value or not self.bloc_zone.value:
            self.message_creation.value = "⚠️ Remplissez tous les champs (nom + zone)"
            self.message_creation.color = "red"
            self.page.update()
            return
        try:
            response = httpx.post(
                f"{self.api_url}/caveaux/blocs", 
                json={
                    "nom": self.bloc_nom.value, 
                    "zone_id": self.bloc_zone.value
                }, 
                timeout=10
            )
            data = response.json()
            if "error" in data:
                self.message_creation.value = "❌ " + data["error"]
                self.message_creation.color = "red"
                self.page.update()
            else:
                # ✅ SUCCÈS : Mettre à jour directement le dropdown des blocs
                self.message_creation.value = f"✅ Bloc '{self.bloc_nom.value}' cree avec succes !"
                self.message_creation.color = "green"
                
                nouveaux_blocs = self.get_blocs()
                self.caveau_bloc.options = [ft.dropdown.Option(str(b.get("id")), f"{b.get('nom')} (Zone: {b.get('zone_nom')})") for b in nouveaux_blocs]
                self.caveau_bloc.value = None  # Réinitialiser la sélection
                
                # Vider le champ pour la prochaine saisie
                self.bloc_nom.value = ""
                
                self.page.update()
        except Exception as ex:
            self.message_creation.value = "❌ Erreur : " + str(ex)
            self.message_creation.color = "red"
            self.page.update()

    def handle_creer_caveau(self, e):
        if not all([self.caveau_numero.value, self.caveau_long.value, self.caveau_larg.value, self.caveau_bloc.value]):
            self.message_creation.value = "⚠️ Remplissez tous les champs"
            self.message_creation.color = "red"
            self.page.update()
            return
        
        try:
            # ✅ CALCUL AUTOMATIQUE des coordonnées GPS
            mon_cimetiere = self.get_mon_cimetiere()
            if mon_cimetiere:
                lat_base = mon_cimetiere.get("latitude", -4.2634)
                lng_base = mon_cimetiere.get("longitude", 15.2429)
                
                # Compter combien de caveaux existent déjà
                caveaux_existants = self.get_caveaux()
                nombre_caveaux = len(caveaux_existants)
                
                # Calculer un décalage automatique (grille 10x10)
                ligne = nombre_caveaux // 10  # Division entière
                colonne = nombre_caveaux % 10  # Reste
                
                # Décalage de 0.0001 degré ≈ 11 mètres
                latitude_auto = lat_base + (ligne * 0.0001)
                longitude_auto = lng_base + (colonne * 0.0001)
            else:
                # Valeurs par défaut
                latitude_auto = -4.2634
                longitude_auto = 15.2429
            
            response = httpx.post(
                f"{self.api_url}/caveaux/", 
                json={
                    "bloc_id": self.caveau_bloc.value, 
                    "numero": self.caveau_numero.value, 
                    "latitude": latitude_auto,  # ✅ Automatique
                    "longitude": longitude_auto,  # ✅ Automatique
                    "longueur": float(self.caveau_long.value), 
                    "largeur": float(self.caveau_larg.value), 
                    "prix": float(self.caveau_prix.value or 75000)
                }, 
                timeout=10
            )
            data = response.json()
            if "error" in data:
                self.message_creation.value = "❌ " + data["error"]
                self.message_creation.color = "red"
                self.page.update()
            else:
                # ✅ SUCCÈS : Vider les champs et afficher le message
                self.message_creation.value = f"✅ Caveau N° '{self.caveau_numero.value}' cree avec succes !"
                self.message_creation.color = "green"
                
                self.caveau_numero.value = ""
                self.caveau_long.value = ""
                self.caveau_larg.value = ""
                self.caveau_prix.value = "75000"
                self.caveau_bloc.value = None
                
                self.page.update()
        except Exception as ex:
            self.message_creation.value = "❌ Erreur : " + str(ex)
            self.message_creation.color = "red"
            self.page.update()

    def build_sidebar(self):
        return ft.Container(
            width=230, bgcolor="#1B5E20", padding=20,
            content=ft.Column(controls=[
                ft.Container(padding=ft.padding.only(bottom=15), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Container(width=65, height=65, bgcolor=ft.Colors.with_opacity(0.2, "white"), border_radius=32, alignment=ft.alignment.center, content=ft.Text("🏛️", size=32)),
                    ft.Container(height=8),
                    ft.Text("Gestion Cimetiere", color="white", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("Republique du Congo", color=ft.Colors.with_opacity(0.6, "white"), size=11, text_align=ft.TextAlign.CENTER),
                ])),
                ft.Divider(color=ft.Colors.with_opacity(0.3, "white")),
                ft.Container(height=10),
                ft.Text("MENU PRINCIPAL", color=ft.Colors.with_opacity(0.5, "white"), size=10),
                ft.Container(height=5),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/dashboard"), content=ft.Text("🏠  Tableau de bord", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, bgcolor=ft.Colors.with_opacity(0.2, "white"), content=ft.Text("🗺️  Carte des caveaux", color="white", size=14, weight=ft.FontWeight.BOLD)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/reservations"), content=ft.Text("📋  Reservations", color="white", size=14)),
                ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=10, on_click=lambda e: self.page.go("/paiement"), content=ft.Text("💰  Paiements", color="white", size=14)),
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

    def couleur_statut(self, statut):
        return {"disponible": "#4CAF50", "reserve": "#FF9800", "occupe": "#F44336", "inexploitable": "#9E9E9E"}.get(statut, "#9E9E9E")

    def build_caveau_card(self, caveau):
        couleur = self.couleur_statut(caveau.get("statut"))
        emoji = {"disponible": "✅", "reserve": "⏳", "occupe": "❌", "inexploitable": "⛔"}.get(caveau.get("statut"), "❓")
        cimetiere_nom = caveau.get("cimetiere_nom", "N/A")
        return ft.Container(
            padding=15, margin=ft.margin.only(bottom=10), bgcolor="white", border_radius=12,
            border=ft.border.all(2, couleur),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.1, "black")),
            content=ft.Column(spacing=8, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(f"{emoji} Caveau N° {caveau.get('numero')}", size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                    ft.Container(padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=couleur, border_radius=20, content=ft.Text(caveau.get("statut", "").upper(), size=11, color="white", weight=ft.FontWeight.BOLD)),
                ]),
                ft.Text(f"🏛️ Cimetiere : {cimetiere_nom}", size=12, color="#666666", weight=ft.FontWeight.BOLD),
                ft.Text(f"Zone : {caveau.get('zone')} — Bloc : {caveau.get('bloc', 'N/A')}", size=12, color="#666666"),
                ft.Text(f" {caveau.get('latitude')}, {caveau.get('longitude')}", size=11, color="#888888"),
                ft.Text(f"💰 Prix : {caveau.get('prix', 0):,.0f} FCFA", size=12, color="#1B5E20", weight=ft.FontWeight.BOLD),
                ft.Row(controls=[
                    ft.FilledButton("🏛️ Voir infos", on_click=lambda e, cid=caveau.get("cimetiere_id"), cn=caveau.get("cimetiere_nom"): self.afficher_infos_cimetiere(cid, cn), style=ft.ButtonStyle(bgcolor="#1B5E20")),
                ]),
            ]),
        )

    def build(self):
        self.caveaux = self.get_caveaux()
        c = self.get_colors()
        if self.role == "client":
            info_role = ft.Container(
                padding=15, bgcolor="#E3F2FD", border_radius=12, border=ft.border.all(2, "#2196F3"),
                content=ft.Row(controls=[ft.Icon(ft.icons.VISIBILITY, color="#1565C0"), ft.Text("👤 Vous visualisez tous les caveaux de tous les cimetieres disponibles", size=13, weight=ft.FontWeight.BOLD, color="#1565C0")]),
            )
        elif self.role in ["admin", "agent", "secretariat"] and self.cimetiere_id:
            mon_cim = self.get_mon_cimetiere()
            nom_cim = mon_cim.get("nom", "Mon cimetiere") if mon_cim else "Mon cimetiere"
            superficie = mon_cim.get("superficie", 0) if mon_cim else 0
            info_role = ft.Container(
                padding=15, bgcolor="#E8F5E9", border_radius=12, border=ft.border.all(2, "#1B5E20"),
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Row(controls=[ft.Icon(ft.icons.PARK, color="#1B5E20"), ft.Text(f"🔒 Cimetiere : {nom_cim}", size=13, weight=ft.FontWeight.BOLD, color="#1B5E20")]),
                        ft.Text(f"📐 Superficie : {superficie} m² | 📍 {len(self.caveaux)} caveau(x)", size=12, color="#555555"),
                    ],
                ),
            )
        else:
            info_role = ft.Container()
            
        if self.caveaux:
            liste_caveaux = [self.build_caveau_card(cv) for cv in self.caveaux]
        else:
            if self.cimetiere_id and self.role in ["admin", "superadmin"]:
                liste_caveaux = [ft.Container(padding=40, bgcolor="#FFF3E0", border_radius=12, border=ft.border.all(2, "#FF9800"), alignment=ft.alignment.center, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("⚠️", size=50), ft.Text("Aucun caveau dans votre cimetiere", size=16, color="#E65100", weight=ft.FontWeight.BOLD), ft.Text("Utilisez le formulaire ci-dessous pour creer des zones, blocs et caveaux.", size=13, color="#666666", text_align=ft.TextAlign.CENTER)]))]
            else:
                liste_caveaux = [ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("Aucun caveau enregistre", size=16, color="#999999"))]
                
        stats = {
            "disponible": sum(1 for cv in self.caveaux if cv.get("statut") == "disponible"),
            "reserve": sum(1 for cv in self.caveaux if cv.get("statut") == "reserve"),
            "occupe": sum(1 for cv in self.caveaux if cv.get("statut") == "occupe"),
            "inexploitable": sum(1 for cv in self.caveaux if cv.get("statut") == "inexploitable"),
        }
        
        return ft.View(
            route="/carte", bgcolor=c["bg"], padding=0,
            controls=[ft.Row(expand=True, spacing=0, controls=[
                self.build_sidebar(),
                ft.Container(expand=True, padding=25, bgcolor=c["bg"], content=ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS, controls=[
                    ft.Text("Carte des Caveaux", size=24, weight=ft.FontWeight.BOLD, color=c["text"]),
                    ft.Text(f"{len(self.caveaux)} caveau(x) affiche(s)", size=13, color=c["subtext"]),
                    ft.Container(height=15),
                    info_role,
                    ft.Container(height=15),
                    self.build_formulaire_creation(c) if self.role in ["admin", "superadmin"] else ft.Container(),
                    ft.Container(height=15) if self.role in ["admin", "superadmin"] else ft.Container(),
                    ft.Container(padding=20, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.Colors.with_opacity(0.08, "black")), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text("️  Carte Interactive", size=18, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                        ft.Text("Cliquez sur un caveau pour voir les informations du cimetiere", size=12, color="#888888", text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        ft.FilledButton("Ouvrir la carte dans le navigateur", on_click=self.ouvrir_carte),
                    ])),
                    ft.Container(height=15),
                    ft.Container(padding=20, bgcolor="white", border_radius=15, content=ft.Column(controls=[
                        ft.Text("Legende des couleurs", size=15, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                        ft.Container(height=10),
                        ft.Row(wrap=True, spacing=15, controls=[
                            ft.Row(controls=[ft.Container(width=20, height=20, bgcolor="#4CAF50", border_radius=10), ft.Text(f"Disponible ({stats['disponible']})", size=13)]),
                            ft.Row(controls=[ft.Container(width=20, height=20, bgcolor="#FF9800", border_radius=10), ft.Text(f"Reserve ({stats['reserve']})", size=13)]),
                            ft.Row(controls=[ft.Container(width=20, height=20, bgcolor="#F44336", border_radius=10), ft.Text(f"Occupe ({stats['occupe']})", size=13)]),
                            ft.Row(controls=[ft.Container(width=20, height=20, bgcolor="#9E9E9E", border_radius=10), ft.Text(f"Inexploitable ({stats['inexploitable']})", size=13)]),
                        ]),
                    ])),
                    ft.Container(height=15),
                    ft.Text("Liste des caveaux", size=18, weight=ft.FontWeight.BOLD, color=c["text"]),
                    ft.Container(height=10),
                ] + liste_caveaux))
            ])]
        )