"""
Tests pour la configuration générale du projet
"""

import os
import sys

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestProjectStructure:
    """Tests pour la structure du projet."""

    def test_src_structure_exists(self):
        """Test que la structure src/ existe."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        expected_dirs = ["src", "src/ui", "src/auth", "src/ai", "src/data", "src/analytics", "src/core"]

        for dir_path in expected_dirs:
            full_path = os.path.join(project_root, dir_path)
            assert os.path.exists(full_path), f"Directory {dir_path} should exist"
            assert os.path.isdir(full_path), f"{dir_path} should be a directory"

    def test_main_modules_exist(self):
        """Test que les modules principaux existent."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        expected_files = [
            "src/ui/app.py",
            "src/auth/auth.py",
            "src/ai/chatbot.py",
            "src/ai/portraits.py",
            "src/data/database.py",
            "src/data/models.py",
            "src/analytics/performance.py",
            "src/core/config.py",
        ]

        for file_path in expected_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"File {file_path} should exist"
            assert os.path.isfile(full_path), f"{file_path} should be a file"

    def test_supporting_modules_exist(self):
        """Test que les modules de support existent."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        supporting_files = [
            "src/ai/api_client.py",
            "src/ai/models_config.py",
            "src/analytics/performance.py",
            "src/analytics/system_monitoring.py",
            "src/core/config.py",
        ]

        for file_path in supporting_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"Supporting file {file_path} should exist"

    def test_ui_components_exist(self):
        """Test que les composants UI existent."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        ui_files = [
            "src/ui/components/styles.py",
            "src/ui/views/auth_page.py",
            "src/ui/views/dashboard_page.py",
            "src/ui/views/chatbot_page.py",
            "src/ui/views/performance_page.py",
            "src/ui/views/settings_page.py",
            "src/ui/app.py",  # Version modulaire (ex-refactored)
        ]

        for file_path in ui_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"UI file {file_path} should exist"

    def test_test_files_exist(self):
        """Test que tous les fichiers de test existent."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        test_files = [
            "tests/conftest.py",
            "tests/test_app.py",
            "tests/test_auth.py",
            "tests/test_chatbot.py",
            "tests/test_ia.py",
            "tests/test_models.py",
            "tests/test_api_client.py",
            "tests/test_models_config.py",
            "tests/test_database.py",
            "tests/test_integration_ai.py",
            "tests/test_ui_components.py",
            "tests/test_config.py",
        ]

        for file_path in test_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"Test file {file_path} should exist"


class TestImportability:
    """Tests pour vérifier que tous les modules peuvent être importés."""

    def test_import_core_modules(self):
        """Test d'import des modules core."""
        try:
            from src.core import config
            from src.data import database, models
            from src.auth import auth
            from src.ai import chatbot, portraits
            from src.analytics import performance

            assert True  # Si on arrive ici, tous les imports ont réussi
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")

    def test_import_supporting_modules(self):
        """Test d'import des modules de support."""
        try:
            from src.ai import api_client, models_config
            from src.analytics import performance, system_monitoring
            from src.core import config

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import supporting modules: {e}")

    def test_import_ui_modules(self):
        """Test d'import des modules UI."""
        try:
            from src.ui import app
            from src.ui.components import styles
            from src.ui.views import auth_page, dashboard_page, chatbot_page

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import UI modules: {e}")


class TestConfiguration:
    """Tests pour la configuration du projet."""

    def test_requirements_file_exists(self):
        """Test que requirements.txt existe."""
        project_root = os.path.join(os.path.dirname(__file__), "..")
        requirements_path = os.path.join(project_root, "requirements", "requirements.txt")
        assert os.path.exists(requirements_path)

    def test_pyproject_config_exists(self):
        """Test que pyproject.toml existe."""
        project_root = os.path.join(os.path.dirname(__file__), "..")
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        assert os.path.exists(pyproject_path)

    def test_docker_files_exist(self):
        """Test que les fichiers Docker existent."""
        project_root = os.path.join(os.path.dirname(__file__), "..")

        docker_files = [("docker", "Dockerfile"), ("docker", "docker-compose.yml"), (".", ".dockerignore")]

        for folder, file_name in docker_files:
            file_path = os.path.join(project_root, folder, file_name)
            assert os.path.exists(file_path), f"Docker file {folder}/{file_name} should exist"

    def test_documentation_exists(self):
        """Test que la documentation existe."""
        project_root = os.path.join(os.path.dirname(__file__), "..")
        docs_dir = os.path.join(project_root, "docs")

        assert os.path.exists(docs_dir)
        assert os.path.isdir(docs_dir)

        # Vérifier quelques fichiers de documentation clés
        doc_files = ["README.md", "DEPLOYMENT_GUIDE.md", "TECHNICAL_GUIDE.md", "USER_GUIDE.md"]

        for doc_file in doc_files:
            doc_path = os.path.join(docs_dir, doc_file)
            assert os.path.exists(doc_path), f"Documentation {doc_file} should exist"


class TestModuleVersions:
    """Tests pour les versions des modules."""

    def test_src_package_version(self):
        """Test que le package src a une version."""
        try:
            from src import __version__

            assert isinstance(__version__, str)
            assert len(__version__) > 0
        except (ImportError, AttributeError):
            pytest.fail("src package should have a __version__ attribute")

    def test_src_package_author(self):
        """Test que le package src a un auteur."""
        try:
            from src import __author__

            assert isinstance(__author__, str)
            assert len(__author__) > 0
        except (ImportError, AttributeError):
            pytest.fail("src package should have an __author__ attribute")


class TestCodeQuality:
    """Tests pour la qualité du code."""

    def test_no_syntax_errors_in_main_modules(self):
        """Test qu'il n'y a pas d'erreurs de syntaxe dans les modules principaux."""
        import ast

        project_root = os.path.join(os.path.dirname(__file__), "..")

        python_files = ["src/ui/app.py", "src/auth/auth.py", "src/ai/chatbot.py", "src/data/database.py", "src/data/models.py"]

        for file_path in python_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {file_path}: {e}")

    def test_no_syntax_errors_in_optimized_modules(self):
        """Test qu'il n'y a pas d'erreurs de syntaxe dans les modules optimisés."""
        import ast

        project_root = os.path.join(os.path.dirname(__file__), "..")

        optimized_files = [
            "src/ai/api_client.py",
            "src/ai/models_config.py",
            "src/ai/chatbot_optimized.py",
            "src/auth/auth_optimized.py",
            "src/data/database_optimized.py",
            "src/data/models_optimized.py",
        ]

        for file_path in optimized_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {file_path}: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
