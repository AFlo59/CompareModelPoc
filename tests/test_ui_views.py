"""
Tests pour les vues UI - pages Streamlit
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.views.auth_page import show_auth_page, determine_user_next_page
from src.ui.views.dashboard_page import show_dashboard_page
from src.ui.views.settings_page import show_settings_page
from src.ui.views.performance_page import show_performance_page


class TestAuthPage:
    """Tests pour la page d'authentification."""

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_with_campaigns(self, mock_get_campaigns):
        """Test redirection - utilisateur avec campagnes."""
        mock_get_campaigns.return_value = [{'id': 1, 'name': 'Campaign 1'}]
        
        result = determine_user_next_page(1)
        
        assert result == "dashboard"
        mock_get_campaigns.assert_called_once_with(1)

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_no_campaigns(self, mock_get_campaigns):
        """Test redirection - utilisateur sans campagnes."""
        mock_get_campaigns.return_value = []
        
        result = determine_user_next_page(1)
        
        assert result == "campaign"  # Pas de campagnes -> redirection vers création de campagne
        mock_get_campaigns.assert_called_once_with(1)

    @patch('src.ui.views.auth_page.get_user_campaigns')
    def test_determine_user_next_page_error(self, mock_get_campaigns):
        """Test redirection - erreur lors du chargement."""
        mock_get_campaigns.side_effect = Exception("Database error")
        
        result = determine_user_next_page(1)
        
        assert result == "dashboard"

    @patch('streamlit.rerun')
    @patch('src.ui.views.auth_page.determine_user_next_page')
    def test_show_auth_page_already_logged_in(self, mock_determine, mock_rerun):
        """Test page auth - utilisateur déjà connecté."""
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_session_state.__contains__ = Mock(return_value=True)  # Pour "user" in session_state
        mock_determine.return_value = 'dashboard'
        
        with patch('streamlit.session_state', mock_session_state):
            show_auth_page()
        
        mock_determine.assert_called_once_with(1)
        assert mock_session_state.page == 'dashboard'
        mock_rerun.assert_called_once()

    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.radio')
    @patch('src.ui.views.auth_page.login')
    def test_show_auth_page_login_success(self, mock_login, mock_radio, mock_columns, mock_markdown):
        """Test page auth - connexion réussie."""
        # Setup session_state
        mock_session_state = Mock()
        mock_session_state.__contains__ = Mock(return_value=False)  # Pas d'utilisateur connecté
        mock_radio.return_value = "🔑 Connexion"
        mock_login.return_value = {'id': 1, 'email': 'test@example.com'}
        
        # Mock des colonnes
        mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun, \
             patch('src.ui.views.auth_page.determine_user_next_page') as mock_determine, \
             patch('time.sleep') as mock_sleep:
            
            mock_determine.return_value = 'dashboard'
            
            show_auth_page()
            
            mock_login.assert_called_once()
            mock_success.assert_called()
            assert mock_session_state.user == {'id': 1, 'email': 'test@example.com'}

    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.radio')
    @patch('src.ui.views.auth_page.register_user')
    def test_show_auth_page_register(self, mock_register, mock_radio, mock_columns, 
                                    mock_markdown, mock_session_state):
        """Test page auth - inscription."""
        mock_session_state.clear()
        mock_radio.return_value = "🆕 Créer un compte"
        
        # Mock des colonnes
        mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        show_auth_page()
        
        mock_register.assert_called_once()


class TestDashboardPage:
    """Tests pour la page de tableau de bord."""

    @patch('streamlit.session_state', new_callable=dict)
    @patch('src.ui.views.dashboard_page.require_auth')
    def test_show_dashboard_page_not_authenticated(self, mock_require_auth, mock_session_state):
        """Test dashboard - utilisateur non authentifié."""
        mock_require_auth.return_value = False
        
        show_dashboard_page()
        
        mock_require_auth.assert_called_once()

    @patch('src.ui.views.dashboard_page.require_auth')
    @patch('src.ui.views.dashboard_page.get_user_campaigns')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    def test_show_dashboard_page_success(self, mock_metric, mock_columns, mock_markdown, 
                                        mock_title, mock_get_campaigns, mock_require_auth):
        """Test dashboard - succès."""
        # Setup
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_get_campaigns.return_value = [
            {'id': 1, 'name': 'Campaign 1', 'message_count': 5, 'language': 'FR', 'themes': ['Fantasy']},
            {'id': 2, 'name': 'Campaign 2', 'message_count': 3, 'language': 'EN', 'themes': ['Sci-Fi']}
        ]
        
        # Mock des colonnes - retourner le bon nombre selon l'appel
        mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
        def mock_columns_side_effect(n):
            if n == 2:
                return [mock_col1, mock_col2]
            elif n == 3:
                return [mock_col1, mock_col2, mock_col3]
            else:
                return [mock_col1, mock_col2]
        mock_columns.side_effect = mock_columns_side_effect
        for col in [mock_col1, mock_col2, mock_col3]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.divider') as mock_divider, \
             patch('streamlit.button') as mock_button:
            
            mock_button.return_value = False  # Aucun bouton cliqué
            
            show_dashboard_page()
            
            mock_require_auth.assert_called_once()
            mock_get_campaigns.assert_called_once_with(1)
            mock_title.assert_called_once()
            assert mock_metric.call_count >= 3

    @patch('src.ui.views.dashboard_page.require_auth')
    @patch('src.ui.views.dashboard_page.get_user_campaigns')
    @patch('streamlit.title')
    @patch('streamlit.error')
    def test_show_dashboard_page_campaigns_error(self, mock_error, mock_title, mock_get_campaigns, mock_require_auth):
        """Test dashboard - erreur chargement campagnes."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_session_state.__contains__ = Mock(return_value=True)  # Pour "user" in session_state
        mock_session_state.__delitem__ = Mock()  # Pour del session_state[key]
        mock_session_state.keys = Mock(return_value=['user', 'page'])
        mock_get_campaigns.side_effect = Exception("Database error")
        
        # Mock st.columns avec le bon nombre de colonnes selon l'argument
        def create_mock_col():
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return mock_col
        
        def mock_columns_side_effect(n):
            if n == 2:
                return [create_mock_col(), create_mock_col()]
            elif n == 3:
                return [create_mock_col(), create_mock_col(), create_mock_col()]
            else:
                return [create_mock_col() for _ in range(n)]
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.markdown'), \
             patch('streamlit.columns', side_effect=mock_columns_side_effect), \
             patch('streamlit.metric'), \
             patch('streamlit.divider'), \
             patch('streamlit.button'):
            
            show_dashboard_page()
            
            mock_error.assert_called_once()

    @patch('src.ui.views.dashboard_page.require_auth')
    @patch('src.ui.views.dashboard_page.get_user_campaigns')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_show_dashboard_page_new_campaign_button(self, mock_rerun, mock_button, 
                                                    mock_get_campaigns, mock_require_auth):
        """Test dashboard - bouton nouvelle campagne."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_get_campaigns.return_value = []
        
        # Mock des boutons - nouveau campagne cliqué
        def button_side_effect(text, **kwargs):
            return "🆕 Créer une nouvelle campagne" in text
        
        mock_button.side_effect = button_side_effect
        
        # Mock st.columns avec le bon nombre de colonnes selon l'argument
        def create_mock_col():
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return mock_col
        
        def mock_columns_side_effect(n):
            if n == 2:
                return [create_mock_col(), create_mock_col()]
            elif n == 3:
                return [create_mock_col(), create_mock_col(), create_mock_col()]
            else:
                return [create_mock_col() for _ in range(n)]
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.title'), \
             patch('streamlit.markdown'), \
             patch('streamlit.columns', side_effect=mock_columns_side_effect), \
             patch('streamlit.metric'), \
             patch('streamlit.divider'):
            
            show_dashboard_page()
            
            assert mock_session_state.page == 'campaign'
            mock_rerun.assert_called_once()

    @patch('src.ui.views.dashboard_page.require_auth')
    @patch('src.ui.views.dashboard_page.get_user_campaigns')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_quick_campaign_buttons(self, mock_rerun, mock_button, mock_get_campaigns, mock_require_auth):
        from src.ui.views.dashboard_page import show_dashboard_page

        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        # Deux campagnes pour lister des boutons
        mock_get_campaigns.return_value = [
            {'id': 1, 'name': 'Campaign 1', 'message_count': 5, 'language': 'FR', 'themes': ['Fantasy']},
            {'id': 2, 'name': 'Campaign 2', 'message_count': 3, 'language': 'EN', 'themes': ['Sci-Fi']}
        ]

        # Simuler un clic sur le premier bouton quick_camp_0
        def button_side_effect(text, **kwargs):
            return text.startswith('🏰 Campaign 1')
        mock_button.side_effect = button_side_effect

        def create_mock_col():
            c = Mock()
            c.__enter__ = Mock(return_value=c)
            c.__exit__ = Mock(return_value=None)
            return c
        def mock_columns_side_effect(n):
            return [create_mock_col() for _ in range(3 if n == 3 else 2)]

        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.title'), \
             patch('streamlit.markdown'), \
             patch('streamlit.columns', side_effect=mock_columns_side_effect), \
             patch('streamlit.metric'), \
             patch('streamlit.divider'):
            show_dashboard_page()

        # Doit avoir redirigé vers chatbot et effectué un rerun
        assert mock_session_state.page == 'chatbot'
        mock_rerun.assert_called()


class TestSettingsPage:
    """Tests pour la page des paramètres."""

    @patch('streamlit.session_state', new_callable=dict)
    @patch('src.ui.views.settings_page.require_auth')
    def test_show_settings_page_not_authenticated(self, mock_require_auth, mock_session_state):
        """Test settings - utilisateur non authentifié."""
        mock_require_auth.return_value = False
        
        show_settings_page()
        
        mock_require_auth.assert_called_once()

    @patch('src.ui.views.settings_page.require_auth')
    @patch('src.ui.views.settings_page.get_user_campaigns')
    @patch('streamlit.title')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    def test_show_settings_page_success(self, mock_button, mock_columns, mock_title, 
                                       mock_get_campaigns, mock_require_auth):
        """Test settings - succès."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_get_campaigns.return_value = [{'id': 1, 'name': 'Campaign 1', 'message_count': 5}]
        mock_button.return_value = False
        
        # Mock st.columns avec le bon nombre selon l'argument (settings page utilise [3, 1] et 3)
        def create_mock_col():
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return mock_col
            
        def mock_columns_side_effect(spec):
            if isinstance(spec, list) and len(spec) == 2:  # [3, 1]
                return [create_mock_col(), create_mock_col()]
            elif spec == 3:  # 3 colonnes
                return [create_mock_col(), create_mock_col(), create_mock_col()]
            else:
                count = spec if isinstance(spec, int) else len(spec)
                return [create_mock_col() for _ in range(count)]
        
        mock_columns.side_effect = mock_columns_side_effect
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.divider'), \
             patch('streamlit.markdown'), \
             patch('streamlit.info'), \
             patch('streamlit.metric'):
            
            show_settings_page()
            
            mock_require_auth.assert_called_once()
            mock_get_campaigns.assert_called_once_with(1)

    @patch('src.ui.views.settings_page.require_auth')
    @patch('src.ui.views.settings_page.get_user_campaigns')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_show_settings_page_back_button(self, mock_rerun, mock_button, mock_get_campaigns, mock_require_auth):
        """Test settings - bouton retour."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_get_campaigns.return_value = []
        
        # Mock bouton retour cliqué
        def button_side_effect(text, **kwargs):
            return "🏠 Retour au tableau de bord" in text
        
        mock_button.side_effect = button_side_effect
        
        # Mock st.columns avec le bon nombre selon l'argument
        def create_mock_col():
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return mock_col
            
        def mock_columns_side_effect(spec):
            if isinstance(spec, list) and len(spec) == 2:  # [3, 1]
                return [create_mock_col(), create_mock_col()]
            elif spec == 3:  # 3 colonnes
                return [create_mock_col(), create_mock_col(), create_mock_col()]
            else:
                count = spec if isinstance(spec, int) else len(spec)
                return [create_mock_col() for _ in range(count)]
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.title'), \
             patch('streamlit.columns', side_effect=mock_columns_side_effect), \
             patch('streamlit.divider'), \
             patch('streamlit.markdown'), \
             patch('streamlit.warning'), \
             patch('streamlit.metric'):
            
            show_settings_page()
            
            assert mock_session_state.page == 'dashboard'
            mock_rerun.assert_called_once()

    @patch('src.ui.views.settings_page.require_auth')
    @patch('src.ui.views.settings_page.get_user_campaigns')
    @patch('streamlit.warning')
    def test_show_settings_page_campaigns_error(self, mock_warning, mock_get_campaigns, mock_require_auth):
        """Test settings - erreur chargement campagnes."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_get_campaigns.side_effect = Exception("Database error")
        
        # Mock st.columns avec le bon nombre selon l'argument
        def create_mock_col():
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return mock_col
            
        def mock_columns_side_effect(spec):
            if isinstance(spec, list) and len(spec) == 2:  # [3, 1]
                return [create_mock_col(), create_mock_col()]
            elif spec == 3:  # 3 colonnes
                return [create_mock_col(), create_mock_col(), create_mock_col()]
            else:
                count = spec if isinstance(spec, int) else len(spec)
                return [create_mock_col() for _ in range(count)]
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.title'), \
             patch('streamlit.columns', side_effect=mock_columns_side_effect), \
             patch('streamlit.button'), \
             patch('streamlit.divider'), \
             patch('streamlit.markdown'), \
             patch('streamlit.info'), \
             patch('streamlit.metric'):
            
            show_settings_page()
            
            # La fonction appelle warning 2 fois (erreur + conseil)
            assert mock_warning.call_count == 2
            # Vérifier que l'erreur est dans l'un des appels
            call_args_list = [str(call) for call in mock_warning.call_args_list]
            assert any("Erreur lors du chargement des statistiques" in call for call in call_args_list)


class TestPerformancePage:
    """Tests pour la page de performance."""

    @patch('streamlit.session_state', new_callable=dict)
    @patch('src.ui.views.performance_page.require_auth')
    def test_show_performance_page_not_authenticated(self, mock_require_auth, mock_session_state):
        """Test performance - utilisateur non authentifié."""
        mock_require_auth.return_value = False
        
        show_performance_page()
        
        mock_require_auth.assert_called_once()

    @patch('src.ui.views.performance_page.require_auth')
    @patch('src.analytics.performance.show_performance')
    @patch('streamlit.button')
    def test_show_performance_page_success(self, mock_button, mock_show_performance, mock_require_auth):
        """Test performance - succès."""
        mock_require_auth.return_value = True
        mock_session_state = Mock()
        mock_session_state.user = {'id': 1, 'email': 'test@example.com'}
        mock_button.return_value = False  # Aucun bouton cliqué
        
        with patch('streamlit.session_state', mock_session_state), \
             patch('streamlit.divider'):
            show_performance_page()
        
        mock_require_auth.assert_called_once()
        mock_show_performance.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__])
