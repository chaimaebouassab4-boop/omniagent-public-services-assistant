"""Build a synthetic PDF specimen to visually verify the receipt template."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from app.services.case_receipt import render_case_receipt


def main() -> None:
    sample = SimpleNamespace(
        public_id=41,
        reference_number="MA-2026-000041",
        applicant_name="Salma Bennani",
        user=SimpleNamespace(full_name="Salma Bennani"),
        service=SimpleNamespace(name_fr="Certificat de résidence"),
        created_at=datetime(2026, 9, 24, 10, 30),
        status="READY_FOR_PICKUP",
    )
    output = Path(__file__).resolve().parents[2] / "output" / "pdf" / "feature3-receipt-sample.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render_case_receipt(sample))
    print(output)


if __name__ == "__main__":
    main()
