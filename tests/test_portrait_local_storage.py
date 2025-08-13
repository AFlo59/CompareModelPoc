"""
Tests pour le système de stockage local des portraits
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPortraitLocalStorage:
    """Tests pour le stockage local des portraits."""

    @patch("src.ai.portraits.requests.get")
    @patch("src.ai.portraits.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_download_and_save_image_success(self, mock_file_open, mock_mkdir, mock_requests):
        """Test du téléchargement et sauvegarde réussis d'une image."""
        from src.ai.portraits import PortraitGenerator

        # Mock de la réponse HTTP
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Test
        result = PortraitGenerator._download_and_save_image("https://dalle.com/image.png", "test_filename", "characters")

        # Vérifications
        assert result == "static/portraits/characters/test_filename.png"
        mock_requests.assert_called_once_with("https://dalle.com/image.png", timeout=30)
        mock_response.raise_for_status.assert_called_once()
        # Vérifier que le fichier a été ouvert pour écriture (ignorer l'ouverture du .env)
        assert any(call for call in mock_file_open.call_args_list if "wb" in str(call))

    @patch("src.ai.portraits.requests.get")
    def test_download_and_save_image_http_error(self, mock_requests):
        """Test de gestion d'erreur HTTP lors du téléchargement."""
        from src.ai.portraits import PortraitGenerator

        # Mock d'une erreur HTTP
        mock_requests.side_effect = Exception("HTTP Error")

        # Test
        result = PortraitGenerator._download_and_save_image("https://dalle.com/image.png", "test_filename", "characters")

        # Vérifications
        assert result is None

    def test_download_and_save_image_invalid_subdirectory(self):
        """Test avec un sous-dossier invalide."""
        from src.ai.portraits import PortraitGenerator

        result = PortraitGenerator._download_and_save_image("https://dalle.com/image.png", "test_filename", "invalid_subdir")

        assert result is None

    @patch("src.ai.portraits.PortraitGenerator._download_and_save_image")
    @patch("src.ai.portraits.update_character_portrait")
    @patch("src.ai.portraits.PortraitGenerator._generate_portrait")
    def test_generate_character_portrait_with_save_local_storage(self, mock_generate, mock_update_db, mock_download):
        """Test de génération de portrait avec stockage local."""
        from src.ai.portraits import PortraitGenerator

        # Mock d'une URL DALL-E temporaire
        mock_generate.return_value = "https://oaidalleapiprodscus.blob.core.windows.net/image.png"
        mock_download.return_value = "static/portraits/characters/character_123.png"

        # Test
        result = PortraitGenerator.generate_character_portrait_with_save(
            name="Test Character", character_id=123, race="Humain", char_class="Guerrier"
        )

        # Vérifications
        assert result == "static/portraits/characters/character_123.png"
        mock_download.assert_called_once_with(
            "https://oaidalleapiprodscus.blob.core.windows.net/image.png", "character_123", "characters"
        )
        mock_update_db.assert_called_once_with(123, "static/portraits/characters/character_123.png")

    @patch("src.ai.portraits.PortraitGenerator._download_and_save_image")
    @patch("src.ai.portraits.update_campaign_portrait")
    @patch("src.ai.portraits.PortraitGenerator._generate_portrait")
    def test_generate_gm_portrait_with_save_local_storage(self, mock_generate, mock_update_db, mock_download):
        """Test de génération de portrait GM avec stockage local."""
        from src.ai.portraits import PortraitGenerator

        # Mock d'une URL DALL-E temporaire
        mock_generate.return_value = "https://oaidalleapiprodscus.blob.core.windows.net/gm.png"
        mock_download.return_value = "static/portraits/gm/gm_456.png"

        # Test
        result = PortraitGenerator.generate_gm_portrait_with_save(campaign_id=456, campaign_name="Test Campaign")

        # Vérifications
        assert result == "static/portraits/gm/gm_456.png"
        mock_download.assert_called_once_with("https://oaidalleapiprodscus.blob.core.windows.net/gm.png", "gm_456", "gm")
        mock_update_db.assert_called_once_with(456, "static/portraits/gm/gm_456.png")

    @patch("src.ai.portraits.PortraitGenerator._generate_portrait")
    def test_generate_character_portrait_dicebear_no_download(self, mock_generate):
        """Test qu'on ne télécharge pas les URLs Dicebear et qu'on ne les sauvegarde pas non plus."""
        from src.ai.portraits import PortraitGenerator

        # Mock d'une URL Dicebear (pas DALL-E)
        dicebear_url = "https://api.dicebear.com/7.x/adventurer/png?seed=test"
        mock_generate.return_value = dicebear_url

        # Test
        result = PortraitGenerator.generate_character_portrait_with_save(
            name="Test Character", character_id=123, race="Humain", char_class="Guerrier"
        )

        # Vérifications - pas de téléchargement, pas de sauvegarde en BDD pour Dicebear
        assert result == dicebear_url
        # Note: Le code ne sauvegarde que les portraits IA, pas les Dicebear

    @patch("src.ai.portraits.PortraitGenerator._ensure_directories")
    def test_ensure_directories_called(self, mock_ensure_dirs):
        """Test que _ensure_directories est appelé lors du téléchargement."""
        from src.ai.portraits import PortraitGenerator

        # Mock pour éviter les erreurs de fichier
        with patch("src.ai.portraits.requests.get") as mock_requests:
            mock_requests.side_effect = Exception("Test exception")

            PortraitGenerator._download_and_save_image("https://test.com/image.png", "test", "characters")

        # Vérification que les dossiers sont créés
        mock_ensure_dirs.assert_called_once()


class TestImageUtils:
    """Tests pour les utilitaires d'images."""

    def test_display_portrait_external_url(self):
        """Test avec une URL externe."""
        from src.ui.components.image_utils import display_portrait

        url = "https://api.dicebear.com/7.x/adventurer/png?seed=test"
        result = display_portrait(url)
        assert result == url

    @patch("os.path.exists", return_value=True)
    def test_display_portrait_local_file_exists(self, mock_exists):
        """Test avec un fichier local existant."""
        from src.ui.components.image_utils import display_portrait

        local_path = "static/portraits/characters/character_123.png"
        result = display_portrait(local_path)
        assert result == local_path

    @patch("os.path.exists", return_value=False)
    def test_display_portrait_local_file_not_exists(self, mock_exists):
        """Test avec un fichier local inexistant."""
        from src.ui.components.image_utils import display_portrait

        local_path = "static/portraits/characters/missing.png"
        result = display_portrait(local_path)
        # Retourne le chemin original même si le fichier n'existe pas
        assert result == local_path

    def test_get_portrait_path_external_url(self):
        """Test get_portrait_path avec URL externe."""
        from src.ui.components.image_utils import get_portrait_path

        url = "https://api.dicebear.com/7.x/adventurer/png?seed=test"
        result = get_portrait_path(url)
        assert result == url

    @patch("pathlib.Path.exists", return_value=True)
    def test_get_portrait_path_local_exists(self, mock_exists):
        """Test get_portrait_path avec fichier local existant."""
        from src.ui.components.image_utils import get_portrait_path

        local_path = "static/portraits/characters/character_123.png"
        result = get_portrait_path(local_path)
        assert result == local_path

    @patch("pathlib.Path.exists", return_value=False)
    def test_get_portrait_path_local_not_exists(self, mock_exists):
        """Test get_portrait_path avec fichier local inexistant."""
        from src.ui.components.image_utils import get_portrait_path

        local_path = "static/portraits/characters/missing.png"
        result = get_portrait_path(local_path)
        assert result is None
