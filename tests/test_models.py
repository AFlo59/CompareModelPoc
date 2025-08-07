import os
import sys

import pytest

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import (
    create_campaign,
    create_character,
    get_campaign_messages,
    get_user_campaigns,
    get_user_characters,
    get_user_model_choice,
    save_model_choice,
)


class TestDatabaseModels:
    """Tests pour les modèles de base de données."""

    def test_save_model_choice(self, sample_user):
        """Test de sauvegarde du choix de modèle."""
        user_id = sample_user["id"]

        # Tester la sauvegarde du modèle
        save_model_choice(user_id, "GPT-4")

        # Vérifier la sauvegarde
        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT model FROM model_choices WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "GPT-4"

    def test_save_model_choice_invalid_params(self):
        """Test avec des paramètres invalides."""
        with pytest.raises(ValueError):
            save_model_choice(None, "GPT-4")

        with pytest.raises(ValueError):
            save_model_choice(1, "")

    def test_create_campaign(self, sample_user):
        """Test de création de campagne avec portrait MJ."""
        user_id = sample_user["id"]

        # Créer une campagne avec portrait MJ
        campaign_id = create_campaign(
            user_id, "Test Campaign", ["Fantasy", "Adventure"], "fr", "https://example.com/gm_portrait.jpg"
        )

        # Vérifier la création
        assert isinstance(campaign_id, int)
        assert campaign_id > 0

        # Vérifier en base
        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, themes, language, gm_portrait FROM campaigns WHERE id = ?", (campaign_id,))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "Test Campaign"
        assert "Fantasy" in result[1]
        assert result[2] == "fr"
        assert result[3] == "https://example.com/gm_portrait.jpg"

    def test_create_character(self, sample_user):
        """Test de création de personnage."""
        user_id = sample_user["id"]

        # Créer un personnage
        character_id = create_character(
            user_id, "Aragorn", "Rôdeur", "Humain", "Grand et sombre", "http://example.com/portrait.jpg"
        )

        # Vérifier la création
        assert isinstance(character_id, int)
        assert character_id > 0

        # Vérifier en base
        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT name, class, race, description, portrait_url 
                         FROM characters WHERE id = ?""",
            (character_id,),
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "Aragorn"
        assert result[1] == "Rôdeur"
        assert result[2] == "Humain"
        assert result[3] == "Grand et sombre"
        assert result[4] == "http://example.com/portrait.jpg"

    def test_get_user_campaigns(self, sample_user):
        """Test de récupération des campagnes utilisateur avec portraits."""
        user_id = sample_user["id"]

        # Créer plusieurs campagnes avec portraits
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr", "https://example.com/gm1.jpg")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en", "https://example.com/gm2.jpg")

        # Récupérer les campagnes
        campaigns = get_user_campaigns(user_id)

        # Vérifications
        assert len(campaigns) == 2
        assert campaigns[0]["name"] == "Campaign 2"  # Plus récent en premier
        assert campaigns[1]["name"] == "Campaign 1"
        assert campaigns[0]["themes"] == ["Sci-Fi"]
        assert campaigns[1]["themes"] == ["Fantasy"]
        assert campaigns[0]["gm_portrait"] == "https://example.com/gm2.jpg"
        assert campaigns[1]["gm_portrait"] == "https://example.com/gm1.jpg"
        assert "message_count" in campaigns[0]
        assert "last_activity" in campaigns[0]

    def test_get_user_characters(self, sample_user):
        """Test de récupération des personnages utilisateur."""
        user_id = sample_user["id"]

        # Créer plusieurs personnages
        char_id_1 = create_character(user_id, "Aragorn", "Rôdeur", "Humain")
        char_id_2 = create_character(user_id, "Legolas", "Archer", "Elfe")

        # Récupérer les personnages
        characters = get_user_characters(user_id)

        # Vérifications
        assert len(characters) == 2
        assert characters[0]["name"] == "Legolas"  # Plus récent en premier
        assert characters[1]["name"] == "Aragorn"

    def test_invalid_user_id(self):
        """Test avec ID utilisateur invalide."""
        with pytest.raises(ValueError):
            get_user_campaigns(None)

        with pytest.raises(ValueError):
            get_user_campaigns("")

    def test_create_campaign_invalid_params(self):
        """Test de création de campagne avec paramètres invalides."""
        with pytest.raises(ValueError):
            create_campaign(None, "Test", ["Fantasy"], "fr")

        with pytest.raises(ValueError):
            create_campaign(1, "", ["Fantasy"], "fr")

        with pytest.raises(ValueError):
            create_campaign(1, "Test", ["Fantasy"], "")

    def test_create_character_invalid_params(self):
        """Test de création de personnage avec paramètres invalides."""
        with pytest.raises(ValueError):
            create_character(None, "Test", "Guerrier", "Humain")

        with pytest.raises(ValueError):
            create_character(1, "", "Guerrier", "Humain")

        with pytest.raises(ValueError):
            create_character(1, "Test", "", "Humain")

        with pytest.raises(ValueError):
            create_character(1, "Test", "Guerrier", "")

    def test_get_user_model_choice(self, sample_user):
        """Test de récupération du choix de modèle utilisateur."""
        user_id = sample_user["id"]

        # Aucun modèle sauvegardé
        result = get_user_model_choice(user_id)
        assert result is None

        # Sauvegarder un modèle
        save_model_choice(user_id, "Claude 3.5 Sonnet")

        # Vérifier la récupération
        result = get_user_model_choice(user_id)
        assert result == "Claude 3.5 Sonnet"

    def test_get_campaign_messages(self, sample_user):
        """Test de récupération des messages par campagne."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en")

        # Ajouter des messages à la première campagne
        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, campaign_id) VALUES (?, ?, ?, ?)",
            (user_id, "user", "Bonjour", campaign_id_1),
        )
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, campaign_id) VALUES (?, ?, ?, ?)",
            (user_id, "assistant", "Salut !", campaign_id_1),
        )

        # Ajouter un message à la deuxième campagne
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, campaign_id) VALUES (?, ?, ?, ?)",
            (user_id, "user", "Hello", campaign_id_2),
        )
        conn.commit()
        conn.close()

        # Récupérer les messages de la première campagne
        messages_1 = get_campaign_messages(user_id, campaign_id_1)
        assert len(messages_1) == 2
        assert messages_1[0]["content"] == "Bonjour"
        assert messages_1[1]["content"] == "Salut !"

        # Récupérer les messages de la deuxième campagne
        messages_2 = get_campaign_messages(user_id, campaign_id_2)
        assert len(messages_2) == 1
        assert messages_2[0]["content"] == "Hello"

    def test_get_campaign_messages_no_campaign(self, sample_user):
        """Test de récupération des messages sans campagne spécifiée."""
        user_id = sample_user["id"]

        # Aucune campagne existante
        messages = get_campaign_messages(user_id)
        assert messages == []

        # Créer une campagne et des messages
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, campaign_id) VALUES (?, ?, ?, ?)",
            (user_id, "user", "Test message", campaign_id),
        )
        conn.commit()
        conn.close()

        # Récupérer sans spécifier la campagne (doit prendre la plus récente)
        messages = get_campaign_messages(user_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"

    def test_campaign_with_no_portrait(self, sample_user):
        """Test de création de campagne sans portrait."""
        user_id = sample_user["id"]

        # Créer une campagne sans portrait
        campaign_id = create_campaign(user_id, "No Portrait Campaign", ["Fantasy"], "fr")

        # Récupérer et vérifier
        campaigns = get_user_campaigns(user_id)
        assert len(campaigns) == 1
        assert campaigns[0]["gm_portrait"] is None


if __name__ == "__main__":
    pytest.main([__file__])
