#!/bin/bash

# 🛡️ GDPR/KVKK Compliance Dashboard - Hızlı Başlangıç Rehberi
# Bu script compliance dashboard'u başlatmasında yardımcı olur

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🛡️ GDPR/KVKK COMPLIANCE DASHBOARD BAŞLATMA          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Adım 1: Python kontrol
echo -e "${BLUE}📋 Adım 1: Sistem Kontrol${NC}"
echo "─────────────────────────────────────────────────────────────────"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunamadı!${NC}"
    echo "Lütfen Python 3.8+ yükleyin: https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION bulundu"

# Adım 2: Proje klasörü
echo ""
echo -e "${BLUE}📁 Adım 2: Proje Klasörü${NC}"
echo "─────────────────────────────────────────────────────────────────"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${GREEN}✓${NC} Proje klasörü: $PROJECT_DIR"

cd "$PROJECT_DIR" || exit 1

# Adım 3: Virtual Environment
echo ""
echo -e "${BLUE}🔧 Adım 3: Virtual Environment${NC}"
echo "─────────────────────────────────────────────────────────────────"

if [ ! -d "venv" ]; then
    echo "Virtual environment oluşturuluyor..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment oluşturuldu"
else
    echo -e "${GREEN}✓${NC} Virtual environment zaten mevcut"
fi

# Virtual environment'i aktifleştir
source venv/bin/activate || . venv/Scripts/activate
echo -e "${GREEN}✓${NC} Virtual environment aktifleştirildi"

# Adım 4: Bağımlılıklar
echo ""
echo -e "${BLUE}📦 Adım 4: Bağımlılıklar Yükleniyor${NC}"
echo "─────────────────────────────────────────────────────────────────"

if [ -f "requirements_middleware.txt" ]; then
    echo "requirements_middleware.txt yükleniyor (bu biraz zaman alabilir)..."
    pip install -q -r requirements_middleware.txt
    echo -e "${GREEN}✓${NC} Bağımlılıklar yüklendi"
else
    echo -e "${RED}❌ requirements_middleware.txt bulunamadı!${NC}"
    exit 1
fi

# Adım 5: Veritabanı Başlatma
echo ""
echo -e "${BLUE}🗄️  Adım 5: Veritabanı Başlatılıyor${NC}"
echo "─────────────────────────────────────────────────────────────────"

if [ -f "init_compliance.py" ]; then
    echo "Compliance veritabanı başlatılıyor..."
    python3 init_compliance.py
    echo -e "${GREEN}✓${NC} Veritabanı başarıyla başlatıldı"
else
    echo -e "${YELLOW}⚠${NC} init_compliance.py bulunamadı"
    echo "  Manuel başlatma için: python3 init_compliance.py"
fi

# Adım 6: Başlatma
echo ""
echo -e "${BLUE}🚀 Adım 6: Uygulama Başlatılıyor${NC}"
echo "─────────────────────────────────────────────────────────────────"

echo ""
echo -e "${GREEN}✅ Tüm hazırlıklar tamamlandı!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}🌐 Flask Uygulaması Başlatılıyor...${NC}"
echo ""
echo "Tarayıcıda açın:"
echo -e "${BLUE}  http://localhost:5000/compliance/dashboard${NC}"
echo ""
echo "Oturum açma bilgileri (varsayılan):"
echo "  Kullanıcı: ${BLUE}admin${NC}"
echo "  Şifre:    ${BLUE}admin${NC}"
echo ""
echo "API Token almak için:"
echo -e "  ${BLUE}curl -X POST http://localhost:5000/auth/login \\${NC}"
echo -e "    ${BLUE}-H \"Content-Type: application/json\" \\${NC}"
echo -e "    ${BLUE}-d '{\"username\":\"admin\",\"password\":\"admin\"}'${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Uygulamayı başlat
python3 app.py
