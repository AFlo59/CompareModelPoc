import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from database import get_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager pour les connexions à la base de données."""
    conn = get_connection()
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur base de données: {e}")
        raise
    else:
        conn.commit()
    finally:
        conn.close()

def save_model_choice(user_id: int, model: str) -> None:
    """Sauvegarde le choix de modèle d'un utilisateur."""
    if not user_id or not model:
        raise ValueError("user_id et model sont requis")
        
    with get_db_connection() as conn:
        c = conn.cursor()
        # Supprimer l'ancien choix et insérer le nouveau
        c.execute("DELETE FROM model_choices WHERE user_id = ?", (user_id,))
        c.execute("INSERT INTO model_choices (user_id, model) VALUES (?, ?)", (user_id, model))
        logger.info(f"Modèle {model} sauvegardé pour utilisateur {user_id}")

def create_campaign(user_id: int, name: str, themes: List[str], language: str) -> int:
    """
    Crée une nouvelle campagne.
    
    Returns:
        ID de la campagne créée
    """
    if not all([user_id, name, language]):
        raise ValueError("user_id, name et language sont requis")
        
    themes_str = json.dumps(themes or [])
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO campaigns (user_id, name, themes, language)
                     VALUES (?, ?, ?, ?)''', (user_id, name, themes_str, language))
        campaign_id = c.lastrowid
        logger.info(f"Campagne '{name}' créée avec ID {campaign_id} pour utilisateur {user_id}")
        return campaign_id

def create_character(user_id: int, name: str, classe: str, race: str, 
                    description: Optional[str] = None, portrait_url: Optional[str] = None) -> int:
    """
    Crée un nouveau personnage.
    
    Returns:
        ID du personnage créé
    """
    if not all([user_id, name, classe, race]):
        raise ValueError("user_id, name, classe et race sont requis")
        
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO characters (user_id, name, class, race, description, portrait_url)
                     VALUES (?, ?, ?, ?, ?, ?)''', 
                  (user_id, name, classe, race, description, portrait_url))
        character_id = c.lastrowid
        logger.info(f"Personnage '{name}' créé avec ID {character_id} pour utilisateur {user_id}")
        return character_id

def get_user_campaigns(user_id: int) -> List[Dict[str, Any]]:
    """Récupère toutes les campagnes d'un utilisateur."""
    if not user_id:
        raise ValueError("user_id est requis")
        
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, themes, language FROM campaigns WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = c.fetchall()
        
        campaigns = []
        for r in rows:
            try:
                themes = json.loads(r[2]) if r[2] else []
            except json.JSONDecodeError:
                logger.warning(f"Thèmes JSON invalides pour campagne {r[0]}")
                themes = []
                
            campaigns.append({
                "id": r[0], 
                "name": r[1], 
                "themes": themes, 
                "language": r[3]
            })
        
        return campaigns

def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    """Récupère tous les personnages d'un utilisateur."""
    if not user_id:
        raise ValueError("user_id est requis")
        
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""SELECT id, name, class, race, description, portrait_url 
                     FROM characters WHERE user_id = ? ORDER BY id DESC""", (user_id,))
        rows = c.fetchall()
        
        return [{
            "id": r[0],
            "name": r[1],
            "class": r[2],
            "race": r[3],
            "description": r[4],
            "portrait_url": r[5]
        } for r in rows]

def delete_campaign(user_id: int, campaign_id: int) -> bool:
    """Supprime une campagne et ses données associées."""
    with get_db_connection() as conn:
        c = conn.cursor()
        # Vérifier que la campagne appartient à l'utilisateur
        c.execute("SELECT id FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id))
        if not c.fetchone():
            return False
            
        # Supprimer les messages associés (optionnel selon la logique métier)
        c.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        # Supprimer la campagne
        c.execute("DELETE FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id))
        
        logger.info(f"Campagne {campaign_id} supprimée pour utilisateur {user_id}")
        return True
