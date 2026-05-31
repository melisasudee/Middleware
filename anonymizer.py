import hashlib
import re
from typing import Any, Dict

SENSITIVE_FIELDS = ["credit_card", "tc_id", "sender_email", "receiver_email", "customer_email", "phone", "phone_number", "password", "secret"]

PATTERN_MAP = {
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "tc_id": re.compile(r"\b\d{11}\b"),
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b(?:\+?\d{2,3}[ -]?)?(?:\(?\d{3}\)?[ -]?)?\d{3}[ -]?\d{2}[ -]?\d{2,3}\b"),
}


def sha256_hash(value: str) -> str:
    if not isinstance(value, str):
        value = str(value)
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"HASH:{digest}"


def mask_value(value: str, prefix: int = 2, suffix: int = 2, mask_char: str = "*") -> str:
    if not isinstance(value, str):
        value = str(value)
    if len(value) <= prefix + suffix:
        return mask_char * len(value)
    return value[:prefix] + mask_char * (len(value) - prefix - suffix) + value[-suffix:]


def replace_with_redacted(value: str) -> str:
    return "[REDACTED]"


def anonymize_email(value: str) -> str:
    if not isinstance(value, str) or "@" not in value:
        return value
    local, domain = value.split("@", 1)
    return mask_value(local, prefix=1, suffix=1) + "@" + domain


def detect_and_redact_patterns(text: str, report: Dict[str, Any]) -> str:
    if not isinstance(text, str):
        return text

    redacted = text
    for name, pattern in PATTERN_MAP.items():
        matches = pattern.findall(redacted)
        for match in set(matches):
            report["patterns"].append({"pattern": name, "value": match})
            if name == "credit_card":
                redacted = redacted.replace(match, mask_value(match.replace(" ", ""), prefix=4, suffix=4))
                report["masked"].append(match)
            elif name == "tc_id":
                redacted = redacted.replace(match, mask_value(match, prefix=3, suffix=3))
                report["masked"].append(match)
            elif name == "email":
                redacted = redacted.replace(match, anonymize_email(match))
                report["masked"].append(match)
            else:
                redacted = redacted.replace(match, replace_with_redacted(match))
                report["replaced"].append(match)
    return redacted


def anonymize_field(field: str, value: Any, report: Dict[str, Any]) -> Any:
    if value is None:
        return value

    if field in {"password", "secret", "token"}:
        report["hashed"].append(field)
        return sha256_hash(str(value))

    if field in {"credit_card", "tc_id"}:
        report["masked"].append(field)
        return mask_value(str(value), prefix=4, suffix=4)

    if field.endswith("email") or field == "email":
        report["masked"].append(field)
        return anonymize_email(str(value))

    if field in {"phone", "phone_number", "mobile"}:
        report["replaced"].append(field)
        return replace_with_redacted(str(value))

    if isinstance(value, str):
        redacted = detect_and_redact_patterns(value, report)
        return redacted

    return value


def anonymize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        return event

    report = {"masked": [], "hashed": [], "replaced": [], "patterns": []}
    anonymized = {}

    for field, value in event.items():
        anonymized[field] = anonymize_field(field, value, report)

    if "transaction_id" in anonymized:
        anonymized["transaction_id"] = mask_value(str(anonymized["transaction_id"]), prefix=4, suffix=4)
        report["masked"].append("transaction_id")

    if "message" in anonymized:
        anonymized["message"] = detect_and_redact_patterns(str(anonymized["message"]), report)

    anonymized["anonymization_report"] = {
        "masked_fields": sorted(set(report["masked"])),
        "hashed_fields": sorted(set(report["hashed"])),
        "replaced_fields": sorted(set(report["replaced"])),
        "detected_patterns": report["patterns"],
    }

    return anonymized
