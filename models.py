from datetime import datetime

from extensions import db


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
        return cls(
            transaction_id=payload.get("transaction_id"),
            sender_id=payload.get("sender_id"),
            error_level=payload.get("error_level"),
            risk_level=payload.get("risk_level"),
            risk_score=payload.get("risk_score"),
            tags=payload.get("tags"),
            payload=payload,
            processed_at=payload.get("processed_at"),
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
