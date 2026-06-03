from enum import Enum
from typing import Any, Dict, List, Optional


class LogType(Enum):
    SECURITY = "security"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class Role(Enum):
    SECURITY = "security"
    DEVELOPER = "developer"
    ADMIN = "admin"
    AUDITOR = "auditor"
    ANALYST = "analyst"


# ── Role configuration tables ─────────────────────────────────────────────────

_ROLE_FORMAT: Dict[str, str] = {
    "security":  "csv",
    "developer": "json",
    "admin":     "html",
    "auditor":   "dual",
    "analyst":   "csv",
}

# None → include all fields after flattening
_ROLE_FIELDS: Dict[str, Optional[List[str]]] = {
    "security": [
        "transaction_id", "sender_id", "sender_email",
        "error_level", "risk_level", "risk_score",
        "tags", "processed_at", "created_at",
    ],
    "developer": None,
    "admin": [
        "id", "transaction_id", "sender_id",
        "error_level", "risk_level", "risk_score",
        "processed_at", "created_at",
    ],
    "auditor": None,
    "analyst": [
        "transaction_id", "amount", "currency",
        "transaction_type", "risk_level", "risk_score",
        "status", "error_level", "processed_at",
    ],
}

# None → no level filter (include all)
_ROLE_FILTERS: Dict[str, Optional[List[str]]] = {
    "security":  ["ERROR", "CRITICAL"],
    "developer": ["ERROR", "WARNING", "CRITICAL"],
    "admin":     None,
    "auditor":   None,
    "analyst":   None,
}


# ── Classifier ────────────────────────────────────────────────────────────────

class LogClassifier:
    """Detects log types and produces role-scoped views of log records."""

    # ── Type detection ────────────────────────────────────────────────────────

    def detect_log_type(self, log: Dict[str, Any]) -> LogType:
        """Classify a single log record into a LogType."""
        error_level = (log.get("error_level") or "").upper()
        risk_level = (log.get("risk_level") or "").upper()

        if error_level == "CRITICAL" or risk_level == "CRITICAL":
            return LogType.SECURITY
        if error_level == "ERROR":
            return LogType.ERROR
        if error_level == "WARNING":
            return LogType.WARNING
        if error_level == "DEBUG":
            return LogType.DEBUG
        return LogType.INFO

    def is_security_event(self, log: Dict[str, Any]) -> bool:
        return self.detect_log_type(log) in (LogType.SECURITY, LogType.ERROR)

    def summary(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count records per LogType across a list of logs."""
        counts: Dict[str, int] = {t.value: 0 for t in LogType}
        for log in logs:
            counts[self.detect_log_type(log).value] += 1
        return counts

    # ── Role-based classification ─────────────────────────────────────────────

    def classify_by_role(
        self, logs: List[Dict[str, Any]], role: Role
    ) -> List[Dict[str, Any]]:
        """Filter and project records for the given role."""
        allowed_levels = _ROLE_FILTERS[role.value]
        fields = _ROLE_FIELDS[role.value]

        result = []
        for log in logs:
            flat = self._flatten(log)
            if allowed_levels is not None:
                if (flat.get("error_level") or "").upper() not in allowed_levels:
                    continue
            flat["log_type"] = self.detect_log_type(flat).value
            result.append(self._project(flat, fields))
        return result

    def get_role_fields(self, role: Role) -> Optional[List[str]]:
        return _ROLE_FIELDS[role.value]

    def get_role_format(self, role: Role) -> str:
        return _ROLE_FORMAT[role.value]

    def get_role_filter(self, role: Role) -> Optional[List[str]]:
        return _ROLE_FILTERS[role.value]

    @staticmethod
    def available_roles() -> List[str]:
        return [r.value for r in Role]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _flatten(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Merge nested payload fields into the top-level dict."""
        flat = {k: v for k, v in log.items() if k != "payload"}
        for k, v in (log.get("payload") or {}).items():
            flat.setdefault(k, v)
        return flat

    def _project(
        self, log: Dict[str, Any], fields: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Keep only the specified fields; keep all when fields is None."""
        if fields is None:
            return log
        return {k: log[k] for k in fields if k in log}
