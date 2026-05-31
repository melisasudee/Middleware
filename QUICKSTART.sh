#!/bin/bash

# ============================================================================
# CENG302 DATA MIDDLEWARE - HIZLI BAŞLANGAÇ REHBERI
# ============================================================================

echo "🚀 Data Middleware Projesi - Hızlı Kurulum Rehberi"
echo "=================================================="
echo ""

# ============================================================================
# ADIM 1: DOSYA KURULUMU
# ============================================================================

echo "📁 ADIM 1: Dosya Yapısını Kontrol Etme..."
echo ""

required_files=(
    "app.py"
    "anonymizer.py"
    "enricher.py"
    "formatters.py"
    "data_generator.py"
    "scenarios.py"
    "performance_test.py"
    "Dockerfile.middleware"
    "Dockerfile.generator"
    "docker-compose.yml"
    "requirements_middleware.txt"
    "requirements_generator.txt"
    "README.md"
)

missing_files=0

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ EKSIK: $file"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -gt 0 ]; then
    echo ""
    echo "⚠️  $missing_files dosya eksik! Lütfen tüm dosyaları kontrol edin."
    exit 1
fi

echo ""
echo "✅ Tüm dosyalar mevcut!"
echo ""

# ============================================================================
# ADIM 2: DOCKER KONTROL
# ============================================================================

echo "🐳 ADIM 2: Docker Kurulumunu Kontrol Etme..."
echo ""

if ! command -v docker &> /dev/null; then
    echo "❌ Docker bulunamadı! Lütfen Docker yükleyin:"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose bulunamadı!"
    exit 1
fi

echo "✅ Docker: $(docker --version)"
echo "✅ Docker Compose: $(docker-compose --version)"
echo ""

# ============================================================================
# ADIM 3: PORT KONTROL
# ============================================================================

echo "🔌 ADIM 3: Port Kullanılabilirliğini Kontrol Etme..."
echo ""

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5000 kullanımda!"
    echo "   Docker-compose.yml'i düzenlemeniz gerekebilir."
else
    echo "✅ Port 5000 boş"
fi

echo ""

# ============================================================================
# ADIM 4: DOCKER BAŞLATMA
# ============================================================================

echo "🚀 ADIM 4: Docker Container'larını Başlatma..."
echo ""

echo "   → Image'ler inşa ediliyor..."
docker-compose build --quiet

echo "   → Container'lar başlatılıyor..."
docker-compose up -d

echo ""
echo "⏳ Container'lar başlatılıyor (30 saniye bekliyoruz)..."
sleep 30

echo ""

# ============================================================================
# ADIM 5: SAĞLIK KONTROL
# ============================================================================

echo "❤️  ADIM 5: Middleware Sağlığını Kontrol Etme..."
echo ""

max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ Middleware sağlıklı ve çalışıyor!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   ⏳ Deneme $attempt/$max_attempts..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Middleware başlatılamadı!"
    echo ""
    echo "📋 Logs'u kontrol edin:"
    echo "   docker-compose logs middleware"
    exit 1
fi

echo ""

# ============================================================================
# ADIM 6: BILGILENDIRME
# ============================================================================

echo "✨ KURULUM BAŞARILI! ✨"
echo ""
echo "=================================================="
echo "📊 DASHBOARD"
echo "=================================================="
echo "   🌐 http://localhost:5000/dashboard"
echo ""
echo "=================================================="
echo "📡 API ENDPOINTS"
echo "=================================================="
echo "   POST /process          - Logu işle"
echo "   POST /batch            - Batch işleme"
echo "   GET  /stats            - İstatistikler"
echo "   GET  /export           - Logları dışa aktar"
echo "   GET  /health           - Sağlık kontrol"
echo "   GET  /logs/critical    - Kritik loglar"
echo "   GET  /logs/errors      - Hata logları"
echo "   GET  /logs/by-risk     - Risk dağılımı"
echo ""
echo "=================================================="
echo "🧪 PERFORMANCE TEST"
echo "=================================================="
echo "   python performance_test.py"
echo ""
echo "=================================================="
echo "🛑 DURDURMA"
echo "=================================================="
echo "   docker-compose down"
echo ""
echo "=================================================="
echo "📚 DAHA FAZLA BILGI"
echo "=================================================="
echo "   Lütfen README.md dosyasını okuyun"
echo ""

echo ""
read -p "Test logu göndermek ister misiniz? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📤 Test logu gönderiliyor..."
    echo ""
    
    curl -s -X POST http://localhost:5000/process \
        -H "Content-Type: application/json" \
        -d '{
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
            "transaction_id": "TEST_'$(shuf -i 100000-999999 -n 1)'",
            "sender_id": "BANK_A",
            "sender_email": "test@example.com",
            "transaction_type": "TRANSFER",
            "amount": 5000.00,
            "currency": "USD",
            "credit_card": "4532-1234-5678-9012",
            "tc_id": "12345678901",
            "error_level": "INFO",
            "message": "Test transaction",
            "status": "SUCCESS"
        }' | python -m json.tool
    
    echo ""
    echo "✅ Test logu gönderildi!"
fi

echo ""
echo "🎉 Başlamaya hazırsınız! Dashboard'a erişin: http://localhost:5000/dashboard"
echo ""