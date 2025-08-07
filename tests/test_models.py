import sys
import os
import pytest

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import (
    save_model_choice, 
    create_campaign, 
    create_character, 
    get_user_campaigns,
    get_user_characters
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
        """Test de création de campagne."""
        user_id = sample_user["id"]
        
        # Créer une campagne
        campaign_id = create_campaign(
            user_id, 
            "Test Campaign", 
            ["Fantasy", "Adventure"], 
            "fr"
        )
        
        # Vérifier la création
        assert isinstance(campaign_id, int)
        assert campaign_id > 0
        
        # Vérifier en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, themes, language FROM campaigns WHERE id = ?", 
                      (campaign_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "Test Campaign"
        assert "Fantasy" in result[1]
        assert result[2] == "fr"

    def test_create_character(self, sample_user):
        """Test de création de personnage."""
        user_id = sample_user["id"]
        
        # Créer un personnage
        character_id = create_character(
            user_id,
            "Aragorn",
            "Rôdeur",
            "Humain",
            "Grand et sombre",
            "http://example.com/portrait.jpg"
        )
        
        # Vérifier la création
        assert isinstance(character_id, int)
        assert character_id > 0
        
        # Vérifier en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT name, class, race, description, portrait_url 
                         FROM characters WHERE id = ?""", (character_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "Aragorn"
        assert result[1] == "Rôdeur"
        assert result[2] == "Humain"
        assert result[3] == "Grand et sombre"
        assert result[4] == "http://example.com/portrait.jpg"

    def test_get_user_campaigns(self, sample_user):
        """Test de récupération des campagnes utilisateur."""
        user_id = sample_user["id"]
        
        # Créer plusieurs campagnes
        campaign_id_1 = create_campaign(user_id, "Campaign 1", ["Fantasy"], "fr")
        campaign_id_2 = create_campaign(user_id, "Campaign 2", ["Sci-Fi"], "en")
        
        # Récupérer les campagnes
        campaigns = get_user_campaigns(user_id)
        
        # Vérifications
        assert len(campaigns) == 2
        assert campaigns[0]["name"] == "Campaign 2"  # Plus récent en premier
        assert campaigns[1]["name"] == "Campaign 1"
        assert campaigns[0]["themes"] == ["Sci-Fi"]
        assert campaigns[1]["themes"] == ["Fantasy"]

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


if __name__ == "__main__":
    pytest.main([__file__])
