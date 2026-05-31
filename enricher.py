from datetime import datetime
import re
from typing import Any, Dict, List

RISK_THRESHOLDS = [1000, 5000, 20000]
ERROR_KEYWORDS = {
    "authentication": "AUTH_ERROR",
    "timeout": "TIMEOUT_ERROR",
    "expired": "AUTH_ERROR",
    "denied": "AUTH_ERROR",
    "fraud": "FRAUD_ALERT",
    "rate limit": "THROTTLE_ERROR",
    "failure": "SYSTEM_ERROR",
}

TAG_TEMPLATES = [
    "risk:{risk_level}",
    "type:{transaction_type}",
    "source:{source_system}",
    "status:{status}",
]


def compute_risk_score(amount: Any, error_level: str = None) -> int:
    if amount is None:
        base = 10
    else:
        try:
            amount = float(amount)
            if amount >= RISK_THRESHOLDS[2]:
                base = 95
            elif amount >= RISK_THRESHOLDS[1]:
                base = 75
            elif amount >= RISK_THRESHOLDS[0]:
                base = 40
            else:
                base = 10
        except (ValueError, TypeError):
            base = 10

    if error_level and error_level.upper() in {"ERROR", "CRITICAL"}:
        base = max(base, 85)
    return base


def describe_risk(score: int) -> str:
    if score >= 90:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def classify_error(message: Any, error_level: str = None) -> str:
    if error_level and error_level.upper() == "CRITICAL":
        return "SYSTEM_CRITICAL"

    text = str(message or "").lower()
    for keyword, label in ERROR_KEYWORDS.items():
        if keyword in text:
            return label

    if error_level and error_level.upper() == "WARNING":
        return "WARN"

    return "NO_ERROR"


def build_tags(event: Dict[str, Any], risk_level: str, error_classification: str) -> List[str]:
    tags = []
    for template in TAG_TEMPLATES:
        value = template.format(
            risk_level=risk_level,
            transaction_type=event.get("transaction_type", "UNKNOWN"),
            source_system=event.get("source_system", "unknown"),
            status=event.get("status", "unknown"),
        )
        tags.append(value)

    if error_classification != "NO_ERROR":
        tags.append(f"error:{error_classification}")

    if event.get("transaction_type") == "REFUND":
        tags.append("operation:refund")
    elif event.get("transaction_type") == "PAYMENT":
        tags.append("operation:payment")
    else:
        tags.append("operation:transfer")

    if event.get("currency") not in {"USD", "EUR", "TRY"}:
        tags.append("currency:other")

    return sorted(set(tags))


def analyze_transaction(event: Dict[str, Any]) -> Dict[str, Any]:
    amount = event.get("amount")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0

    if amount >= 20000:
        bucket = "EXTREME"
    elif amount >= 5000:
        bucket = "HIGH"
    elif amount >= 1000:
        bucket = "MEDIUM"
    else:
        bucket = "LOW"

    return {
        "amount_bucket": bucket,
        "is_high_value": amount >= 10000,
        "requires_manual_review": bucket in {"HIGH", "EXTREME"},
        "transaction_age_seconds": 0,
        "trust_score": max(0, 100 - int(amount / 1000)),
    }


def enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        return event

    enriched = dict(event)
    enriched.setdefault("source_system", "web-gateway")
    enriched.setdefault("geo_region", "EU")

    amount = enriched.get("amount")
    error_level = enriched.get("error_level")
    risk_score = compute_risk_score(amount, error_level)
    risk_level = describe_risk(risk_score)
    error_classification = classify_error(enriched.get("message"), error_level)

    if enriched.get("transaction_type") == "REFUND":
        risk_level = "LOW"
        risk_score = min(risk_score, 20)

    if enriched.get("sender_id", "").startswith("BANK_") and amount is not None:
        try:
            if float(amount) > 10000:
                risk_level = "HIGH"
                risk_score = max(risk_score, 80)
        except (TypeError, ValueError):
            pass

    enriched["risk_score"] = risk_score
    enriched["risk_level"] = risk_level
    enriched["error_classification"] = error_classification
    enriched["tags"] = build_tags(enriched, risk_level, error_classification)
    enriched["analysis"] = analyze_transaction(enriched)
    enriched["processed_at"] = datetime.utcnow().isoformat() + "Z"

    if error_classification not in {"NO_ERROR", None}:
        enriched["tags"].append("flagged:error")

    return enriched
