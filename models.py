from datetime import datetime, timedelta, timezone
from enum import Enum

from extensions import db


class RtBFStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DENIED = "denied"


class ConsentStatus(Enum):
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"


class ViolationType(Enum):
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    POLICY_VIOLATION = "policy_violation"
    RETENTION_VIOLATION = "retention_violation"


class LogEntry(db.Model):
    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(128), index=True)
    sender_id = db.Column(db.String(128), index=True)
    error_level = db.Column(db.String(64), index=True)
    risk_level = db.Column(db.String(64), index=True)
    risk_score = db.Column(db.Integer)
    tags = db.Column(db.JSON)
    payload = db.Column(db.JSON)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "sender_id": self.sender_id,
            "error_level": self.error_level,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "tags": self.tags,
            "payload": self.payload,
            "processed_at": self.processed_at.isoformat() + "Z" if self.processed_at else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }

    @classmethod
    def from_payload(cls, payload: dict):
        processed_at_value = payload.get("processed_at")
        if isinstance(processed_at_value, str):
            try:
                processed_at_value = datetime.fromisoformat(processed_at_value.replace("Z", "+00:00"))
            except ValueError:
                processed_at_value = None

        if isinstance(processed_at_value, datetime) and processed_at_value.tzinfo is not None:
            processed_at_value = processed_at_value.astimezone(timezone.utc).replace(tzinfo=None)

        return cls(
            transaction_id=payload.get("transaction_id"),
            sender_id=payload.get("sender_id"),
            error_level=payload.get("error_level"),
            risk_level=payload.get("risk_level"),
            risk_score=payload.get("risk_score"),
            tags=payload.get("tags"),
            payload=payload,
            processed_at=processed_at_value,
        )


class ApiKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    key = db.Column(db.String(256), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "key": self.key,
            "active": self.active,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class ComplianceMetric(db.Model):
    """GDPR/KVKK uyum metriklerini saklar"""
    __tablename__ = "compliance_metrics"

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(128), nullable=False)
    gdpr_score = db.Column(db.Float, default=0.0)
    kvkk_score = db.Column(db.Float, default=0.0)
    combined_score = db.Column(db.Float, default=0.0)
    data_retention_adherence = db.Column(db.Float, default=0.0)
    encryption_status = db.Column(db.Float, default=0.0)
    access_control_effectiveness = db.Column(db.Float, default=0.0)
    audit_log_completeness = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "gdpr_score": self.gdpr_score,
            "kvkk_score": self.kvkk_score,
            "combined_score": self.combined_score,
            "data_retention_adherence": self.data_retention_adherence,
            "encryption_status": self.encryption_status,
            "access_control_effectiveness": self.access_control_effectiveness,
            "audit_log_completeness": self.audit_log_completeness,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class DataCategory(db.Model):
    """Veri kategorilerini ve koruma durumlarını saklar"""
    __tablename__ = "data_categories"

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text)
    protection_method = db.Column(db.String(64))  # anonymization, encryption, hashing, masking
    protection_percentage = db.Column(db.Float, default=0.0)
    total_records = db.Column(db.Integer, default=0)
    protected_records = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "category_name": self.category_name,
            "description": self.description,
            "protection_method": self.protection_method,
            "protection_percentage": self.protection_percentage,
            "total_records": self.total_records,
            "protected_records": self.protected_records,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class RtBFRequest(db.Model):
    """Right to be Forgotten isteklerini saklar"""
    __tablename__ = "rtbf_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False, index=True)
    data_categories = db.Column(db.JSON)  # Silinmesi istenen veri kategorileri
    status = db.Column(db.String(32), default=RtBFStatus.PENDING.value)
    reason = db.Column(db.Text)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "data_categories": self.data_categories,
            "status": self.status,
            "reason": self.reason,
            "requested_at": self.requested_at.isoformat() + "Z" if self.requested_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
            "notes": self.notes,
        }

    @property
    def completion_time_days(self):
        if self.completed_at:
            return (self.completed_at - self.requested_at).days
        return None


class ConsentRecord(db.Model):
    """Kullanıcı rız ve consent kayıtlarını saklar"""
    __tablename__ = "consent_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False, index=True)
    consent_type = db.Column(db.String(128), nullable=False)  # marketing, analytics, profiling, etc.
    status = db.Column(db.String(32), default=ConsentStatus.PENDING.value)
    given_date = db.Column(db.DateTime)
    withdrawn_date = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "consent_type": self.consent_type,
            "status": self.status,
            "given_date": self.given_date.isoformat() + "Z" if self.given_date else None,
            "withdrawn_date": self.withdrawn_date.isoformat() + "Z" if self.withdrawn_date else None,
            "expires_at": self.expires_at.isoformat() + "Z" if self.expires_at else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class DataAccessLog(db.Model):
    """Veri erişim loglarını saklar"""
    __tablename__ = "data_access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False, index=True)
    data_type = db.Column(db.String(128), nullable=False)
    access_purpose = db.Column(db.String(256))
    status = db.Column(db.String(32), default="approved")  # approved, denied, pending
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "data_type": self.data_type,
            "access_purpose": self.access_purpose,
            "status": self.status,
            "ip_address": self.ip_address,
            "accessed_at": self.accessed_at.isoformat() + "Z" if self.accessed_at else None,
        }


class AuditLog(db.Model):
    """Sistem audit loglarını saklar"""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    actor = db.Column(db.String(128))  # Kim yaptı
    action_type = db.Column(db.String(64))  # create, update, delete, access
    affected_resource = db.Column(db.String(256))  # Hangi kaynağı etkiledi
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "description": self.description,
            "actor": self.actor,
            "action_type": self.action_type,
            "affected_resource": self.affected_resource,
            "details": self.details,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class ComplianceViolation(db.Model):
    """Uyum ihlallerini saklar"""
    __tablename__ = "compliance_violations"

    id = db.Column(db.Integer, primary_key=True)
    violation_type = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(32))  # critical, warning, info
    description = db.Column(db.Text)
    affected_user_id = db.Column(db.String(128), index=True)
    resolution_notes = db.Column(db.Text)
    resolved = db.Column(db.Boolean, default=False)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "description": self.description,
            "affected_user_id": self.affected_user_id,
            "resolution_notes": self.resolution_notes,
            "resolved": self.resolved,
            "detected_at": self.detected_at.isoformat() + "Z" if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() + "Z" if self.resolved_at else None,
        }


class ComplianceChecklist(db.Model):
    """GDPR/KVKK uyum checklist maddeleri"""
    __tablename__ = "compliance_checklist"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime)
    responsible = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "item_name": self.item_name,
            "description": self.description,
            "completed": self.completed,
            "completed_date": self.completed_date.isoformat() + "Z" if self.completed_date else None,
            "responsible": self.responsible,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }

