#!/usr/bin/env bash
# ============================================================================
# MediFlow - Provisionamento, Firewall, Segurança e Deploy em VM OCI Always Free
# Hackathon ONE G10 - Grupo 10: MediFlow
# Responsável: Ingrid Soares (Infra OCI, Redes, Segurança & Deploy)
#
# Uso na instância OCI Compute (Ubuntu 22.04 / 24.04 LTS Always Free):
#   chmod +x deploy/setup_oci_vm.sh
#   ./deploy/setup_oci_vm.sh
# ============================================================================

set -euo pipefail

echo "============================================================"
echo " 🏥 MediFlow - Setup Seguro de VM na Oracle Cloud (Always Free)"
echo "============================================================"

# 1. Atualização de pacotes de segurança e ferramentas de rede
echo "[1/5] Atualizando pacotes do sistema e instalando dependências básicas..."
sudo apt-get update -y
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    ufw \
    fail2ban \
    nginx

# 2. Instalação do Docker e Docker Compose Plugin (caso ainda não instalados)
if ! command -v docker >/dev/null 2>&1; then
    echo "[2/5] Instalando Docker Engine oficial..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
else
    echo "[2/5] Docker já instalado: $(docker --version)"
fi

# 3. Hardening de Permissões das Credenciais OCI (~/.oci) e .env
echo "[3/5] Aplicando hardening de permissões em ~/.oci e arquivo .env..."
mkdir -p "$HOME/.oci"
chmod 700 "$HOME/.oci"
if compgen -G "$HOME/.oci/*.pem" > /dev/null; then
    chmod 600 "$HOME/.oci/"*.pem
fi
if [ -f "$HOME/.oci/config" ]; then
    chmod 600 "$HOME/.oci/config"
fi
if [ -f ".env" ]; then
    chmod 600 ".env"
fi

# 4. Configuração de Firewall Local (UFW) alinhado à Security List da VCN OCI
echo "[4/5] Configurando regras de firewall (UFW) e proteção SSH (Fail2Ban)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment "SSH Admin"
sudo ufw allow 80/tcp comment "Nginx Reverse Proxy HTTP"
sudo ufw allow 443/tcp comment "HTTPS"
sudo ufw allow 8000/tcp comment "MediFlow FastAPI"
sudo ufw allow 8501/tcp comment "MediFlow Streamlit UI"
sudo ufw --force enable

sudo systemctl enable --now fail2ban

# 5. Configuração do Nginx e subida dos containers MediFlow
echo "[5/5] Configurando Reverse Proxy Nginx e iniciando containers MediFlow..."
if [ -f "deploy/nginx_mediflow.conf" ]; then
    sudo cp deploy/nginx_mediflow.conf /etc/nginx/sites-available/mediflow.conf
    sudo ln -sf /etc/nginx/sites-available/mediflow.conf /etc/nginx/sites-enabled/mediflow.conf
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx
fi

sudo docker compose -f deploy/docker-compose.yml up -d --build

echo "============================================================"
echo " ✅ Deploy do MediFlow concluído com sucesso na OCI!"
echo " - Interface Streamlit (via Nginx): http://<IP_PUBLICO_VM>/"
echo " - Interface Streamlit (direta):    http://<IP_PUBLICO_VM>:8501"
echo " - API FastAPI (Swagger Docs):      http://<IP_PUBLICO_VM>:8000/docs"
echo "============================================================"
