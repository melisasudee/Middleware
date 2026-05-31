import csv
import json
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Dict, List


class OutputFormatter(ABC):
    @abstractmethod
    def format(self, logs: List[Dict[str, Any]]) -> str:
        pass


class JSONFormatter(OutputFormatter):
    def format(self, logs: List[Dict[str, Any]]) -> str:
        return json.dumps(logs, indent=2, ensure_ascii=False)


class CSVFormatter(OutputFormatter):
    def format(self, logs: List[Dict[str, Any]]) -> str:
        if not logs:
            return ""

        output = StringIO()
        headers = sorted({key for item in logs for key in item.keys()})
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for item in logs:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in item.items()})
        return output.getvalue()


class HTMLFormatter(OutputFormatter):
    def format(self, logs: List[Dict[str, Any]]) -> str:
        if not logs:
            return "<p>Veri bulunamadı.</p>"

        headers = sorted({key for item in logs for key in item.keys()})
        html = [
            "<html><head><meta charset='utf-8'><title>Log Export</title>",
            "<style>body{font-family:Arial,sans-serif;background:#f7f9fd;color:#1f2937;}table{border-collapse:collapse;width:100%;}th,td{padding:10px;border:1px solid #d1d5db;}th{background:#1f2937;color:#fff;}</style>",
            "</head><body>",
            "<h1>Log Export</h1>",
            "<table>",
            "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>",
            "<tbody>",
        ]

        for item in logs:
            row = "<tr>" + "".join(f"<td>{item.get(h, '')}</td>" for h in headers) + "</tr>"
            html.append(row)

        html.extend(["</tbody>", "</table>", "</body></html>"])
        return "\n".join(html)


class FormatterFactory:
    @staticmethod
    def get_formatter(format_type: str) -> OutputFormatter:
        format_type = format_type.lower()
        if format_type == "json":
            return JSONFormatter()
        if format_type == "csv":
            return CSVFormatter()
        if format_type == "html":
            return HTMLFormatter()
        raise ValueError(f"Bilinmeyen formatter: {format_type}")


class FormatterStrategy:
    def __init__(self, style: str = "json"):
        self.formatter = FormatterFactory.get_formatter(style)

    def format(self, data: List[Dict[str, Any]]) -> str:
        return self.formatter.format(data)
