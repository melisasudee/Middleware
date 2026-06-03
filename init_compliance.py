#!/usr/bin/env python3
"""
GDPR/KVKK Compliance Dashboard Initialization Script
Veritabanını varsayılan compliance verisiyle başlatır
"""

import sys
from datetime import datetime, timedelta

try:
    from app import app
    from models import (
        db, DataCategory, ComplianceChecklist, AuditLog
    )
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    print("Lütfen gerekli bağımlılıkları yükleyin: pip install -r requirements_middleware.txt")
    sys.exit(1)


def initialize_data_categories():
    """Varsayılan veri kategorilerini oluştur"""
    print("📊 Veri kategorileri başlatılıyor...")
    
    categories = [
        {
            "category_name": "Personal Data (PII)",
            "description": "Kişisel bilgiler - isim, soyisim, TC kimliği, doğum tarihi",
            "protection_method": "anonymization",
            "protection_percentage": 85.0,
            "total_records": 5000,
            "protected_records": 4250
        },
        {
            "category_name": "Financial Data",
            "description": "Mali veriler - kredi kartı, banka hesabı, ödeme bilgileri",
            "protection_method": "encryption",
            "protection_percentage": 95.0,
            "total_records": 3000,
            "protected_records": 2850
        },
        {
            "category_name": "Identity Data",
            "description": "Kimlik verileri - Pasaport, Sürücü belgesi, Vize bilgileri",
            "protection_method": "hashing",
            "protection_percentage": 90.0,
            "total_records": 2000,
            "protected_records": 1800
        },
        {
            "category_name": "Contact Data",
            "description": "İletişim verileri - Email, telefon, adres",
            "protection_method": "masking",
            "protection_percentage": 80.0,
            "total_records": 8000,
            "protected_records": 6400
        },
        {
            "category_name": "Health Data",
            "description": "Sağlık verileri - Tıbbi kayıtlar, ilaçlar",
            "protection_method": "encryption",
            "protection_percentage": 98.0,
            "total_records": 1500,
            "protected_records": 1470
        },
        {
            "category_name": "Biometric Data",
            "description": "Biyometrik veriler - Parmak izi, yüz tanıma",
            "protection_method": "hashing",
            "protection_percentage": 100.0,
            "total_records": 500,
            "protected_records": 500
        }
    ]

    for cat_data in categories:
        existing = DataCategory.query.filter_by(
            category_name=cat_data["category_name"]
        ).first()
        
        if not existing:
            category = DataCategory(**cat_data)
            db.session.add(category)
            print(f"  ✓ {cat_data['category_name']} eklendi")
        else:
            print(f"  ⚠ {cat_data['category_name']} zaten mevcut")

    db.session.commit()
    print("✅ Veri kategorileri başlatıldı\n")


def initialize_checklist():
    """Varsayılan compliance checklist'ini oluştur"""
    print("📋 Compliance Checklist başlatılıyor...")
    
    items = [
        {
            "item_name": "Data inventory completed",
            "description": "Tüm kişisel veri envanteri tamamlandı ve tanımlandı"
        },
        {
            "item_name": "Privacy policy updated",
            "description": "Gizlilik politikası GDPR/KVKK gereksinimlerine göre güncellendi"
        },
        {
            "item_name": "Data processing agreements signed",
            "description": "Tüm veri işleyicileri ile DPA (Data Processing Agreement) imzalandı"
        },
        {
            "item_name": "DPA/DPO assigned",
            "description": "Veri Koruma Müdürü (DPO) atandı ve kayıtlandı"
        },
        {
            "item_name": "Technical measures implemented",
            "description": "Teknik güvenlik önlemleri (şifreleme, firewall, vs.) uygulandı"
        },
        {
            "item_name": "Privacy by design implemented",
            "description": "Tasarımdan itibaren gizlilik ilkesi uygulanıyor"
        },
        {
            "item_name": "Breach notification plan ready",
            "description": "Veri ihlali bildirim prosedürü oluşturuldu ve test edildi"
        },
        {
            "item_name": "Staff training completed",
            "description": "Çalışanlar GDPR/KVKK ve veri koruma eğitimleri aldı"
        },
        {
            "item_name": "DPIA conducted",
            "description": "Etki Değerlendirmesi (DPIA) yapıldı"
        },
        {
            "item_name": "Audit trail logging enabled",
            "description": "Denetim logları kayıt altına alınıyor"
        },
        {
            "item_name": "Incident response procedures defined",
            "description": "İhlal olay müdahale prosedürleri tanımlandı"
        },
        {
            "item_name": "Third-party vendor audit completed",
            "description": "Üçüncü taraf satıcılar denetlendi ve onaylandı"
        }
    ]

    for item_data in items:
        existing = ComplianceChecklist.query.filter_by(
            item_name=item_data["item_name"]
        ).first()
        
        if not existing:
            item = ComplianceChecklist(**item_data)
            db.session.add(item)
            print(f"  ✓ {item_data['item_name']} eklendi")
        else:
            print(f"  ⚠ {item_data['item_name']} zaten mevcut")

    db.session.commit()
    print("✅ Compliance Checklist başlatıldı\n")


def initialize_audit_logs():
    """İlk denetim loglarını oluştur"""
    print("📝 Denetim Logları başlatılıyor...")
    
    # Eğer hiç log yoksa, başlatma logları oluştur
    existing_logs = AuditLog.query.count()
    if existing_logs == 0:
        logs = [
            {
                "event_type": "system_initialized",
                "description": "GDPR/KVKK Compliance Dashboard başlatıldı",
                "actor": "system",
                "action_type": "create",
                "affected_resource": "compliance_system"
            },
            {
                "event_type": "data_categories_initialized",
                "description": "Veri kategorileri başlatıldı",
                "actor": "system",
                "action_type": "create",
                "affected_resource": "data_categories"
            },
            {
                "event_type": "checklist_initialized",
                "description": "Compliance checklist başlatıldı",
                "actor": "system",
                "action_type": "create",
                "affected_resource": "compliance_checklist"
            }
        ]

        for log_data in logs:
            log = AuditLog(**log_data)
            db.session.add(log)
            print(f"  ✓ {log_data['event_type']} kaydedildi")

        db.session.commit()
    
    print("✅ Denetim Logları başlatıldı\n")


def main():
    """Ana başlatma fonksiyonu"""
    print("\n" + "="*60)
    print("🛡️  GDPR/KVKK Compliance Dashboard Başlatılıyor")
    print("="*60 + "\n")

    with app.app_context():
        try:
            # Veritabanını oluştur/güncelle
            print("🗄️  Veritabanı şeması oluşturuluyor...")
            db.create_all()
            print("✅ Veritabanı şeması hazır\n")

            # Varsayılan verileri başlat
            initialize_data_categories()
            initialize_checklist()
            initialize_audit_logs()

            print("="*60)
            print("✅ GDPR/KVKK Compliance Dashboard başarıyla başlatıldı!")
            print("="*60)
            print("\n🌐 Dashboard'a erişmek için:")
            print("   http://localhost:5000/compliance/dashboard")
            print("\n📚 API Endpoints:")
            print("   GET  /compliance/metrics        - Tüm metrikleri getir")
            print("   GET  /compliance/scores         - Uyum puanlarını getir")
            print("   GET  /compliance/data-categories - Veri kategorilerini getir")
            print("   GET  /compliance/dashboard      - Dashboard HTML'i göster")
            print("\n💡 Daha fazla endpoint için:")
            print("   cat COMPLIANCE_ENDPOINTS.md")
            print("\n")

            return 0

        except Exception as e:
            print(f"\n❌ Başlatma hatası: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(main())
