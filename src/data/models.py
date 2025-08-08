"""
Module de modèles optimisé avec cache et requêtes performantes
"""

import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from src.data.database import get_optimized_connection, get_connection

logger = logging.getLogger(__name__)

class ModelCache:
    """Cache simple en mémoire pour les requêtes fréquentes."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes par défaut
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        if key not in self._cache:
            return None
        
        # Vérifier l'expiration
        if datetime.now().timestamp() - self._timestamps[key] > self._ttl:
            self.delete(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Stocke une valeur dans le cache."""
        self._cache[key] = value
        self._timestamps[key] = datetime.now().timestamp()
    
    def delete(self, key: str) -> None:
        """Supprime une clé du cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Vide le cache complètement."""
        self._cache.clear()
        self._timestamps.clear()

# Instance globale du cache
_model_cache = ModelCache()

class UserManager:
    """Gestionnaire optimisé des utilisateurs."""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur par ID avec cache."""
        cache_key = f"user_{user_id}"
        cached_user = _model_cache.get(cache_key)
        
        if cached_user:
            return cached_user
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, created_at, last_login, is_active 
                FROM users 
                WHERE id = ? AND is_active = 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                user_data = dict(row)
                _model_cache.set(cache_key, user_data)
                return user_data
        
        return None
    
    @staticmethod
    def update_last_login(user_id: int):
        """Met à jour la dernière connexion."""
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (user_id,))
        
        # Invalider le cache
        _model_cache.delete(f"user_{user_id}")

class ModelChoiceManager:
    """Gestionnaire optimisé des choix de modèles."""
    
    @staticmethod
    def save_model_choice(user_id: int, model: str) -> None:
        """Sauvegarde le choix de modèle avec validation."""
        if not user_id or not model:
            raise ValueError("user_id et model sont requis")
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Utiliser INSERT OR REPLACE pour optimiser
            cursor.execute("""
                INSERT OR REPLACE INTO model_choices (user_id, model, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, model))
            
            # COMMIT OBLIGATOIRE pour éviter database locked
            conn.commit()
        
        # Invalider le cache
        _model_cache.delete(f"model_choice_{user_id}")
        logger.info(f"Modèle {model} sauvegardé pour utilisateur {user_id}")
    
    @staticmethod
    def get_user_model_choice(user_id: int) -> Optional[str]:
        """Récupère le choix de modèle avec cache."""
        cache_key = f"model_choice_{user_id}"
        cached_choice = _model_cache.get(cache_key)
        
        if cached_choice:
            return cached_choice
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model 
                FROM model_choices 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                model = row[0]
                _model_cache.set(cache_key, model)
                return model
        
        return None

class CampaignManager:
    """Gestionnaire optimisé des campagnes."""
    
    @staticmethod
    def create_campaign(
        user_id: int, 
        name: str, 
        themes: List[str], 
        language: str, 
        ai_model: str = "GPT-4o",
        gm_portrait: Optional[str] = None
    ) -> int:
        """Crée une nouvelle campagne avec validation."""
        if not all([user_id, name, language]):
            raise ValueError("user_id, name et language sont requis")
        
        themes_json = json.dumps(themes) if themes else "[]"
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO campaigns (user_id, name, themes, language, ai_model, gm_portrait)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, themes_json, language, ai_model, gm_portrait))
            
            campaign_id = cursor.lastrowid
        
        # Invalider le cache des campagnes utilisateur
        _model_cache.delete(f"user_campaigns_{user_id}")
        logger.info(f"Campagne '{name}' créée avec ID {campaign_id}")
        return campaign_id
    
    @staticmethod
    def update_campaign_portrait(campaign_id: int, gm_portrait_url: str) -> bool:
        """Met à jour le portrait du MJ d'une campagne."""
        try:
            with get_optimized_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE campaigns 
                    SET gm_portrait = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (gm_portrait_url, campaign_id))
                
                # Vérifier si une ligne a été modifiée
                if cursor.rowcount == 0:
                    logger.warning(f"Aucune campagne trouvée avec l'ID {campaign_id}")
                    return False
                
                conn.commit()
                
                # Invalider le cache
                cursor.execute("SELECT user_id FROM campaigns WHERE id = ?", (campaign_id,))
                row = cursor.fetchone()
                if row:
                    _model_cache.delete(f"user_campaigns_{row[0]}")
                
            logger.info(f"Portrait MJ mis à jour pour campagne {campaign_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour portrait MJ: {e}")
            return False
    
    @staticmethod
    def get_user_campaigns(user_id: int) -> List[Dict]:
        """Récupère les campagnes avec statistiques (optimisé)."""
        if not user_id or (isinstance(user_id, str) and not user_id.strip()):
            raise ValueError("user_id ne peut pas être None ou vide")
        
        cache_key = f"user_campaigns_{user_id}"
        cached_campaigns = _model_cache.get(cache_key)
        
        if cached_campaigns:
            return cached_campaigns
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Requête optimisée avec JOIN pour éviter les requêtes N+1
            cursor.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.themes,
                    c.language,
                    c.gm_portrait,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) as message_count,
                    MAX(m.timestamp) as last_activity
                FROM campaigns c
                LEFT JOIN messages m ON c.id = m.campaign_id
                WHERE c.user_id = ? AND c.is_active = 1
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """, (user_id,))
            
            campaigns = []
            for row in cursor.fetchall():
                campaign = {
                    "id": row[0],
                    "name": row[1],
                    "themes": json.loads(row[2]) if row[2] else [],
                    "language": row[3],
                    "gm_portrait": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "message_count": row[7] or 0,
                    "last_activity": row[8]
                }
                campaigns.append(campaign)
        
        # Cache pour 5 minutes
        _model_cache.set(cache_key, campaigns)
        return campaigns
    
    @staticmethod
    def update_campaign_timestamp(campaign_id: int):
        """Met à jour le timestamp de dernière activité."""
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE campaigns 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (campaign_id,))

class CharacterManager:
    """Gestionnaire optimisé des personnages."""
    
    @staticmethod
    def create_character(
        user_id: int,
        name: str,
        char_class: str,
        race: str,
        description: Optional[str] = None,
        portrait_url: Optional[str] = None,
        gender: Optional[str] = None,
        campaign_id: Optional[int] = None,
        level: int = 1
    ) -> int:
        """Crée un nouveau personnage."""
        if not all([user_id, name, char_class, race]):
            raise ValueError("user_id, name, char_class et race sont requis")
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO characters 
                (user_id, campaign_id, name, class, race, gender, level, description, portrait_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, campaign_id, name, char_class, race, gender, level, description, portrait_url))
            
            character_id = cursor.lastrowid
        
        # Invalider le cache
        _model_cache.delete(f"user_characters_{user_id}")
        logger.info(f"Personnage '{name}' créé avec ID {character_id}")
        return character_id
    
    @staticmethod
    def update_character_portrait(character_id: int, portrait_url: str) -> bool:
        """Met à jour le portrait d'un personnage."""
        try:
            with get_optimized_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE characters 
                    SET portrait_url = ?
                    WHERE id = ?
                """, (portrait_url, character_id))
                
                # Vérifier si une ligne a été modifiée
                if cursor.rowcount == 0:
                    logger.warning(f"Aucun personnage trouvé avec l'ID {character_id}")
                    return False
                
                conn.commit()
                
                # Invalider le cache
                cursor.execute("SELECT user_id FROM characters WHERE id = ?", (character_id,))
                row = cursor.fetchone()
                if row:
                    _model_cache.delete(f"user_characters_{row[0]}")
                
            logger.info(f"Portrait mis à jour pour personnage {character_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour portrait personnage: {e}")
            return False
    
    @staticmethod
    def get_user_characters(user_id: int) -> List[Dict]:
        """Récupère tous les personnages d'un utilisateur."""
        cache_key = f"user_characters_{user_id}"
        cached_characters = _model_cache.get(cache_key)
        
        if cached_characters:
            return cached_characters
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, class, race, gender, description, portrait_url, created_at
                FROM characters
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
            """, (user_id,))
            
            characters = []
            for row in cursor.fetchall():
                character = {
                    "id": row[0],
                    "name": row[1],
                    "class": row[2],
                    "race": row[3],
                    "gender": row[4],
                    "description": row[5],
                    "portrait_url": row[6],
                    "created_at": row[7]
                }
                characters.append(character)
        
        _model_cache.set(cache_key, characters)
        return characters

class MessageManager:
    """Gestionnaire optimisé des messages."""
    
    @staticmethod
    def store_message(
        user_id: int,
        role: str,
        content: str,
        campaign_id: Optional[int] = None,
        character_id: Optional[int] = None
    ) -> int:
        """Stocke un message avec optimisations."""
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (user_id, campaign_id, role, content, character_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, campaign_id, role, content, character_id))
            
            message_id = cursor.lastrowid
        
        # Mettre à jour l'activité de la campagne si applicable
        if campaign_id:
            CampaignManager.update_campaign_timestamp(campaign_id)
            # Invalider le cache des campagnes
            _model_cache.delete(f"user_campaigns_{user_id}")
        
        return message_id
    
    @staticmethod
    def get_campaign_messages(
        user_id: int, 
        campaign_id: Optional[int] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """Récupère les messages d'une campagne avec pagination."""
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            
            if campaign_id:
                cursor.execute("""
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE user_id = ? AND campaign_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (user_id, campaign_id, limit))
            else:
                # Récupérer les messages de la campagne la plus récente
                cursor.execute("""
                    SELECT m.role, m.content, m.timestamp
                    FROM messages m
                    JOIN campaigns c ON m.campaign_id = c.id
                    WHERE m.user_id = ? AND c.is_active = 1
                    ORDER BY c.updated_at DESC, m.timestamp ASC
                    LIMIT ?
                """, (user_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                message = {
                    "role": row[0],
                    "content": row[1],
                    "timestamp": row[2]
                }
                messages.append(message)
        
        return messages

class PerformanceManager:
    """Gestionnaire optimisé des données de performance."""
    
    @staticmethod
    def store_performance(
        user_id: int,
        model: str,
        latency: float,
        tokens_in: int,
        tokens_out: int,
        campaign_id: Optional[int] = None,
        cost_estimate: Optional[float] = None
    ) -> int:
        """Stocke les données de performance."""
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_logs 
                (user_id, campaign_id, model, latency, tokens_in, tokens_out, cost_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, campaign_id, model, latency, tokens_in, tokens_out, cost_estimate))
            
            log_id = cursor.lastrowid
        
        return log_id
    
    @staticmethod
    def get_performance_stats(
        user_id: int, 
        days: int = 7
    ) -> Dict[str, Any]:
        """Récupère les statistiques de performance avec cache."""
        cache_key = f"performance_stats_{user_id}_{days}"
        cached_stats = _model_cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques globales
            cursor.execute("""
                SELECT 
                    model,
                    COUNT(*) as count,
                    AVG(latency) as avg_latency,
                    SUM(tokens_in) as total_tokens_in,
                    SUM(tokens_out) as total_tokens_out,
                    SUM(cost_estimate) as total_cost
                FROM performance_logs
                WHERE user_id = ? 
                    AND timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY model
                ORDER BY count DESC
            """, (user_id, days))
            
            stats = {
                "by_model": {},
                "total_requests": 0,
                "total_cost": 0.0
            }
            
            for row in cursor.fetchall():
                model_stats = {
                    "count": row[1],
                    "avg_latency": round(row[2], 3) if row[2] else 0,
                    "total_tokens_in": row[3] or 0,
                    "total_tokens_out": row[4] or 0,
                    "total_cost": round(row[5], 4) if row[5] else 0
                }
                stats["by_model"][row[0]] = model_stats
                stats["total_requests"] += model_stats["count"]
                stats["total_cost"] += model_stats["total_cost"]
        
        # Cache pour 2 minutes (données de performance changent souvent)
        _model_cache.set(cache_key, stats)
        return stats

# Fonctions de rétrocompatibilité avec l'ancienne API
def save_model_choice(user_id: int, model: str) -> None:
    """Sauvegarde du choix de modèle (compatibilité)."""
    ModelChoiceManager.save_model_choice(user_id, model)

def get_user_model_choice(user_id: int) -> Optional[str]:
    """Récupération du choix de modèle (compatibilité)."""
    return ModelChoiceManager.get_user_model_choice(user_id)

def create_campaign(user_id: int, name: str, themes: List[str], language: str, ai_model: str = "GPT-4o", gm_portrait: Optional[str] = None) -> int:
    """Création de campagne (compatibilité)."""
    return CampaignManager.create_campaign(user_id, name, themes, language, ai_model, gm_portrait)

def get_user_campaigns(user_id: int) -> List[Dict]:
    """Récupération des campagnes (compatibilité)."""
    return CampaignManager.get_user_campaigns(user_id)

def create_character(user_id: int, name: str, char_class: str, race: str, description: Optional[str] = None, portrait_url: Optional[str] = None, campaign_id: Optional[int] = None, level: int = 1) -> int:
    """Création de personnage (compatibilité)."""
    return CharacterManager.create_character(
        user_id=user_id, 
        name=name, 
        char_class=char_class, 
        race=race, 
        description=description, 
        portrait_url=portrait_url, 
        campaign_id=campaign_id, 
        level=level
    )

def get_user_characters(user_id: int) -> List[Dict]:
    """Récupération des personnages (compatibilité)."""
    return CharacterManager.get_user_characters(user_id)

def get_campaign_messages(user_id: int, campaign_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Récupération des messages (compatibilité)."""
    return MessageManager.get_campaign_messages(user_id, campaign_id, limit)

def store_message(user_id: int, role: str, content: str, campaign_id: Optional[int] = None) -> int:
    """Stockage de message (compatibilité)."""
    return MessageManager.store_message(user_id, role, content, campaign_id)

def update_campaign_portrait(campaign_id: int, gm_portrait_url: str) -> bool:
    """Mise à jour du portrait MJ (compatibilité)."""
    return CampaignManager.update_campaign_portrait(campaign_id, gm_portrait_url)

def update_character_portrait(character_id: int, portrait_url: str) -> bool:
    """Mise à jour du portrait personnage (compatibilité)."""
    return CharacterManager.update_character_portrait(character_id, portrait_url)

# Fonction utilitaire pour nettoyer le cache
def clear_cache():
    """Nettoie le cache complet (utile pour les tests)."""
    _model_cache.clear()
    logger.info("Cache des modèles nettoyé")
