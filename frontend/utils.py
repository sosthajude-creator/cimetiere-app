import re


def valider_email(email):
    """Valide le format d'un email"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def valider_telephone_congo(telephone):
    """
    Valide un numéro de téléphone congolais
    Format accepté : (+242) XXXXXXXXX ou +242XXXXXXXX ou 0XXXXXXXX
    Doit contenir exactement 9 chiffres après l'indicatif
    """
    if not telephone:
        return True  # Téléphone optionnel
    
    # Nettoyer le numéro
    telephone_clean = telephone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Extraire les chiffres
    chiffres = re.sub(r'\D', '', telephone_clean)
    
    # Vérifier le format
    if telephone_clean.startswith("+242") or telephone_clean.startswith("242"):
        # Format international : doit avoir 9 chiffres après +242
        if len(chiffres) == 12:  # 242 + 9 chiffres
            return True
        return False
    elif telephone_clean.startswith("0"):
        # Format local : 0 + 9 chiffres = 10 chiffres total
        if len(chiffres) == 10:
            return True
        return False
    else:
        # Juste 9 chiffres
        if len(chiffres) == 9:
            return True
        return False


def valider_date(date_str):
    """Valide le format AAAA-MM-JJ"""
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return re.match(pattern, date_str) is not None


def valider_montant(montant):
    """Valide qu'un montant est un nombre positif"""
    try:
        valeur = float(montant)
        return valeur > 0
    except (ValueError, TypeError):
        return False


def valider_nom(nom):
    """Valide qu'un nom ne contient pas de chiffres"""
    if not nom:
        return False
    return not any(c.isdigit() for c in nom)