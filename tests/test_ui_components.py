"""
Tests pour les composants d'interface utilisateur
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.components.styles import apply_custom_css, configure_page


class TestUIComponents:
    """Tests pour les composants UI."""

    @patch('src.ui.components.styles.st')
    def test_apply_custom_css(self, mock_st):
        """Test d'application des styles CSS."""
        apply_custom_css()
        
        # Vérifier que st.markdown a été appelé avec du CSS
        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args
        
        # Vérifier que du CSS est présent
        css_content = call_args[0][0]
        assert "<style>" in css_content
        assert "</style>" in css_content
        assert "main-header" in css_content
        assert "character-card" in css_content
        assert "campaign-info" in css_content
        
        # Vérifier que unsafe_allow_html est True
        assert call_args[1]["unsafe_allow_html"] is True

    @patch('src.ui.components.styles.st')
    def test_configure_page(self, mock_st):
        """Test de configuration de la page."""
        configure_page()
        
        # Vérifier que set_page_config a été appelé
        mock_st.set_page_config.assert_called_once()
        call_args = mock_st.set_page_config.call_args
        
        # Vérifier les paramètres de configuration
        assert call_args[1]["page_title"] == "DnD AI GameMaster"
        assert call_args[1]["page_icon"] == "🎲"
        assert call_args[1]["layout"] == "wide"
        assert call_args[1]["initial_sidebar_state"] == "expanded"


class TestPageImports:
    """Tests pour vérifier que les pages peuvent être importées."""

    def test_import_auth_page(self):
        """Test d'import de la page d'authentification."""
        try:
            from src.ui.views.auth_page import show_auth_page, determine_user_next_page
            assert callable(show_auth_page)
            assert callable(determine_user_next_page)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_import_dashboard_page(self):
        """Test d'import de la page dashboard."""
        try:
            from src.ui.views.dashboard_page import show_dashboard_page
            assert callable(show_dashboard_page)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_import_chatbot_page(self):
        """Test d'import de la page chatbot."""
        try:
            from src.ui.views.chatbot_page import show_chatbot_page
            assert callable(show_chatbot_page)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_import_performance_page(self):
        """Test d'import de la page performance."""
        try:
            from src.ui.views.performance_page import show_performance_page
            assert callable(show_performance_page)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_import_settings_page(self):
        """Test d'import de la page settings."""
        try:
            from src.ui.views.settings_page import show_settings_page
            assert callable(show_settings_page)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestAuthPageFunctions:
    """Tests pour les fonctions de la page d'authentification."""

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_with_campaigns(self, mock_get_campaigns):
        """Test de détermination de page avec campagnes existantes."""
        from src.ui.views.auth_page import determine_user_next_page
        
        # Utilisateur avec campagnes
        mock_get_campaigns.return_value = [{"id": 1, "name": "Test Campaign"}]
        
        result = determine_user_next_page(123)
        assert result == "dashboard"

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_without_campaigns(self, mock_get_campaigns):
        """Test de détermination de page sans campagnes."""
        from src.ui.views.auth_page import determine_user_next_page
        
        # Utilisateur sans campagnes
        mock_get_campaigns.return_value = []
        
        result = determine_user_next_page(123)
        assert result == "campaign"

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_error(self, mock_get_campaigns):
        """Test de détermination de page en cas d'erreur."""
        from src.ui.views.auth_page import determine_user_next_page
        
        # Erreur lors de la récupération des campagnes
        mock_get_campaigns.side_effect = Exception("Database error")
        
        result = determine_user_next_page(123)
        assert result == "dashboard"  # Fallback


class TestAppRefactored:
    """Tests pour l'application refactorisée."""

    def test_import_app_refactored(self):
        """Test d'import de l'application refactorisée."""
        try:
            from src.ui.app import main, initialize_app
            assert callable(main)
            assert callable(initialize_app)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    @patch('src.ui.app.init_db')
    @patch('src.ui.app.logger')
    def test_initialize_app_success(self, mock_logger, mock_init_db):
        """Test d'initialisation réussie de l'application."""
        from src.ui.app import initialize_app
        
        initialize_app()
        
        mock_init_db.assert_called_once()
        mock_logger.info.assert_called_with("Application initialisée avec succès")

    @patch('src.ui.app.init_db')
    @patch('src.ui.app.st')
    @patch('src.ui.app.logger')
    def test_initialize_app_error(self, mock_logger, mock_st, mock_init_db):
        """Test d'initialisation avec erreur."""
        from src.ui.app import initialize_app
        
        mock_init_db.side_effect = Exception("Database error")
        # Configurer st.stop pour lever SystemExit comme Streamlit le fait réellement
        mock_st.stop.side_effect = SystemExit("Streamlit stop")
        
        with pytest.raises(SystemExit):  # st.stop() lève SystemExit
            initialize_app()
        
        mock_st.error.assert_called_once()
        mock_st.stop.assert_called_once()
        mock_logger.error.assert_called_once()


class TestModuleStructure:
    """Tests pour la structure des modules UI."""

    def test_ui_package_structure(self):
        """Test de la structure du package UI."""
        import src.ui
        import src.ui.components
        import src.ui.views
        
        # Vérifier que les packages peuvent être importés
        assert hasattr(src.ui, '__path__')
        assert hasattr(src.ui.components, '__path__')
        assert hasattr(src.ui.views, '__path__')

    def test_components_init_file(self):
        """Test du fichier __init__.py des composants."""
        try:
            from src.ui.components import __doc__
            assert isinstance(__doc__, str)
        except ImportError:
            pytest.fail("Components __init__.py not found")

    def test_pages_init_file(self):
        """Test du fichier __init__.py des pages."""
        try:
            from src.ui.views import __doc__
            assert isinstance(__doc__, str)
        except ImportError:
            pytest.fail("Pages __init__.py not found")

    def test_main_ui_init_file(self):
        """Test du fichier __init__.py principal UI."""
        try:
            from src.ui import __version__, __author__
            assert isinstance(__version__, str)
            assert isinstance(__author__, str)
        except (ImportError, AttributeError):
            pytest.fail("Main UI __init__.py not found or missing attributes")


class TestPageFunctionalities:
    """Tests fonctionnels pour les pages."""

    @patch('src.ui.views.dashboard_page.get_user_campaigns')
    @patch('src.ui.views.dashboard_page.require_auth')
    @patch('src.ui.views.dashboard_page.st')
    def test_dashboard_page_unauthorized(self, mock_st, mock_require_auth, mock_get_campaigns):
        """Test de la page dashboard sans autorisation."""
        from src.ui.views.dashboard_page import show_dashboard_page
        
        mock_require_auth.return_value = False
        
        show_dashboard_page()
        
        # Vérifier que require_auth a été appelé
        mock_require_auth.assert_called_once()
        # get_user_campaigns ne doit pas être appelé
        mock_get_campaigns.assert_not_called()

    @patch('src.ui.views.performance_page.require_auth')
    @patch('src.ui.views.performance_page.show_performance')
    @patch('src.ui.views.performance_page.st')
    def test_performance_page_authorized(self, mock_st, mock_show_performance, mock_require_auth):
        """Test de la page performance avec autorisation."""
        from src.ui.views.performance_page import show_performance_page
        
        mock_require_auth.return_value = True
        mock_st.session_state.user = {"id": 123}
        
        show_performance_page()
        
        mock_require_auth.assert_called_once()
        mock_show_performance.assert_called_once_with(123)

    @patch('src.ui.views.settings_page.require_auth')
    @patch('src.ui.views.settings_page.get_user_model_choice')
    @patch('src.ui.views.settings_page.st')
    def test_settings_page_load_model_choice(self, mock_st, mock_get_model_choice, mock_require_auth):
        """Test de chargement du choix de modèle dans les paramètres."""
        from src.ui.views.settings_page import show_settings_page
        
        mock_require_auth.return_value = True
        mock_st.session_state.user = {"id": 123}
        mock_get_model_choice.return_value = "Claude 3.5 Sonnet"
        
        # Mock des éléments Streamlit
        mock_st.selectbox.return_value = "Claude 3.5 Sonnet"
        mock_st.button.return_value = False
        # Configurer st.columns pour retourner le bon nombre d'objets mock selon l'appel
        from unittest.mock import MagicMock
        def mock_columns(spec):
            if isinstance(spec, list) and len(spec) == 2:
                return [MagicMock(), MagicMock()]
            elif spec == 3:
                return [MagicMock(), MagicMock(), MagicMock()]
            else:
                return [MagicMock(), MagicMock()]  # Défaut
        mock_st.columns.side_effect = mock_columns
        
        show_settings_page()
        
        mock_get_model_choice.assert_called_once_with(123)


if __name__ == "__main__":
    pytest.main([__file__])
