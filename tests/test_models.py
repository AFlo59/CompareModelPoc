import os
import sys

import pytest

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import (
    create_campaign,
    create_character,
    get_campaign_character,
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

    def test_create_character_with_campaign(self, sample_user):
        """Test de création de personnage lié à une campagne."""
        user_id = sample_user["id"]

        # Créer une campagne d'abord
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Créer un personnage lié à cette campagne
        character_id = create_character(
            user_id, campaign_id, "Aragorn", "Rôdeur", "Humain", "Grand et sombre", "http://example.com/portrait.jpg"
        )

        # Vérifier la création
        assert isinstance(character_id, int)
        assert character_id > 0

        # Vérifier en base que le campaign_id est bien enregistré
        from database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT name, class, race, description, portrait_url, campaign_id 
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
        assert result[5] == campaign_id  # Vérifier la liaison campaign_id

    def test_create_character(self, sample_user):
        """Test de création de personnage (ancien comportement pour compatibilité)."""
        user_id = sample_user["id"]

        # Créer une campagne d'abord
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Créer un personnage avec le nouveau format (campaign_id requis)
        character_id = create_character(
            user_id, campaign_id, "Aragorn", "Rôdeur", "Humain", "Grand et sombre", "http://example.com/portrait.jpg"
        )

        # Vérifier la création
        assert isinstance(character_id, int)
        assert character_id > 0

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

    def test_get_user_characters_with_campaigns(self, sample_user):
        """Test de récupération des personnages utilisateur avec campaign_id."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en")

        # Créer des personnages pour chaque campagne
        char_id_1 = create_character(user_id, campaign_id_1, "Aragorn", "Rôdeur", "Humain")
        char_id_2 = create_character(user_id, campaign_id_2, "Spock", "Scientifique", "Vulcain")

        # Récupérer les personnages
        characters = get_user_characters(user_id)

        # Vérifications
        assert len(characters) == 2
        assert characters[0]["name"] == "Spock"  # Plus récent en premier
        assert characters[1]["name"] == "Aragorn"
        assert characters[0]["campaign_id"] == campaign_id_2
        assert characters[1]["campaign_id"] == campaign_id_1

    def test_get_user_characters(self, sample_user):
        """Test de récupération des personnages utilisateur."""
        user_id = sample_user["id"]

        # Créer une campagne d'abord
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Créer plusieurs personnages pour cette campagne
        char_id_1 = create_character(user_id, campaign_id, "Aragorn", "Rôdeur", "Humain")
        char_id_2 = create_character(user_id, campaign_id, "Legolas", "Archer", "Elfe")

        # Récupérer les personnages
        characters = get_user_characters(user_id)

        # Vérifications
        assert len(characters) == 2
        assert characters[0]["name"] == "Legolas"  # Plus récent en premier
        assert characters[1]["name"] == "Aragorn"
        assert all(char["campaign_id"] == campaign_id for char in characters)

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
        # Créer une campagne valide pour les tests
        from database import get_connection
        import bcrypt
        
        # Créer un utilisateur temporaire
        conn = get_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw("testpass".encode("utf-8"), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("temp@test.com", hashed_password))
        temp_user_id = cursor.lastrowid
        conn.commit()
        
        # Créer une campagne valide
        valid_campaign_id = create_campaign(temp_user_id, "Valid Campaign", ["Fantasy"], "fr")
        
        # Tests avec paramètres invalides
        with pytest.raises(ValueError):
            create_character(None, valid_campaign_id, "Test", "Guerrier", "Humain")

        with pytest.raises(ValueError):
            create_character(temp_user_id, None, "Test", "Guerrier", "Humain")

        with pytest.raises(ValueError):
            create_character(temp_user_id, valid_campaign_id, "", "Guerrier", "Humain")

        with pytest.raises(ValueError):
            create_character(temp_user_id, valid_campaign_id, "Test", "", "Humain")

        with pytest.raises(ValueError):
            create_character(temp_user_id, valid_campaign_id, "Test", "Guerrier", "")

        # Test avec campaign_id inexistant
        with pytest.raises(ValueError, match="La campagne spécifiée n'appartient pas à cet utilisateur"):
            create_character(temp_user_id, 99999, "Test", "Guerrier", "Humain")
            
        # Nettoyer
        cursor.execute("DELETE FROM campaigns WHERE id = ?", (valid_campaign_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (temp_user_id,))
        conn.commit()
        conn.close()

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


class TestCampaignCharacterLinking:
    """Tests spécifiques pour la liaison personnage-campagne."""

    def test_get_campaign_character(self, sample_user):
        """Test de récupération du personnage associé à une campagne."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en")

        # Créer un personnage pour la première campagne
        char_id_1 = create_character(user_id, campaign_id_1, "Aragorn", "Rôdeur", "Humain", "Grand et sombre")

        # Récupérer le personnage de la première campagne
        character = get_campaign_character(user_id, campaign_id_1)
        assert character is not None
        assert character["name"] == "Aragorn"
        assert character["class"] == "Rôdeur"
        assert character["race"] == "Humain"
        assert character["campaign_id"] == campaign_id_1

        # Vérifier qu'aucun personnage n'existe pour la deuxième campagne
        character_2 = get_campaign_character(user_id, campaign_id_2)
        assert character_2 is None

    def test_character_unique_to_campaign(self, sample_user):
        """Test que chaque personnage est unique à sa campagne."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Fantasy Campaign", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Sci-Fi Campaign", ["Sci-Fi"], "en")

        # Créer un personnage pour chaque campagne
        char_id_1 = create_character(user_id, campaign_id_1, "Gandalf", "Magicien", "Humain")
        char_id_2 = create_character(user_id, campaign_id_2, "Spock", "Scientifique", "Vulcain")

        # Vérifier que chaque campagne a son propre personnage
        char_campaign_1 = get_campaign_character(user_id, campaign_id_1)
        char_campaign_2 = get_campaign_character(user_id, campaign_id_2)

        assert char_campaign_1["name"] == "Gandalf"
        assert char_campaign_1["campaign_id"] == campaign_id_1
        
        assert char_campaign_2["name"] == "Spock"
        assert char_campaign_2["campaign_id"] == campaign_id_2

        # Vérifier que les personnages sont différents
        assert char_campaign_1["id"] != char_campaign_2["id"]

    def test_create_character_invalid_campaign(self, sample_user):
        """Test de création de personnage avec une campagne invalide."""
        user_id = sample_user["id"]

        # Tenter de créer un personnage avec un campaign_id inexistant
        with pytest.raises(ValueError, match="La campagne spécifiée n'appartient pas à cet utilisateur"):
            create_character(user_id, 999999, "Test", "Guerrier", "Humain")

    def test_create_character_wrong_user(self, sample_user):
        """Test de création de personnage avec un mauvais utilisateur."""
        user_id = sample_user["id"]
        
        # Créer une campagne
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Tenter de créer un personnage avec un autre user_id
        with pytest.raises(ValueError, match="La campagne spécifiée n'appartient pas à cet utilisateur"):
            create_character(888888, campaign_id, "Test", "Guerrier", "Humain")

    def test_multiple_characters_same_campaign(self, sample_user):
        """Test de création de plusieurs personnages pour la même campagne."""
        user_id = sample_user["id"]

        # Créer une campagne
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Créer deux personnages pour la même campagne
        char_id_1 = create_character(user_id, campaign_id, "Aragorn", "Rôdeur", "Humain")
        char_id_2 = create_character(user_id, campaign_id, "Legolas", "Archer", "Elfe")

        # get_campaign_character devrait retourner le plus récent (Legolas)
        character = get_campaign_character(user_id, campaign_id)
        assert character["name"] == "Legolas"  # Le plus récent

        # Vérifier que les deux personnages existent en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM characters WHERE campaign_id = ?", (campaign_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2  # Deux personnages pour cette campagne

    def test_get_campaign_character_invalid_params(self):
        """Test de get_campaign_character avec paramètres invalides."""
        # Test avec user_id None
        result = get_campaign_character(None, 1)
        assert result is None

        # Test avec campaign_id None
        result = get_campaign_character(1, None)
        assert result is None

        # Test avec les deux None
        result = get_campaign_character(None, None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])


class TestCampaignCharacterLinking:
    """Tests spécifiques pour la liaison personnage-campagne."""

    def test_get_campaign_character_success(self, sample_user):
        """Test de récupération du personnage d'une campagne."""
        user_id = sample_user["id"]

        # Créer une campagne
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")

        # Créer un personnage pour cette campagne
        character_id = create_character(
            user_id, campaign_id, "Gandalf", "Magicien", "Humain", "Vieux sage", "http://example.com/gandalf.jpg"
        )

        # Récupérer le personnage de la campagne
        character = get_campaign_character(user_id, campaign_id)

        # Vérifications
        assert character is not None
        assert character["id"] == character_id
        assert character["name"] == "Gandalf"
        assert character["class"] == "Magicien"
        assert character["race"] == "Humain"
        assert character["description"] == "Vieux sage"
        assert character["portrait_url"] == "http://example.com/gandalf.jpg"
        assert character["campaign_id"] == campaign_id

    def test_get_campaign_character_no_character(self, sample_user):
        """Test de récupération du personnage d'une campagne sans personnage."""
        user_id = sample_user["id"]

        # Créer une campagne sans personnage
        campaign_id = create_campaign(user_id, "Empty Campaign", ["Fantasy"], "fr")

        # Essayer de récupérer le personnage
        character = get_campaign_character(user_id, campaign_id)

        # Vérification
        assert character is None

    def test_get_campaign_character_invalid_params(self):
        """Test avec paramètres invalides."""
        # Paramètres None
        assert get_campaign_character(None, 1) is None
        assert get_campaign_character(1, None) is None

    def test_multiple_characters_different_campaigns(self, sample_user):
        """Test que chaque campagne peut avoir son propre personnage."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Fantasy Campaign", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Sci-Fi Campaign", ["Sci-Fi"], "en")

        # Créer un personnage pour chaque campagne
        char_id_1 = create_character(user_id, campaign_id_1, "Aragorn", "Rôdeur", "Humain")
        char_id_2 = create_character(user_id, campaign_id_2, "Spock", "Scientifique", "Vulcain")

        # Récupérer les personnages par campagne
        character_1 = get_campaign_character(user_id, campaign_id_1)
        character_2 = get_campaign_character(user_id, campaign_id_2)

        # Vérifications
        assert character_1["name"] == "Aragorn"
        assert character_1["campaign_id"] == campaign_id_1
        assert character_2["name"] == "Spock"
        assert character_2["campaign_id"] == campaign_id_2

    def test_character_belongs_to_specific_campaign(self, sample_user):
        """Test qu'un personnage appartient bien à sa campagne spécifique."""
        user_id = sample_user["id"]

        # Créer deux campagnes
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en")

        # Créer un personnage pour la première campagne
        create_character(user_id, campaign_id_1, "Hero", "Guerrier", "Humain")

        # Vérifier que le personnage n'est pas accessible depuis l'autre campagne
        character_in_campaign_1 = get_campaign_character(user_id, campaign_id_1)
        character_in_campaign_2 = get_campaign_character(user_id, campaign_id_2)

        assert character_in_campaign_1 is not None
        assert character_in_campaign_1["name"] == "Hero"
        assert character_in_campaign_2 is None

    def test_create_character_wrong_user_campaign(self, sample_user):
        """Test qu'on ne peut pas créer un personnage dans la campagne d'un autre utilisateur."""
        user_id = sample_user["id"]

        # Créer un autre utilisateur
        from database import get_connection
        import bcrypt

        conn = get_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw("otherpass".encode("utf-8"), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("other@test.com", hashed_password))
        other_user_id = cursor.lastrowid
        conn.commit()

        # Créer une campagne pour l'autre utilisateur
        other_campaign_id = create_campaign(other_user_id, "Other User Campaign", ["Fantasy"], "fr")

        # Essayer de créer un personnage dans la campagne de l'autre utilisateur
        with pytest.raises(ValueError, match="La campagne spécifiée n'appartient pas à cet utilisateur"):
            create_character(user_id, other_campaign_id, "Intruder", "Voleur", "Humain")

        # Nettoyer
        cursor.execute("DELETE FROM campaigns WHERE id = ?", (other_campaign_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (other_user_id,))
        conn.commit()
        conn.close()

    def test_character_isolation_between_users(self, sample_user):
        """Test que les personnages sont isolés entre les utilisateurs."""
        user_id = sample_user["id"]

        # Créer un autre utilisateur
        from database import get_connection
        import bcrypt

        conn = get_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw("user2pass".encode("utf-8"), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("user2@test.com", hashed_password))
        user2_id = cursor.lastrowid
        conn.commit()

        # Créer des campagnes pour chaque utilisateur
        campaign1_id = create_campaign(user_id, "User 1 Campaign", ["Fantasy"], "fr")
        campaign2_id = create_campaign(user2_id, "User 2 Campaign", ["Fantasy"], "fr")

        # Créer des personnages
        create_character(user_id, campaign1_id, "Hero1", "Guerrier", "Humain")
        create_character(user2_id, campaign2_id, "Hero2", "Magicien", "Elfe")

        # Vérifier l'isolation
        user1_character = get_campaign_character(user_id, campaign1_id)
        user2_character = get_campaign_character(user2_id, campaign2_id)

        # User 1 ne peut pas voir le personnage de User 2
        cross_character = get_campaign_character(user_id, campaign2_id)

        assert user1_character["name"] == "Hero1"
        assert user2_character["name"] == "Hero2"
        assert cross_character is None  # Isolation respectée

        # Nettoyer
        cursor.execute("DELETE FROM characters WHERE campaign_id IN (?, ?)", (campaign1_id, campaign2_id))
        cursor.execute("DELETE FROM campaigns WHERE id IN (?, ?)", (campaign1_id, campaign2_id))
        cursor.execute("DELETE FROM users WHERE id = ?", (user2_id,))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__])
