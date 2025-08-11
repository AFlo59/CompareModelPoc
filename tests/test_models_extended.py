"""
Tests étendus pour le module data.models - améliorer la couverture
"""

import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.models import (
    CampaignManager,
    CharacterManager,
    ModelCache,
    ModelChoiceManager,
    UserManager,
    _model_cache,
    clear_cache,
)


class TestModelCache:
    """Tests pour la classe ModelCache."""

    def setup_method(self):
        """Setup pour chaque test."""
        self.cache = ModelCache(ttl_seconds=60)

    def test_cache_init(self):
        """Test initialisation du cache."""
        cache = ModelCache(ttl_seconds=120)
        assert cache._ttl == 120
        assert cache._cache == {}
        assert cache._timestamps == {}

    def test_cache_set_and_get(self):
        """Test set et get basiques."""
        self.cache.set("key1", "value1")
        result = self.cache.get("key1")

        assert result == "value1"
        assert "key1" in self.cache._cache
        assert "key1" in self.cache._timestamps

    def test_cache_get_nonexistent(self):
        """Test get d'une clé inexistante."""
        result = self.cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """Test expiration du cache."""
        # Utiliser un TTL très court
        cache = ModelCache(ttl_seconds=0.1)
        cache.set("key1", "value1")

        # Immédiatement, la valeur devrait être là
        assert cache.get("key1") == "value1"

        # Attendre expiration
        time.sleep(0.2)

        # Maintenant elle devrait être expirée
        assert cache.get("key1") is None
        assert "key1" not in cache._cache

    def test_cache_delete(self):
        """Test suppression manuelle."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        self.cache.delete("key1")
        assert self.cache.get("key1") is None
        assert "key1" not in self.cache._cache

    def test_cache_delete_nonexistent(self):
        """Test suppression d'une clé inexistante."""
        # Ne devrait pas lever d'erreur
        self.cache.delete("nonexistent")

    def test_cache_clear(self):
        """Test nettoyage complet du cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        assert len(self.cache._cache) == 2

        self.cache.clear()

        assert len(self.cache._cache) == 0
        assert len(self.cache._timestamps) == 0

    def test_global_cache_clear(self):
        """Test de la fonction clear_cache globale."""
        _model_cache.set("test_key", "test_value")
        assert _model_cache.get("test_key") == "test_value"

        clear_cache()

        assert _model_cache.get("test_key") is None


class TestUserManager:
    """Tests pour UserManager."""

    def setup_method(self):
        """Setup pour chaque test."""
        clear_cache()  # Nettoyer le cache avant chaque test

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_by_id_success(self, mock_get_connection):
        """Test récupération utilisateur par ID - succès."""
        # Mock de la connexion
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Mock du résultat de la DB
        mock_row = {
            "id": 1,
            "email": "test@example.com",
            "created_at": "2024-01-01 00:00:00",
            "last_login": None,
            "is_active": 1,
        }
        mock_cursor.fetchone.return_value = mock_row

        result = UserManager.get_user_by_id(1)

        assert result == mock_row
        mock_cursor.execute.assert_called_once()

        # Vérifier que le résultat est mis en cache
        cached_result = _model_cache.get("user_1")
        assert cached_result == mock_row

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_by_id_not_found(self, mock_get_connection):
        """Test récupération utilisateur par ID - non trouvé."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        mock_cursor.fetchone.return_value = None

        result = UserManager.get_user_by_id(999)

        assert result is None

    def test_get_user_by_id_from_cache(self):
        """Test récupération utilisateur depuis le cache."""
        # Mettre en cache d'abord
        user_data = {"id": 1, "email": "test@example.com"}
        _model_cache.set("user_1", user_data)

        # Récupérer depuis le cache
        result = UserManager.get_user_by_id(1)

        assert result == user_data

    @patch("src.data.models.get_optimized_connection")
    def test_update_last_login(self, mock_get_connection):
        """Test mise à jour dernière connexion."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Mettre d'abord en cache
        _model_cache.set("user_1", {"id": 1, "email": "test@example.com"})

        UserManager.update_last_login(1)

        mock_cursor.execute.assert_called_once()
        # Vérifier que le cache est invalidé
        assert _model_cache.get("user_1") is None


class TestModelChoiceManager:
    """Tests pour ModelChoiceManager."""

    @patch("src.data.models.get_optimized_connection")
    def test_save_model_choice_new(self, mock_get_connection):
        """Test sauvegarde nouveau choix de modèle."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Pas de choix existant
        mock_cursor.fetchone.return_value = None

        ModelChoiceManager.save_model_choice(1, "GPT-4")

        # Vérifier INSERT OR REPLACE (une seule requête)
        assert mock_cursor.execute.call_count == 1

    @patch("src.data.models.get_optimized_connection")
    def test_save_model_choice_update(self, mock_get_connection):
        """Test mise à jour choix de modèle existant."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Choix existant
        mock_cursor.fetchone.return_value = (1,)

        ModelChoiceManager.save_model_choice(1, "Claude 3.5 Sonnet")

        # Vérifier INSERT OR REPLACE (une seule requête)
        assert mock_cursor.execute.call_count == 1

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_model_choice(self, mock_get_connection):
        """Test récupération choix de modèle utilisateur."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        mock_cursor.fetchone.return_value = ("GPT-4",)

        result = ModelChoiceManager.get_user_model_choice(1)

        assert result == "GPT-4"

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_model_choice_not_found(self, mock_get_connection):
        """Test récupération choix de modèle - non trouvé."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        mock_cursor.fetchone.return_value = None

        result = ModelChoiceManager.get_user_model_choice(999)

        assert result is None


class TestCampaignManager:
    """Tests pour CampaignManager."""

    @patch("src.data.models.get_optimized_connection")
    def test_create_campaign_success(self, mock_get_connection):
        """Test création campagne - succès."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 123
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        result = CampaignManager.create_campaign(
            user_id=1, name="Test Campaign", themes=["Fantasy", "Adventure"], language="FR"
        )

        assert result == 123
        mock_cursor.execute.assert_called_once()

    def test_create_campaign_missing_required_fields(self):
        """Test création campagne - champs requis manquants."""
        with pytest.raises(ValueError) as exc_info:
            CampaignManager.create_campaign(user_id=None, name="Test Campaign", themes=["Fantasy"], language="FR")

        assert "user_id, name et language sont requis" in str(exc_info.value)

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_campaigns(self, mock_get_connection):
        """Test récupération campagnes utilisateur."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Mock des résultats - tuples correspondant aux colonnes SQL
        # (id, name, themes, language, gm_portrait, created_at, updated_at, message_count, last_activity)
        mock_campaigns = [
            (
                1,
                "Campaign 1",
                '["Fantasy"]',
                "FR",
                None,
                "2024-01-01 00:00:00",
                "2024-01-01 00:00:00",
                5,
                "2024-01-01 12:00:00",
            ),
            (
                2,
                "Campaign 2",
                '["Sci-Fi"]',
                "EN",
                None,
                "2024-01-02 00:00:00",
                "2024-01-02 00:00:00",
                3,
                "2024-01-02 12:00:00",
            ),
        ]
        mock_cursor.fetchall.return_value = mock_campaigns

        result = CampaignManager.get_user_campaigns(1)

        assert len(result) == 2
        assert result[0]["name"] == "Campaign 1"


class TestCharacterManager:
    """Tests pour CharacterManager."""

    @patch("src.data.models.get_optimized_connection")
    def test_create_character_success(self, mock_get_connection):
        """Test création personnage - succès."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 456
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        result = CharacterManager.create_character(
            user_id=1,
            name="Test Character",
            char_class="Warrior",
            race="Human",
            description="Test Description",
            gender="Male",
            level=5,
        )

        assert result == 456
        mock_cursor.execute.assert_called_once()

    def test_create_character_missing_required_fields(self):
        """Test création personnage - champs requis manquants."""
        with pytest.raises(ValueError) as exc_info:
            CharacterManager.create_character(user_id=1, name="Test Character", char_class="", race="Human")  # Manquant

        assert "user_id, name, char_class et race sont requis" in str(exc_info.value)

    @patch("src.data.models.get_optimized_connection")
    def test_update_character_portrait_success(self, mock_get_connection):
        """Test mise à jour portrait personnage - succès."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1  # Une ligne affectée
        mock_cursor.fetchone.return_value = (1,)  # user_id pour la requête SELECT
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        result = CharacterManager.update_character_portrait(123, "http://example.com/portrait.jpg")

        assert result is True
        assert mock_cursor.execute.call_count == 2  # UPDATE puis SELECT

    @patch("src.data.models.get_optimized_connection")
    def test_update_character_portrait_not_found(self, mock_get_connection):
        """Test mise à jour portrait personnage - personnage non trouvé."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 0  # Aucune ligne affectée
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        result = CharacterManager.update_character_portrait(999, "http://example.com/portrait.jpg")

        assert result is False

    @patch("src.data.models.get_optimized_connection")
    def test_get_user_characters(self, mock_get_connection):
        """Test récupération personnages utilisateur."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_connection.return_value.__exit__ = Mock(return_value=None)

        # Mock des résultats - tuples correspondant aux colonnes SQL ACTUELLES
        # (id, campaign_id, name, class, race, gender, level, description, portrait_url, created_at)
        mock_characters = [
            (1, 10, "Character 1", "Warrior", "Human", "Male", 3, "Desc 1", None, "2024-01-01 00:00:00"),
            (2, 11, "Character 2", "Mage", "Elf", "Female", 2, "Desc 2", None, "2024-01-02 00:00:00"),
        ]
        mock_cursor.fetchall.return_value = mock_characters

        result = CharacterManager.get_user_characters(1)

        assert len(result) == 2
        assert result[0]["name"] == "Character 1"


if __name__ == "__main__":
    pytest.main([__file__])
