#!/bin/bash
# Script de déploiement automatisé sur VPS OVH

# Charger les variables d'environnement
source .env

echo "🚀 Déploiement sur VPS OVH"
echo "IP: $IPv4"
echo "User: $NAME"

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Préparation du déploiement...${NC}"

# Créer un script temporaire pour le serveur
cat > deploy_remote.sh << 'EOF'
#!/bin/bash
echo "🔄 Mise à jour du système..."
apt update && apt upgrade -y

echo "📥 Installation des outils essentiels..."
apt install -y curl wget git nano htop

echo "🐳 Installation de Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

echo "🔧 Installation de Docker Compose..."
apt install -y docker-compose-plugin

echo "🛡️ Configuration du firewall..."
apt install -y ufw
ufw --force reset
ufw allow 22/tcp
ufw allow 8501/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "📁 Préparation du répertoire de l'application..."
cd /root
if [ -d "CompareModelPoc" ]; then
    echo "🔄 Mise à jour du code existant..."
    cd CompareModelPoc
    git pull origin main
else
    echo "📥 Clonage du repository..."
    git clone https://github.com/AFlo59/CompareModelPoc.git
    cd CompareModelPoc
fi

echo "✅ Serveur préparé pour le déploiement !"
EOF

echo -e "${BLUE}📤 Copie du script sur le serveur...${NC}"

# Copier le script sur le serveur
scp deploy_remote.sh $NAME@$IPv4:/tmp/

echo -e "${BLUE}🔗 Connexion au serveur et exécution...${NC}"

# Se connecter au serveur et exécuter le script
ssh $NAME@$IPv4 << EOF
chmod +x /tmp/deploy_remote.sh
sudo /tmp/deploy_remote.sh
rm /tmp/deploy_remote.sh
EOF

echo -e "${GREEN}✅ Préparation du serveur terminée !${NC}"
echo -e "${BLUE}📋 Prochaines étapes :${NC}"
echo "1. Connectez-vous au serveur : ssh $NAME@$IPv4"
echo "2. Allez dans le dossier : cd /root/CompareModelPoc"
echo "3. Créez le fichier .env avec vos clés API"
echo "4. Lancez l'application : cd docker && docker compose up -d"

# Nettoyer
rm deploy_remote.sh

echo -e "${GREEN}🎉 Script terminé !${NC}"
