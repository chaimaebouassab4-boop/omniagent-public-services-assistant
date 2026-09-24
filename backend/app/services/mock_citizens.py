"""Deterministic synthetic Moroccan profiles for demos and automated verification."""

from dataclasses import asdict, dataclass
from random import Random
from pathlib import Path
import json

MOCK_PROFILE_PROMPT = """Generate synthetic Moroccan citizen test profiles as JSON.
Fields: full_name, cin, phone, address, city, cnss_number, cnss_status.
Use plausible Casablanca or Rabat addresses and a Moroccan CIN pattern (two letters plus
six digits). Every value must be fictional; never copy a real person's identity or imply
that a CIN/CNSS record has been checked against a government registry.
"""

_FIRST = ("Salma", "Youssef", "Amina", "Mehdi", "Imane", "Omar", "Nadia", "Rachid")
_LAST = ("El Amrani", "Bennani", "Alaoui", "Idrissi", "Berrada", "Tazi")
_ADDRESSES = {
    "Casablanca": ("Rue Al Massira, Maarif", "Boulevard Zerktouni, Bourgogne", "Rue des Fleurs, Sidi Maarouf"),
    "Rabat": ("Avenue Fal Ould Oumeir, Agdal", "Rue Oued Moulouya, Hassan", "Avenue Mohammed VI, Souissi"),
}


@dataclass(frozen=True)
class MockCitizen:
    full_name: str
    cin: str
    phone: str
    address: str
    city: str
    cnss_number: str
    cnss_status: str
    synthetic: bool = True


def generate_mock_citizens(count: int = 10, seed: int = 2026) -> list[dict]:
    if not 1 <= count <= 1000:
        raise ValueError("count must be between 1 and 1000")
    rng = Random(seed)
    profiles = []
    used_cins: set[str] = set()
    for index in range(count):
        city = "Casablanca" if index % 2 == 0 else "Rabat"
        cin = f"{rng.choice(('BK', 'AB', 'BE', 'JB'))}{rng.randrange(100000, 1000000)}"
        while cin in used_cins:
            cin = f"{rng.choice(('BK', 'AB', 'BE', 'JB'))}{rng.randrange(100000, 1000000)}"
        used_cins.add(cin)
        profile = MockCitizen(
            full_name=f"{rng.choice(_FIRST)} {rng.choice(_LAST)}",
            cin=cin,
            phone=f"+2126{rng.randrange(10000000, 99999999)}",
            address=f"{rng.randrange(1, 120)}, {rng.choice(_ADDRESSES[city])}",
            city=city,
            cnss_number=f"{rng.randrange(100000000, 999999999)}",
            cnss_status=rng.choice(("active", "inactive", "not_registered")),
        )
        profiles.append(asdict(profile))
    return profiles


def load_sample_profiles() -> list[dict]:
    sample_path = Path(__file__).resolve().parents[2] / "data" / "mock_citizens.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


def verify_mock_profile(field: str, value: str) -> dict:
    if field not in {"cin", "cnss_number"}:
        raise ValueError("Unsupported mock verification field")
    match = next((profile for profile in load_sample_profiles() if profile[field].upper() == value.strip().upper()), None)
    return {
        "valid": match is not None,
        "name": match["full_name"] if match else None,
        "cnss_status": match["cnss_status"] if match else None,
        "synthetic": True,
    }
