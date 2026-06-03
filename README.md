# Middleware Data Processing Platform

Finansal işlem loglarını alan, PII alanlarını anonimleştiren, risk skoruyla zenginleştiren ve rol bazlı REST API + gerçek zamanlı dashboard sunan bir Flask middleware platformu.

## Servisler

| Servis | Port | Konteyner |
|---|---|---|
| Middleware (Ana API) | 5000 | `finalproje-middleware` |
| Data Generator | 5001 | `finalproje-generator` |

## Hızlı Başlangıç

Docker ve Docker Compose kurulu olmalıdır.

```bash
# Stack'i derle ve başlat
docker compose up -d --build

# Sağlık kontrolü
curl http://localhost:5000/health

# Dashboard
open http://localhost:5000
```

### Veri üretme

```bash
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "scenario": "normal"}'
```

### Stack durdurma

```bash
docker compose down
```

## API Endpointleri

### Core

| Method | Endpoint | Auth | Açıklama |
|---|---|---|---|
| GET | `/health` | - | Servis sağlık kontrolü |
| GET | `/` `/dashboard` | - | Web dashboard |
| GET | `/api/dashboard-stats` | - | Chart.js veri beslemesi |
| POST | `/auth/login` | - | JWT token al |
| POST | `/api/process` | ✅ | Tek log işle |
| POST | `/api/batch` | ✅ | Toplu log işle |
| GET | `/stats` | - | Özet istatistikler |

### Log Sorgulama

| Method | Endpoint | Auth | Açıklama |
|---|---|---|---|
| GET | `/logs/critical` | - | Kritik loglar |
| GET | `/logs/errors` | - | Hata logları |
| GET | `/logs/by-risk` | - | Risk seviyesine göre gruplu |

### Export

| Method | Endpoint | Auth | Açıklama |
|---|---|---|---|
| GET | `/export` | ✅ | Format export (`?format=json\|csv\|html`) |
| GET | `/api/export` | ✅ | Rol bazlı export (`?role=security\|developer\|admin\|auditor\|analyst`) |
| GET | `/format/<mode>` | - | Son logları formatla |

### Compliance (GDPR/KVKK)

`/compliance/dashboard`, `/compliance/metrics`, `/compliance/scores`,  
`/compliance/data-categories`, `/compliance/rtbf-requests`,  
`/compliance/consents`, `/compliance/access-logs`,  
`/compliance/audit-logs`, `/compliance/violations`, `/compliance/checklist`

## Kimlik Doğrulama

**API Key (header):**
```
X-API-KEY: local-api-key
```

**API Key (query param — browser export için):**
```
GET /api/export?role=security&api_key=local-api-key
```

**JWT:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'
# → {"data":{"access_token":"eyJ..."},"status":"ok"}
```

## Rol Bazlı Export

Dashboard'daki "Role-Based Log Export" panelinden veya API üzerinden:

| Rol | Format | Kapsam |
|---|---|---|
| security | CSV | ERROR + CRITICAL loglar, 9 güvenlik alanı |
| developer | JSON | ERROR/WARNING/CRITICAL, tüm alanlar |
| admin | HTML | Tüm loglar, 8 yönetim alanı |
| auditor | JSON (dual) | Tüm loglar, CSV + JSON envelope |
| analyst | CSV | Tüm loglar, 9 analitik alan |

## Dosya Yapısı

```
FinalProje/
├── app.py                 # Flask uygulaması, tüm route'lar, dashboard HTML
├── anonymizer.py          # PII anonimleştirme (mask, hash, redact)
├── auth.py                # JWT + API Key dual auth dekoratörü
├── compliance.py          # GDPR/KVKK uyum yöneticisi
├── config.py              # Dev/Production konfigürasyonları
├── data_generator.py      # Sentetik veri üretici (Flask sunucu modu)
├── enricher.py            # Risk skoru + tag motoru
├── extensions.py          # Flask extension başlatma (db, jwt, limiter)
├── formatters.py          # Strategy Pattern: JSON/CSV/HTML formatter'ları
├── init_compliance.py     # Compliance DB başlangıç verisi
├── log_classifier.py      # Rol bazlı log sınıflandırma (5 rol)
├── models.py              # SQLAlchemy modelleri (9 tablo)
├── performance_test.py    # Yük testi aracı
├── start_containers.py    # Docker yardımcı script
├── Dockerfile.middleware  # Middleware konteyner build
├── Dockerfile.generator   # Generator konteyner build
├── docker-compose.yml     # Servis orkestrasyonu
├── requirements_middleware.txt
├── requirements_generator.txt
├── requirements_dev.txt
├── PROJECT_REPORT.md      # Teknik proje raporu
└── tests/
    ├── conftest.py
    ├── test_app.py
    └── test_auth.py
```

## Testler

```bash
# venv aktifle
source .venv/bin/activate

# testleri çalıştır
python -m pytest tests/ -v
```

## Performans Testi

```bash
python performance_test.py \
  --target http://localhost:5000/api/process \
  --count 50 --workers 10 \
  --batch-size 20 --batch-count 5
```

## Container Durumu

```bash
docker ps
docker logs finalproje-middleware --tail 50
docker logs finalproje-generator  --tail 50
```
