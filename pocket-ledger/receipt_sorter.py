"""Local receipt extraction helpers and file organization."""

from __future__ import annotations

import base64
import csv
import io
import json
import re
import urllib.error
import urllib.request
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

CSV_FIELDS = (
    "vendor",
    "date",
    "amount",
    "currency",
    "category",
    "description",
    "source_file",
    "sorted_path",
)

CATEGORIES = (
    "Meals",
    "Travel",
    "Office Supplies",
    "Software",
    "Utilities",
    "Professional Services",
    "Other",
)

OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def _clean_text(value: Any, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:limit]


def _safe_component(value: str, fallback: str) -> str:
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip(" ._")
    return value[:80] or fallback


def parse_receipt_json(content: str) -> dict[str, str]:
    """Parse and normalize a model response to the receipt CSV schema."""
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"The model did not return valid JSON: {exc.msg}") from exc
    if not isinstance(result, dict):
        raise ValueError("The model response must be a JSON object.")

    raw_date = _clean_text(result.get("date"), 10)
    if raw_date:
        try:
            raw_date = date.fromisoformat(raw_date).isoformat()
        except ValueError:
            raw_date = ""

    raw_amount = result.get("amount")
    amount = ""
    if raw_amount not in (None, ""):
        try:
            parsed_amount = Decimal(str(raw_amount).replace(",", "").replace("$", "").strip())
            if parsed_amount.is_finite() and parsed_amount >= 0:
                amount = format(parsed_amount, "f")
        except (InvalidOperation, ValueError):
            amount = ""

    category = _clean_text(result.get("category"), 40)
    category = next((item for item in CATEGORIES if item.casefold() == category.casefold()), "Other")
    currency = _clean_text(result.get("currency"), 3).upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        currency = ""

    return {
        "vendor": _clean_text(result.get("vendor"), 100) or "Unknown vendor",
        "date": raw_date,
        "amount": amount,
        "currency": currency,
        "category": category,
        "description": _clean_text(result.get("description"), 200),
    }


def extract_receipt(
    file_name: str,
    file_bytes: bytes,
    model: str = "gemma3:4b",
) -> dict[str, str]:
    """Extract receipt fields using Ollama running on this machine."""
    suffix = Path(file_name).suffix.lower()
    images: list[str] = []
    receipt_text = ""

    if suffix == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PDF support requires PyMuPDF. Install requirements.txt and retry.") from exc

        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
            receipt_text = "\n".join(page.get_text() for page in document).strip()
            if not receipt_text and len(document):
                pixmap = document[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                images.append(base64.b64encode(pixmap.tobytes("png")).decode("ascii"))
            document.close()
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc
    else:
        images.append(base64.b64encode(file_bytes).decode("ascii"))

    prompt = (
        "Extract the purchase details from this receipt or invoice. Return only one JSON object with "
        'exactly these keys: "vendor", "date", "amount", "currency", "category", "description". '
        'Use an ISO date (YYYY-MM-DD), a plain non-negative numeric amount, and a three-letter '
        "currency code. Use an empty string when a value is unreadable. Choose category from "
        f"{', '.join(CATEGORIES)}. Never guess missing values. Keep description brief.\n\n"
        f"PDF text, if available:\n{receipt_text[:12000]}"
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": images}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 128},
    }
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(
            f"Could not reach local Ollama at {OLLAMA_CHAT_URL}: {reason}. "
            f"Start Ollama and pull the model '{model}'."
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama did not return a valid response: {exc}") from exc

    try:
        return parse_receipt_json(response_data["message"]["content"])
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Ollama returned a response without message content.") from exc


def organize_receipt(
    output_dir: Path,
    file_name: str,
    file_bytes: bytes,
    receipt: dict[str, str],
) -> str:
    """Copy a receipt to category/year folders without overwriting existing files."""
    receipt_date = receipt["date"]
    year = receipt_date[:4] if receipt_date else "Undated"
    vendor = _safe_component(receipt["vendor"], "Unknown_vendor")
    amount = _safe_component(receipt["amount"], "amount-unknown")
    currency = _safe_component(receipt["currency"], "currency-unknown")
    original_suffix = Path(file_name).suffix.lower()
    extension = original_suffix if re.fullmatch(r"\.[a-z0-9]{1,10}", original_suffix) else ".bin"
    filename = f"{vendor}_{receipt_date or 'undated'}_{amount}_{currency}{extension}"
    destination_dir = output_dir / _safe_component(receipt["category"], "Other") / year
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / filename

    counter = 2
    while destination.exists():
        destination = destination_dir / f"{Path(filename).stem}_{counter}{extension}"
        counter += 1

    destination.write_bytes(file_bytes)
    return str(destination.relative_to(output_dir))


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def write_csv(output_dir: Path, rows: list[dict[str, str]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "receipts.csv"
    csv_path.write_bytes(csv_bytes(rows))
    return csv_path
