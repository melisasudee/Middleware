import csv
import html as html_lib
import json
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Dict, List


class Formatter(ABC):
    """Strategy interface: every concrete formatter must implement these contracts."""

    @abstractmethod
    def format(self, data: List[Dict[str, Any]]) -> str:
        """Convert log records to the target string representation."""

    @abstractmethod
    def validate(self, data: List[Dict[str, Any]]) -> bool:
        """Return True if data can be handled by this formatter."""

    @abstractmethod
    def get_content_type(self) -> str:
        """MIME type for HTTP Content-Type header."""

    @abstractmethod
    def get_file_extension(self) -> str:
        """File extension used when saving the output."""

    def get_name(self) -> str:
        return self.__class__.__name__

    def safe_format(self, data: List[Dict[str, Any]]) -> str:
        """Validate then format; raises ValueError on invalid input."""
        if not self.validate(data):
            raise ValueError(f"{self.get_name()}: data failed validation")
        return self.format(data)


class JSONFormatter(Formatter):
    """Concrete strategy: serialises log records as indented JSON."""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    def format(self, data: List[Dict[str, Any]]) -> str:
        return json.dumps(data, indent=self._indent, ensure_ascii=self._ensure_ascii)

    def format_compact(self, data: List[Dict[str, Any]]) -> str:
        """Single-line JSON, no whitespace."""
        return json.dumps(data, ensure_ascii=self._ensure_ascii)

    def format_pretty(self, data: List[Dict[str, Any]], indent: int = 4) -> str:
        """JSON with a custom indentation level."""
        return json.dumps(data, indent=indent, ensure_ascii=self._ensure_ascii)

    def format_single(self, record: Dict[str, Any]) -> str:
        """Format a single log record instead of a list."""
        return json.dumps(record, indent=self._indent, ensure_ascii=self._ensure_ascii)

    def validate(self, data: List[Dict[str, Any]]) -> bool:
        return isinstance(data, list)

    def get_content_type(self) -> str:
        return "application/json"

    def get_file_extension(self) -> str:
        return ".json"


class CSVFormatter(Formatter):
    """Concrete strategy: serialises log records as comma-separated values."""

    def __init__(self, delimiter: str = ",", include_headers: bool = True) -> None:
        self._delimiter = delimiter
        self._include_headers = include_headers

    def _extract_headers(self, data: List[Dict[str, Any]]) -> List[str]:
        """Collect every unique field name across all records, sorted."""
        return sorted({key for row in data for key in row})

    def _serialize_cell(self, value: Any) -> str:
        """Flatten nested objects to JSON strings; convert None to empty string."""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def format(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return ""
        headers = self._extract_headers(data)
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=headers,
            delimiter=self._delimiter,
            extrasaction="ignore",
        )
        if self._include_headers:
            writer.writeheader()
        for row in data:
            writer.writerow({h: self._serialize_cell(row.get(h)) for h in headers})
        return output.getvalue()

    def format_tsv(self, data: List[Dict[str, Any]]) -> str:
        """Tab-separated variant."""
        original = self._delimiter
        self._delimiter = "\t"
        result = self.format(data)
        self._delimiter = original
        return result

    def validate(self, data: List[Dict[str, Any]]) -> bool:
        return isinstance(data, list) and all(isinstance(r, dict) for r in data)

    def get_content_type(self) -> str:
        return "text/csv"

    def get_file_extension(self) -> str:
        return ".csv"


class HTMLFormatter(Formatter):
    """Concrete strategy: serialises log records as a styled HTML table."""

    _STYLE = (
        "body{font-family:system-ui,sans-serif;background:#f7f9fd;"
        "color:#1f2937;padding:24px;margin:0}"
        "h1{margin-bottom:16px;font-size:1.3rem;color:#111827}"
        "p.meta{margin-bottom:12px;font-size:.85rem;color:#6b7280}"
        "table{border-collapse:collapse;width:100%;font-size:.82rem}"
        "th,td{padding:8px 12px;border:1px solid #d1d5db;text-align:left;vertical-align:top}"
        "th{background:#1e293b;color:#f1f5f9;white-space:nowrap}"
        "tr:nth-child(even){background:#f1f5f9}"
        "td{max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
    )

    def _build_header_row(self, headers: List[str]) -> str:
        cells = "".join(f"<th>{html_lib.escape(h)}</th>" for h in headers)
        return f"<thead><tr>{cells}</tr></thead>"

    def _build_data_rows(self, data: List[Dict[str, Any]], headers: List[str]) -> str:
        rows = []
        for row in data:
            cells = "".join(
                f"<td>{html_lib.escape(str(row.get(h, '')))}</td>"
                for h in headers
            )
            rows.append(f"<tr>{cells}</tr>")
        return "<tbody>" + "".join(rows) + "</tbody>"

    def _build_document(self, body: str, record_count: int) -> str:
        return (
            f"<!DOCTYPE html><html lang='en'>"
            f"<head><meta charset='utf-8'><title>Log Export</title>"
            f"<style>{self._STYLE}</style></head>"
            f"<body><h1>Log Export</h1>"
            f"<p class='meta'>{record_count} record(s)</p>"
            f"{body}</body></html>"
        )

    def format(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return self._build_document("<p>No records found.</p>", 0)
        headers = sorted({key for row in data for key in row})
        table = (
            f"<table>"
            f"{self._build_header_row(headers)}"
            f"{self._build_data_rows(data, headers)}"
            f"</table>"
        )
        return self._build_document(table, len(data))

    def validate(self, data: List[Dict[str, Any]]) -> bool:
        return isinstance(data, list) and all(isinstance(r, dict) for r in data)

    def get_content_type(self) -> str:
        return "text/html"

    def get_file_extension(self) -> str:
        return ".html"


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: Dict[str, Formatter] = {
    "json": JSONFormatter(),
    "csv": CSVFormatter(),
    "html": HTMLFormatter(),
}


# ── Context ───────────────────────────────────────────────────────────────────

class SelectiveFormatter:
    """Context: holds a reference to a Formatter strategy and delegates to it.

    The strategy can be swapped at any point without changing the caller.
    """

    def __init__(self, format_type: str = "json") -> None:
        self._strategy: Formatter = self._resolve(format_type)

    @staticmethod
    def _resolve(format_type: str) -> Formatter:
        strategy = _REGISTRY.get(format_type.lower())
        if strategy is None:
            raise ValueError(
                f"Unknown format '{format_type}'. "
                f"Available: {SelectiveFormatter.available_formats()}"
            )
        return strategy

    def set_strategy(self, format_type: str) -> None:
        """Swap the active strategy at runtime."""
        self._strategy = self._resolve(format_type)

    def format(self, data: List[Dict[str, Any]]) -> str:
        return self._strategy.format(data)

    def validate(self, data: List[Dict[str, Any]]) -> bool:
        return self._strategy.validate(data)

    def safe_format(self, data: List[Dict[str, Any]]) -> str:
        return self._strategy.safe_format(data)

    def get_content_type(self) -> str:
        return self._strategy.get_content_type()

    def get_file_extension(self) -> str:
        return self._strategy.get_file_extension()

    @staticmethod
    def available_formats() -> List[str]:
        return list(_REGISTRY)

    @staticmethod
    def register(name: str, formatter: Formatter) -> None:
        """Register a new strategy at runtime — Open/Closed principle."""
        if not isinstance(formatter, Formatter):
            raise TypeError("formatter must be a Formatter subclass")
        _REGISTRY[name.lower()] = formatter


# ── Backward-compatible factory ───────────────────────────────────────────────

class FormatterFactory:
    """Thin facade kept for backward compatibility; delegates to the registry."""

    @staticmethod
    def get_formatter(format_type: str) -> Formatter:
        return SelectiveFormatter._resolve(format_type)


# ── Role-based formatter ──────────────────────────────────────────────────────

class RoleBasedFormatter:
    """Selects a Formatter strategy and renders output for a given Role.

    The 'auditor' role produces a JSON envelope that embeds both a CSV
    string and the full JSON record list so consumers can choose either.
    """

    def format(self, data: List[Dict[str, Any]], fmt: str, role_name: str) -> str:
        if fmt == "dual":
            return self._format_dual(data, role_name)
        return FormatterFactory.get_formatter(fmt).format(data)

    def get_content_type(self, fmt: str) -> str:
        if fmt == "dual":
            return "application/json"
        return FormatterFactory.get_formatter(fmt).get_content_type()

    def get_file_extension(self, fmt: str) -> str:
        if fmt == "dual":
            return ".json"
        return FormatterFactory.get_formatter(fmt).get_file_extension()

    def _format_dual(self, data: List[Dict[str, Any]], role_name: str) -> str:
        """Produce a JSON envelope containing both CSV and JSON representations."""
        csv_output = FormatterFactory.get_formatter("csv").format(data)
        return json.dumps(
            {
                "role": role_name,
                "record_count": len(data),
                "formats": {
                    "csv": csv_output,
                    "json": data,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
