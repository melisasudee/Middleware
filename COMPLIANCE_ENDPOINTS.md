# GDPR/KVKK Compliance Dashboard API Endpoints

## Dashboard Arayüzü

### HTML Dashboard
- **GET** `/compliance/dashboard` - Compliance Dashboard HTML gösterir

## API Endpoints

### 1. Compliance Metrics

#### Genel Metrikleri Al
- **GET** `/compliance/metrics` - Tüm compliance metriklerini getir (auth required)
  
#### Uyum Puanlarını Al
- **GET** `/compliance/scores` - GDPR/KVKK uyum puanlarını getir (auth required)
  ```json
  {
    "gdpr_score": 92.15,
    "kvkk_score": 91.45,
    "combined_score": 91.80
  }
  ```

#### Veri Kategorilerini Al
- **GET** `/compliance/data-categories` - Veri kategorilerinin koruma durumunu getir (auth required)
  ```json
  [
    {
      "category_name": "Personal Data (PII)",
      "description": "Kişisel bilgiler",
      "protection_method": "anonymization",
      "protection_percentage": 85.0,
      "total_records": 1000,
      "protected_records": 850
    }
  ]
  ```

### 2. Right to be Forgotten (RtBF)

#### RtBF İsteklerini Listele
- **GET** `/compliance/rtbf-requests` - Tüm RtBF isteklerini ve metriklerini getir (auth required)

#### Yeni RtBF İsteği Oluştur
- **POST** `/compliance/rtbf-requests` - Yeni RtBF isteği oluştur
  ```json
  {
    "user_id": "user_123",
    "data_categories": ["Personal Data", "Contact Data"],
    "reason": "Kullanıcı isteği"
  }
  ```

#### Belirli RtBF İsteğini Al
- **GET** `/compliance/rtbf-requests/<id>` - Belirli bir RtBF isteğini getir (auth required)

#### RtBF İsteğini Güncelle
- **PUT** `/compliance/rtbf-requests/<id>` - RtBF isteğini güncelle (auth required)
  ```json
  {
    "status": "in_progress|completed|denied",
    "notes": "İşleme notları"
  }
  ```

### 3. Consent Management (Rıza Yönetimi)

#### Consent Kayıtlarını Listele
- **GET** `/compliance/consents` - Tüm consent kayıtlarını getir (auth required)

#### Yeni Consent Oluştur
- **POST** `/compliance/consents` - Yeni consent kaydı oluştur (rate limited: 20 per minute)
  ```json
  {
    "user_id": "user_123",
    "consent_type": "marketing|analytics|profiling",
    "given": true
  }
  ```

#### Consent'i Güncelle
- **PUT** `/compliance/consents/<id>` - Consent kaydını güncelle (auth required)
  ```json
  {
    "status": "given|withdrawn|pending"
  }
  ```

### 4. Data Access Logging (Veri Erişim Logging)

#### Veri Erişimini Kaydet
- **POST** `/compliance/access-logs` - Veri erişim logunu kaydet (rate limited: 100 per minute)
  ```json
  {
    "user_id": "user_123",
    "data_type": "personal_data|financial_data|identity_data",
    "purpose": "Erişim nedeni",
    "status": "approved|denied|pending"
  }
  ```

#### Access Log'ları Al
- **GET** `/compliance/access-logs?limit=10` - Son veri erişim loglarını getir (auth required)

### 5. Audit Logs (Denetim Logları)

#### Audit Log'ları Al
- **GET** `/compliance/audit-logs?limit=20` - Son audit loglarını getir (auth required)

### 6. Compliance Violations (Uyum İhlalleri)

#### İhlalleri Listele
- **GET** `/compliance/violations?include_resolved=false` - Uyum ihlallerini getir (auth required)

#### Yeni İhlal Kaydı Oluştur
- **POST** `/compliance/violations` - Yeni uyum ihlali kaydı oluştur (auth required)
  ```json
  {
    "violation_type": "data_breach|unauthorized_access|policy_violation",
    "severity": "critical|warning|info",
    "description": "İhlal açıklaması",
    "affected_user_id": "user_123"
  }
  ```

### 7. Compliance Checklist

#### Checklist'i Al
- **GET** `/compliance/checklist` - Compliance checklist'ini getir (auth required)

#### Checklist Maddesini Güncelle
- **PUT** `/compliance/checklist/<id>` - Checklist maddesini güncelle (auth required)
  ```json
  {
    "completed": true
  }
  ```

## Authentication

Tüm `(auth required)` ile işaretlenen endpoints için:
1. `/auth/login` endpoint'ine POST isteği gönderin
2. Alınan `access_token`'ı kullanarak diğer isteklerde `Authorization: Bearer <token>` header'ı ekleyin

## Rate Limiting

- `/compliance/rtbf-requests` (POST): 10 per minute
- `/compliance/consents` (POST): 20 per minute
- `/compliance/access-logs` (POST): 100 per minute

## Test Komutu Örnekleri

### 1. Giriş Yap ve Token Al
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### 2. Compliance Metriklerini Al
```bash
curl -X GET http://localhost:5000/compliance/metrics \
  -H "Authorization: Bearer <token>"
```

### 3. RtBF İsteği Oluştur
```bash
curl -X POST http://localhost:5000/compliance/rtbf-requests \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "data_categories": ["Personal Data"],
    "reason": "Hesap silme isteği"
  }'
```

### 4. Veri Erişimini Kaydet
```bash
curl -X POST http://localhost:5000/compliance/access-logs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_456",
    "data_type": "personal_data",
    "purpose": "Account verification",
    "status": "approved"
  }'
```

### 5. Dashboard'u Aç
```
http://localhost:5000/compliance/dashboard
```

## Database Models

### ComplianceMetric
Uyum puanlarını ve metrikleri saklar

### DataCategory
Veri kategorilerini ve koruma durumlarını saklar

### RtBFRequest
Unutulma Hakkı (RtBF) isteklerini saklar

### ConsentRecord
Kullanıcı rızası kayıtlarını saklar

### DataAccessLog
Veri erişim loglarını saklar

### AuditLog
Sistem denetim loglarını saklar

### ComplianceViolation
Uyum ihlallerini saklar

### ComplianceChecklist
GDPR/KVKK compliance checklist maddelerini saklar

## Features

✅ GDPR/KVKK Compliance Score hesaplanması
✅ Veri kategorileri koruma durumu takibi
✅ Right to be Forgotten (RtBF) istekleri yönetimi
✅ Kullanıcı rızası (Consent) yönetimi
✅ Veri erişim logging ve takibi
✅ Denetim (Audit) logging
✅ Uyum ihlalleri (Violations) takibi
✅ Compliance checklist
✅ Gerçek zamanlı dashboard
✅ Responsive web arayüz
