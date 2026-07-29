import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings


def generer_facture_pdf(facture):
    """✅ Génère une facture PDF et retourne (chemin_complet, nom_fichier)"""
    # Créer le dossier media/factures
    dossier = os.path.join(settings.MEDIA_ROOT, 'factures')
    os.makedirs(dossier, exist_ok=True)

    nom_fichier = f"facture_{str(facture.id)[:8].upper()}.pdf"
    chemin = os.path.join(dossier, nom_fichier)

    # Créer le document PDF
    doc = SimpleDocTemplate(
        chemin,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        'titre', parent=styles['Heading1'],
        fontSize=22, textColor=colors.HexColor('#1B5E20'),
        alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica-Bold',
    )
    style_sous_titre = ParagraphStyle(
        'sous_titre', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER, spaceAfter=5,
    )
    style_section = ParagraphStyle(
        'section', parent=styles['Normal'],
        fontSize=13, textColor=colors.HexColor('#1B5E20'),
        fontName='Helvetica-Bold', spaceAfter=8,
    )

    # Récupérer les données
    reservation = facture.reservation
    client = reservation.client
    caveau = reservation.caveau
    paiements = facture.paiements.all()

    contenu = []

    # ===== EN-TÊTE =====
    contenu.append(Paragraph("REPUBLIQUE DU CONGO", style_sous_titre))
    contenu.append(Paragraph("Administration des Cimetieres", style_sous_titre))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#1B5E20')))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph("FACTURE OFFICIELLE", style_titre))
    contenu.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CCCCCC')))
    contenu.append(Spacer(1, 0.5*cm))

    # ===== NUMÉRO ET DATE =====
    data_info = [
        ['N° Facture :', str(facture.id)[:8].upper()],
        ['Date emission :', datetime.now().strftime('%d/%m/%Y a %H:%M')],
        ['Statut :', facture.statut.upper()],
    ]
    table_info = Table(data_info, colWidths=[4*cm, 12*cm])
    table_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1B5E20')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    contenu.append(table_info)
    contenu.append(Spacer(1, 0.5*cm))

    # ===== CLIENT =====
    contenu.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0')))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph("INFORMATIONS CLIENT", style_section))
    data_client = [
        ['Nom complet :', f"{client.prenom} {client.nom}"],
        ['Email :', client.email],
        ['Telephone :', client.telephone or 'Non renseigne'],
    ]
    table_client = Table(data_client, colWidths=[4*cm, 12*cm])
    table_client.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    contenu.append(table_client)
    contenu.append(Spacer(1, 0.5*cm))

    # ===== DÉTAILS CONCESSION =====
    contenu.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0')))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph("DETAILS DE LA CONCESSION", style_section))

    data_caveau = [
        ['Caveau N° :', caveau.numero],
        ['Zone :', caveau.zone.nom if caveau.zone else 'N/A'],
        ['Superficie :', f"{caveau.longueur} m x {caveau.largeur} m"],
        ['Defunt :', f"{reservation.defunt_prenom} {reservation.defunt_nom}"],
        ['Date de deces :', reservation.defunt_deces.strftime('%d/%m/%Y') if reservation.defunt_deces else 'N/A'],
    ]

    try:
        concession = reservation.concession
        data_caveau.append(['Type concession :', concession.type_concess.upper()])
        data_caveau.append(['Date debut :', concession.date_debut.strftime('%d/%m/%Y')])
        if concession.date_fin:
            data_caveau.append(['Date fin :', concession.date_fin.strftime('%d/%m/%Y')])
        else:
            data_caveau.append(['Date fin :', 'Perpetuelle'])
    except:
        pass

    table_caveau = Table(data_caveau, colWidths=[5*cm, 11*cm])
    table_caveau.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    contenu.append(table_caveau)
    contenu.append(Spacer(1, 0.5*cm))

    # ===== MONTANTS =====
    contenu.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0')))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph("DETAILS FINANCIERS", style_section))

    data_montants = [
        ['Description', 'Montant (FCFA)'],
        ['Frais de concession', f"{float(facture.montant):,.0f}"],
    ]

    for p in paiements:
        data_montants.append([
            f"Paiement via {p.canal.replace('_', ' ').title()} ({p.reference})",
            f"-{float(p.montant):,.0f}"
        ])

    data_montants.append(['MONTANT TOTAL', f"{float(facture.montant):,.0f}"])
    data_montants.append(['MONTANT PAYE', f"{float(facture.montant_paye):,.0f}"])
    data_montants.append(['RESTE A PAYER', f"{float(facture.montant_restant):,.0f}"])

    table_montants = Table(data_montants, colWidths=[12*cm, 4*cm])
    table_montants.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B5E20')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#F5F5F5')),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1B5E20')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    contenu.append(table_montants)
    contenu.append(Spacer(1, 1*cm))

    # ===== PIED DE PAGE =====
    contenu.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1B5E20')))
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph(
        "Ce document est une facture officielle de l'Administration des Cimetieres de la Republique du Congo.",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
    ))
    contenu.append(Paragraph(
        f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
        ParagraphStyle('footer2', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
    ))

    # ✅ Générer le PDF
    doc.build(contenu)

    # ✅ Vérifier que le fichier existe
    if not os.path.exists(chemin):
        raise Exception("Le fichier PDF n'a pas pu etre genere")

    return chemin, nom_fichier