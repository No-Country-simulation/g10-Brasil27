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
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    iptables-persistent \
    netfilter-persistent \
    fail2ban \
    nginx

# 2. Instalação do Docker e Docker Compose Plugin (caso ainda não instalados)
if ! command -v docker >/dev/null 2>&1; then
    echo "[2/5] Instalando Docker Engine oficial..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "Usuário $USER adicionado ao grupo docker."
else
    echo "[2/5] Docker já instalado: $(docker --version)"
    sudo usermod -aG docker "$USER" 2>/dev/null || true
fi

# 3. Hardening de Permissões das Credenciais OCI (~/.oci) e .env
echo "[3/5] Aplicando permissões em ~/.oci (UID 10001:10001 do container) e .env..."
mkdir -p "$HOME/.oci"
chmod 755 "$HOME/.oci"
if compgen -G "$HOME/.oci/*.pem" > /dev/null; then
    chmod 600 "$HOME/.oci/"*.pem
fi
if [ -f "$HOME/.oci/config" ]; then
    chmod 600 "$HOME/.oci/config"
fi
if [ -f ".env" ]; then
    chmod 600 ".env"
fi
sudo chown -R 10001:10001 "$HOME/.oci"

# 4. Configuração de Firewall Local (iptables) alinhado à Security List da VCN OCI
# A imagem Ubuntu da OCI utiliza regras nativas de iptables com REJECT.
# Inserimos as portas 80 e 443 antes do REJECT e persistimos via netfilter-persistent (sem UFW).
echo "[4/5] Configurando regras de firewall (iptables) e proteção SSH (Fail2Ban)..."
if ! sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
fi
if ! sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
fi
sudo netfilter-persistent save || true

sudo systemctl enable --now fail2ban

# 5. Configuração do Nginx e subida dos containers MediFlow
echo "[5/5] Configurando Reverse Proxy Nginx e iniciando containers MediFlow..."
if [ -f "deploy/nginx_mediflow.conf" ]; then
    sudo cp deploy/nginx_mediflow.conf /etc/nginx/sites-available/mediflow.conf
    sudo ln -sf /etc/nginx/sites-available/mediflow.conf /etc/nginx/sites-enabled/mediflow.conf
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx
fi

# Executa docker compose sem sudo para preservar o $HOME do usuário (evita montar /root/.oci)
docker compose -f deploy/docker-compose.yml up -d --build

echo "============================================================"
echo " ✅ Deploy do MediFlow concluído com sucesso na OCI!"
echo " - Interface Streamlit (via Nginx): http://<IP_PUBLICO_VM>/"
echo " - API FastAPI (via Nginx):         http://<IP_PUBLICO_VM>/api/v1/saude"
echo "============================================================"
