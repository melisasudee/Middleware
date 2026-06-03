# 🛡️ GDPR/KVKK Compliance Dashboard

Veri Middleware projesi için oluşturulan, GDPR (General Data Protection Regulation) ve KVKK (Kişisel Verileri Koruma Kanunu) uyumluluğunu gerçek zamanlı olarak izleyen bir dashboard sistemidir.

## 📋 İçindekiler
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Başlatma](#başlatma)
- [Kullanım](#kullanım)
- [API Endpoints](#api-endpoints)
- [Database Modelleri](#database-modelleri)
- [Dashboard Özellikleri](#dashboard-özellikleri)
- [Security](#security)

## ✨ Özellikler

### 📊 Compliance Scoring
- **GDPR Score** - GDPR uyum puanı (0-100%)
- **KVKK Score** - KVKK uyum puanı (0-100%)
- **Combined Score** - Birleşik uyum puanı
- **Weighted Metrics** - Çeşitli faktörlerle ağırlıklı hesaplama

### 🔐 Veri Koruma Takibi
- Kişisel veri (PII) anonimleştirme durumu
- Mali veri şifreleme durumu
- Kimlik verisi hashing durumu
- İletişim verisi masklama durumu
- Sağlık verisi şifreleme durumu
- Biyometrik veri hashing durumu

### 🗑️ Unutulma Hakkı (Right to be Forgotten - RtBF)
- RtBF istekleri yönetimi
- İstek durumu takibi (Pending/In Progress/Completed)
- Tamamlanma süresi ölçümü
- Vadesi geçen isteklerin tespiti
- Tamamlanma oranı hesaplanması

### ✅ Rıza & Onay Yönetimi (Consent)
- Kullanıcı rizası kaydı
- Rıza durumu geçmişi
- Rıza süresi yönetimi
- Yakında sonlanacak rizaların uyarısı
- Kategorilere göre rıza takibi

### 📝 Denetim Logları (Audit Logs)
- Tüm sistem işlemlerinin kaydı
- İşlem türüne göre kategorilendirme
- Zaman damgalı kayıtlar
- İşlem yapan kişi/sistem kaydı 
- Etkilenen kaynakların kaydı

### 🚨 İhlal & Uyarı Sistemi
- Veri ihlallerinin tespiti ve kaydı
- Yetkisiz erişim denemelerinin kaydı
- Uyum ihlallerinin otomatik tespiti
- Saklama politikası ihlallerinin tespiti
- Kritik/Uyarı/Bilgi seviyesiyle kategorilendirme

### 📋 Compliance Checklist
- 12 maddelik GDPR/KVKK kontrol listesi
- İlerleme takibi
- Tamamlanma yüzdesinin hesaplanması
- Her maddenin açıklaması

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- Flask 2.3.4+
- SQLAlchemy
- Flask-JWT-Extended
- PostgreSQL ya da SQLite

### Bağımlılıkların Yüklenmesi

```bash
# Middleware bağımlılıklarını yükle
pip install -r requirements_middleware.txt

# veya development için
pip install -r requirements_dev.txt
```

### Veritabanı Şemasının Oluşturulması

```bash
# Otomatik başlatma scripti çalıştır
python init_compliance.py

# Veya manuel olarak:
# Python interaktif modunda
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

## 🎯 Başlatma

### Docker ile Başlatma (Önerilen)

```bash
# Tüm servisleri başlat
docker-compose up -d

# Compliance dashboard'a erişin
# http://localhost:5000/compliance/dashboard
```

### Lokal Python ile Başlatma

```bash
# 1. Çevresel değişkenleri ayarla
export FLASK_ENV=development
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin

# 2. Bağımlılıkları yükle
pip install -r requirements_middleware.txt

# 3. Veritabanını başlat
python init_compliance.py

# 4. Flask uygulamasını çalıştır
python app.py

# 5. Dashboard'a erişin
# http://localhost:5000/compliance/dashboard
```

## 📊 Kullanım

### Dashboard Web Arayüzü

Tarayıcıda aşağıdaki URL'ye erişin:
```
http://localhost:5000/compliance/dashboard
```

Dashboard otomatik olarak her 30 saniyede verileri yeniler.

**Dashboard Bölümleri:**
1. **Uyum Puanları** - GDPR, KVKK ve birleşik puanlar
2. **İhlal Özeti** - Kritik, uyarı ve bilgi seviyesi ihlalleri
3. **Checklist İlerleme** - Compliance checklist tamamlanma yüzdesi
4. **Veri Koruma Durumu** - Her veri kategorisinin koruma yüzdesi
5. **RtBF Metrikleri** - Unutulma Hakkı istekleri
6. **Rıza Yönetimi** - Kullanıcı rizaları ve durumları
7. **Aktiviteler & Uyarılar** - Sistem uyarıları ve etkinlikleri
8. **Compliance Checklist** - Yapılacaklar listesi

### API Kullanımı

#### 1. Giriş Yapma ve Token Alma

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }'

# Yanıt:
# {
#   "status": "ok",
#   "data": {
#     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
#   }
# }
```

#### 2. Compliance Metriklerini Alma

```bash
TOKEN="<access_token>"

curl -X GET http://localhost:5000/compliance/metrics \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. RtBF İsteği Oluşturma

```bash
curl -X POST http://localhost:5000/compliance/rtbf-requests \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "data_categories": ["Personal Data", "Contact Data"],
    "reason": "User requested account deletion"
  }'
```

#### 4. Veri Erişimini Logging

```bash
curl -X POST http://localhost:5000/compliance/access-logs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin_user",
    "data_type": "personal_data",
    "purpose": "Account verification",
    "status": "approved"
  }'
```

## 📡 API Endpoints

### Genel Metrikleri Alma
- **GET** `/compliance/metrics` (auth required)
  - Tüm compliance metriklerini döner

### Uyum Puanları
- **GET** `/compliance/scores` (auth required)
  - GDPR, KVKK ve birleşik puanları döner

### Veri Kategorileri
- **GET** `/compliance/data-categories` (auth required)
  - Veri kategorilerinin koruma durumunu döner

### Right to be Forgotten
- **GET** `/compliance/rtbf-requests` (auth required)
  - Tüm RtBF isteklerini döner
- **POST** `/compliance/rtbf-requests` (rate limited: 10/min)
  - Yeni RtBF isteği oluşturur
- **GET** `/compliance/rtbf-requests/<id>` (auth required)
  - Belirli bir RtBF isteğini döner
- **PUT** `/compliance/rtbf-requests/<id>` (auth required)
  - RtBF isteğinin durumunu günceller

### Consent Yönetimi
- **GET** `/compliance/consents` (auth required)
  - Tüm consent kayıtlarını döner
- **POST** `/compliance/consents` (rate limited: 20/min)
  - Yeni consent kaydı oluşturur
- **PUT** `/compliance/consents/<id>` (auth required)
  - Consent kaydını günceller

### Veri Erişim Logging
- **POST** `/compliance/access-logs` (rate limited: 100/min)
  - Veri erişim logunu kaydeder
- **GET** `/compliance/access-logs` (auth required)
  - Son veri erişim loglarını döner

### Denetim Logları
- **GET** `/compliance/audit-logs` (auth required)
  - Son denetim loglarını döner

### İhlal Yönetimi
- **GET** `/compliance/violations` (auth required)
  - Uyum ihlallerini döner
- **POST** `/compliance/violations` (auth required)
  - Yeni uyum ihlali kaydı oluşturur

### Checklist
- **GET** `/compliance/checklist` (auth required)
  - Compliance checklist'ini döner
- **PUT** `/compliance/checklist/<id>` (auth required)
  - Checklist maddesini günceller

## 🗄️ Database Modelleri

### ComplianceMetric
```python
{
  "id": 1,
  "gdpr_score": 92.15,
  "kvkk_score": 91.45,
  "combined_score": 91.80,
  "data_retention_adherence": 85.0,
  "encryption_status": 90.0,
  "access_control_effectiveness": 88.0,
  "audit_log_completeness": 95.0,
  "created_at": "2026-06-02T10:30:00Z"
}
```

### DataCategory
```python
{
  "id": 1,
  "category_name": "Personal Data (PII)",
  "protection_method": "anonymization",
  "protection_percentage": 85.0,
  "total_records": 5000,
  "protected_records": 4250
}
```

### RtBFRequest
```python
{
  "id": 1,
  "user_id": "user_123",
  "status": "pending|in_progress|completed|denied",
  "requested_at": "2026-06-02T10:00:00Z",
  "completed_at": "2026-06-05T14:30:00Z"
}
```

### ConsentRecord
```python
{
  "id": 1,
  "user_id": "user_123",
  "consent_type": "marketing",
  "status": "given|withdrawn|pending|expired",
  "given_date": "2026-06-02T10:00:00Z",
  "expires_at": "2027-06-02T10:00:00Z"
}
```

## 🎨 Dashboard Özellikleri

### Responsive Tasarım
- Masaüstü, tablet ve mobil cihazlar için optimize edilmiş
- Açık ve koyu tema desteği için hazırlanmış

### Gerçek Zamanlı Güncelleme
- 30 saniye aralıklarla otomatik yenileme
- Manual yenileme düğmesi

### İnteraktif Bileşenler
- Dinamik göstergeler (gauges)
- Durum rozetleri (status badges)
- İlerleme çubukları
- Kaydırılabilir listeler

### Uyarı Sistemi
- Kritik uyarılar (kırmızı)
- Uyarılar (sarı)
- Başarı mesajları (yeşil)
- Bilgi mesajları (mavi)

## 🔒 Security

### Authentication
- JWT token tabanlı kimlik doğrulama
- Token süresi sınırı
- Secure token generation

### Authorization
- Rol tabanlı erişim kontrolü
- Admin ve user rolleri
- Endpoint bazında kullanıcı gereksinimi

### Rate Limiting
- `/compliance/rtbf-requests` (POST): 10 per minute
- `/compliance/consents` (POST): 20 per minute
- `/compliance/access-logs` (POST): 100 per minute

### Data Protection
- AES-256 şifreleme
- TLS 1.3 in transit
- Hassas verilerin maskelenmesi
- Denetim logları her işlem için

## 📈 Uyum Puanları Nasıl Hesaplanır?

### GDPR Score Hesaplama
```
GDPR = (Retention × 0.25) + (Encryption × 0.35) + 
       (Access Control × 0.25) + (Audit × 0.15)
```

### KVKK Score Hesaplama
```
KVKK = (Retention × 0.20) + (Encryption × 0.30) + 
       (Access Control × 0.30) + (Audit × 0.20)
```

### Faktörler
- **Data Retention** - Veri saklama politikası uygunluğu
- **Encryption** - Veri şifreleme yüzdesi
- **Access Control** - Erişim kontrol etkinliği
- **Audit** - Denetim log tamamlığı

## 🐛 Sorun Giderme

### Problem: Veritabanı hatası
```
Çözüm: python init_compliance.py komutunu çalıştırın
```

### Problem: Token süresi dolmuş
```
Çözüm: Yeni token almak için /auth/login endpoint'ini kullanın
```

### Problem: Rate limit hatasından oluştu
```
Çözüm: Belirtilen saniye bekleyin ve tekrar deneyin
```

## 📚 Ek Kaynaklar

- [GDPR Resmi Sitesi](https://gdpr.eu/)
- [KVKK - KVKK Rehberi](https://www.kvk.gov.tr/)
- [Compliance Endpoints Dokumentasyonu](COMPLIANCE_ENDPOINTS.md)
- [Güvenlik Önlemleri](SECURITY_ENHANCEMENTS_SUMMARY.md)

## 📝 Lisans

Bu proje Data Middleware projesinin bir parçasıdır. Daha fazla bilgi için ana README.md dosyasına bakın.

## 🤝 Katkı

Katkı yapmak isteryeniz, lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını inceleyin.

---

**Son Güncelleme:** 2 Haziran 2026  
**Versiyon:** 1.0.0  
**Durum:** ✅ Production Ready
