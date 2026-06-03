"""
GDPR/KVKK Compliance Helper Module
Uyum metriklerini hesapla, sorgula ve yönet
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any

from models import (
    ComplianceMetric, DataCategory, RtBFRequest, ConsentRecord,
    DataAccessLog, AuditLog, ComplianceViolation, ComplianceChecklist, LogEntry
)
from extensions import db


class ComplianceManager:
    """GDPR/KVKK uyum yöneticisi"""

    @staticmethod
    def calculate_compliance_scores() -> Dict[str, float]:
        """Genel uyum puanlarını hesapla"""
        scores = {
            "gdpr_score": 0.0,
            "kvkk_score": 0.0,
            "combined_score": 0.0
        }

        # Data retention kontrol
        retention_score = ComplianceManager._check_data_retention()

        # Encryption kontrolü
        encryption_score = ComplianceManager._check_encryption_status()

        # Access control kontrolü
        access_score = ComplianceManager._check_access_control()

        # Audit log kontrolü
        audit_score = ComplianceManager._check_audit_completeness()

        # GDPR skoru
        gdpr_score = (retention_score * 0.25 + encryption_score * 0.35 +
                      access_score * 0.25 + audit_score * 0.15)

        # KVKK skoru (GDPR'a benzer ama farklı ağırlıklar)
        kvkk_score = (retention_score * 0.20 + encryption_score * 0.30 +
                      access_score * 0.30 + audit_score * 0.20)

        combined = (gdpr_score + kvkk_score) / 2

        scores["gdpr_score"] = round(gdpr_score, 2)
        scores["kvkk_score"] = round(kvkk_score, 2)
        scores["combined_score"] = round(combined, 2)

        return scores

    @staticmethod
    def _check_data_retention() -> float:
        """Veri saklama politikası uygunluğunu kontrol et"""
        total_logs = LogEntry.query.count()
        if total_logs == 0:
            return 90.0

        # 90 gün öncesinden eski loglar
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_logs = LogEntry.query.filter(LogEntry.created_at < cutoff_date).count()

        if old_logs > 0:
            # Eski loglar bulundu, sil
            LogEntry.query.filter(LogEntry.created_at < cutoff_date).delete()
            db.session.commit()

        return 85.0

    @staticmethod
    def _check_encryption_status() -> float:
        """Şifreleme durumunu kontrol et"""
        categories = DataCategory.query.all()
        if not categories:
            return 80.0

        encrypted = sum(1 for cat in categories
                       if cat.protection_method in ['encryption', 'hashing'])
        encryption_percentage = (encrypted / len(categories)) * 100

        return min(encryption_percentage, 100.0)

    @staticmethod
    def _check_access_control() -> float:
        """Erişim kontrolünü kontrol et"""
        total_accesses = DataAccessLog.query.count()
        if total_accesses == 0:
            return 75.0

        denied = DataAccessLog.query.filter_by(status='denied').count()
        denied_percentage = (denied / total_accesses) * 100

        # Bazı reddedilen istekler iyi bir işaret
        if 5 <= denied_percentage <= 20:
            return 90.0
        elif denied_percentage > 20:
            return 70.0
        else:
            return 65.0 + (denied_percentage / 5 * 10)

    @staticmethod
    def _check_audit_completeness() -> float:
        """Audit log tamamlığını kontrol et"""
        total_logs = LogEntry.query.count()
        audit_logs = AuditLog.query.count()

        if total_logs == 0:
            return 70.0

        completeness = min((audit_logs / total_logs) * 100, 100.0)
        return completeness

    @staticmethod
    def get_data_categories_status() -> List[Dict[str, Any]]:
        """Veri kategorilerinin koruma durumunu getir"""
        categories = DataCategory.query.all()

        if not categories:
            # Varsayılan kategorileri oluştur
            default_categories = [
                {
                    "category_name": "Personal Data (PII)",
                    "description": "Kişisel bilgiler - isim, soyisim, TC kimliği",
                    "protection_method": "anonymization"
                },
                {
                    "category_name": "Financial Data",
                    "description": "Mali veriler - kredi kartı, banka hesabı",
                    "protection_method": "encryption"
                },
                {
                    "category_name": "Identity Data",
                    "description": "Kimlik verileri - Pasaport, Sürücü belgesi",
                    "protection_method": "hashing"
                },
                {
                    "category_name": "Contact Data",
                    "description": "İletişim verileri - Email, telefon",
                    "protection_method": "masking"
                }
            ]

            for cat_data in default_categories:
                category = DataCategory(
                    category_name=cat_data["category_name"],
                    description=cat_data["description"],
                    protection_method=cat_data["protection_method"],
                    protection_percentage=85.0,
                    total_records=1000,
                    protected_records=850
                )
                db.session.add(category)

            db.session.commit()
            categories = DataCategory.query.all()

        return [cat.to_dict() for cat in categories]

    @staticmethod
    def get_rtbf_metrics() -> Dict[str, Any]:
        """Right to be Forgotten metriklerini getir"""
        total_requests = RtBFRequest.query.count()
        pending_requests = RtBFRequest.query.filter_by(
            status='pending').count()
        in_progress = RtBFRequest.query.filter_by(
            status='in_progress').count()
        completed_requests = RtBFRequest.query.filter_by(
            status='completed').count()

        completion_rate = 0.0
        avg_completion_time = 0

        if completed_requests > 0:
            completed = RtBFRequest.query.filter_by(
                status='completed').all()
            total_days = sum(
                (req.completion_time_days or 0) for req in completed)
            avg_completion_time = total_days // completed_requests
            completion_rate = (completed_requests / total_requests * 100
                              if total_requests > 0 else 0)

        # Uzun süredir pending olan istekleri bul
        old_pending_date = datetime.utcnow() - timedelta(days=30)
        overdue_requests = RtBFRequest.query.filter(
            RtBFRequest.status == 'pending',
            RtBFRequest.requested_at < old_pending_date
        ).count()

        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "in_progress_requests": in_progress,
            "completed_requests": completed_requests,
            "completion_rate": round(completion_rate, 2),
            "avg_completion_time_days": avg_completion_time,
            "overdue_requests": overdue_requests
        }

    @staticmethod
    def get_consent_metrics() -> Dict[str, Any]:
        """Consent metriklerini getir"""
        total_consents = ConsentRecord.query.count()

        given = ConsentRecord.query.filter_by(status='given').count()
        withdrawn = ConsentRecord.query.filter_by(status='withdrawn').count()
        pending = ConsentRecord.query.filter_by(status='pending').count()

        # Süresi dolan consent'ler
        now = datetime.utcnow()
        expired = ConsentRecord.query.filter(
            ConsentRecord.expires_at < now).count()

        # Yakında süresi dolacak consent'ler (30 gün içinde)
        future_date = now + timedelta(days=30)
        expiring_soon = ConsentRecord.query.filter(
            ConsentRecord.expires_at >= now,
            ConsentRecord.expires_at <= future_date
        ).count()

        given_percentage = (given / total_consents * 100 if total_consents > 0 else 0)
        withdrawn_percentage = (withdrawn / total_consents * 100 if total_consents > 0 else 0)
        pending_percentage = (pending / total_consents * 100 if total_consents > 0 else 0)

        return {
            "total_consents": total_consents,
            "given": given,
            "withdrawn": withdrawn,
            "pending": pending,
            "expired": expired,
            "expiring_soon": expiring_soon,
            "given_percentage": round(given_percentage, 2),
            "withdrawn_percentage": round(withdrawn_percentage, 2),
            "pending_percentage": round(pending_percentage, 2)
        }

    @staticmethod
    def get_access_logs(limit: int = 10) -> List[Dict[str, Any]]:
        """Son veri erişim loglarını getir"""
        logs = DataAccessLog.query.order_by(
            DataAccessLog.accessed_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_audit_logs(limit: int = 20) -> List[Dict[str, Any]]:
        """Son audit loglarını getir"""
        logs = AuditLog.query.order_by(
            AuditLog.created_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_violations(include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Uyum ihlallerini getir"""
        query = ComplianceViolation.query.order_by(
            ComplianceViolation.detected_at.desc())

        if not include_resolved:
            query = query.filter_by(resolved=False)

        violations = query.all()
        return [v.to_dict() for v in violations]

    @staticmethod
    def get_compliance_checklist() -> Dict[str, Any]:
        """Uyum checklist'ini getir"""
        items = ComplianceChecklist.query.all()

        if not items:
            # Varsayılan checklist oluştur
            default_items = [
                "Data inventory completed",
                "Privacy policy updated",
                "Data processing agreements signed",
                "DPA/DPO assigned",
                "Technical measures implemented",
                "Privacy by design implemented",
                "Breach notification plan ready",
                "Staff training completed"
            ]

            for item_name in default_items:
                item = ComplianceChecklist(item_name=item_name, completed=False)
                db.session.add(item)

            db.session.commit()
            items = ComplianceChecklist.query.all()

        checklist_items = [item.to_dict() for item in items]
        completed = sum(1 for item in items if item.completed)
        total = len(items)
        completion_percentage = (completed / total * 100) if total > 0 else 0

        return {
            "items": checklist_items,
            "completed": completed,
            "total": total,
            "completion_percentage": round(completion_percentage, 2)
        }

    @staticmethod
    def create_rtbf_request(user_id: str, data_categories: List[str],
                           reason: str = None) -> Dict[str, Any]:
        """Yeni bir Right to be Forgotten isteği oluştur"""
        request = RtBFRequest(
            user_id=user_id,
            data_categories=data_categories,
            reason=reason,
            status='pending'
        )
        db.session.add(request)

        # Audit log oluştur
        audit = AuditLog(
            event_type='rtbf_request_created',
            description=f'RtBF request created for user {user_id}',
            actor='system',
            action_type='create',
            affected_resource=f'user:{user_id}'
        )
        db.session.add(audit)

        db.session.commit()
        return request.to_dict()

    @staticmethod
    def create_consent_record(user_id: str, consent_type: str,
                             given: bool = False) -> Dict[str, Any]:
        """Yeni bir consent kaydı oluştur"""
        status = 'given' if given else 'pending'
        given_date = datetime.utcnow() if given else None
        expires_at = datetime.utcnow() + timedelta(days=365) if given else None

        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            status=status,
            given_date=given_date,
            expires_at=expires_at
        )
        db.session.add(record)

        audit = AuditLog(
            event_type='consent_created',
            description=f'Consent record created for user {user_id}',
            actor='system',
            action_type='create',
            affected_resource=f'user:{user_id}'
        )
        db.session.add(audit)

        db.session.commit()
        return record.to_dict()

    @staticmethod
    def create_access_log(user_id: str, data_type: str, purpose: str = None,
                         status: str = 'approved', ip_address: str = None) -> Dict[str, Any]:
        """Veri erişim logunu kaydet"""
        log = DataAccessLog(
            user_id=user_id,
            data_type=data_type,
            access_purpose=purpose or "Not specified",
            status=status,
            ip_address=ip_address
        )
        db.session.add(log)

        if status == 'denied':
            # Unauthorized access attempt - violation oluştur
            violation = ComplianceViolation(
                violation_type='unauthorized_access',
                severity='warning',
                description=f'Unauthorized access attempt by {user_id} for {data_type}',
                affected_user_id=user_id
            )
            db.session.add(violation)

        db.session.commit()
        return log.to_dict()

    @staticmethod
    def update_checklist_item(item_id: int, completed: bool) -> Dict[str, Any]:
        """Checklist maddesini güncelle"""
        item = ComplianceChecklist.query.get(item_id)
        if not item:
            return {"error": "Item not found"}

        item.completed = completed
        if completed:
            item.completed_date = datetime.utcnow()

        audit = AuditLog(
            event_type='checklist_updated',
            description=f'Checklist item "{item.item_name}" updated',
            actor='admin',
            action_type='update',
            affected_resource=f'checklist:{item_id}'
        )
        db.session.add(audit)
        db.session.commit()

        return item.to_dict()

    @staticmethod
    def record_violation(violation_type: str, severity: str,
                        description: str, affected_user_id: str = None) -> Dict[str, Any]:
        """Uyum ihlali kaydını oluştur"""
        violation = ComplianceViolation(
            violation_type=violation_type,
            severity=severity,
            description=description,
            affected_user_id=affected_user_id,
            resolved=False
        )
        db.session.add(violation)

        audit = AuditLog(
            event_type='violation_detected',
            description=f'Compliance violation detected: {description}',
            actor='system',
            action_type='create',
            affected_resource='compliance'
        )
        db.session.add(audit)

        db.session.commit()
        return violation.to_dict()

    @staticmethod
    def get_compliance_summary() -> Dict[str, Any]:
        """Tüm uyum metriklerinin özet bilgisini getir"""
        scores = ComplianceManager.calculate_compliance_scores()
        data_categories = ComplianceManager.get_data_categories_status()
        rtbf_metrics = ComplianceManager.get_rtbf_metrics()
        consent_metrics = ComplianceManager.get_consent_metrics()
        violations = ComplianceManager.get_violations()
        checklist = ComplianceManager.get_compliance_checklist()

        return {
            "scores": scores,
            "data_categories": data_categories,
            "rtbf_metrics": rtbf_metrics,
            "consent_metrics": consent_metrics,
            "violations_count": len(violations),
            "critical_violations": len(
                [v for v in violations if v['severity'] == 'critical']),
            "checklist": checklist,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
