"""
Utilitaires pour la gestion des images et portraits
"""

import base64
import os
from pathlib import Path
from typing import Optional


def get_portrait_path(portrait_path: str) -> Optional[str]:
    """
    Récupère le chemin d'accès correct pour un portrait.

    Args:
        portrait_path: Chemin du portrait (peut être URL ou chemin local)

    Returns:
        Chemin accessible ou URL, None si le fichier n'existe pas
    """
    # Si c'est une URL externe (Dicebear ou autre), la retourner directement
    if portrait_path.startswith(("http://", "https://")):
        return portrait_path

    # Si c'est un chemin local relatif (static/portraits/...)
    if portrait_path.startswith("static/"):
        # Vérifier si le fichier existe
        file_path = Path(portrait_path)
        if file_path.exists():
            return str(file_path)
        else:
            return None

    return portrait_path


def image_to_base64(image_path: str) -> Optional[str]:
    """
    Convertit une image locale en base64 pour affichage dans Streamlit.

    Args:
        image_path: Chemin vers l'image locale

    Returns:
        String base64 de l'image ou None si erreur
    """
    try:
        if not os.path.exists(image_path):
            return None

        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode()
            return f"data:image/png;base64,{img_base64}"
    except Exception:
        return None


def display_portrait(portrait_path: str, width: int = 150, caption: str = "") -> str:
    """
    Prépare une image pour affichage dans Streamlit.

    Args:
        portrait_path: Chemin du portrait
        width: Largeur d'affichage
        caption: Légende de l'image

    Returns:
        URL ou chemin pour st.image()
    """
    # Si c'est une URL externe, la retourner directement
    if portrait_path.startswith(("http://", "https://")):
        return portrait_path

    # Si c'est un fichier local
    if portrait_path.startswith("static/") and os.path.exists(portrait_path):
        # Dans Streamlit, on peut directement passer le chemin du fichier
        return portrait_path

    # Fallback: retourner le chemin original (peut causer une erreur d'affichage)
    return portrait_path
