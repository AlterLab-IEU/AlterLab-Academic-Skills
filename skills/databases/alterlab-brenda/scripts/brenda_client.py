"""
BRENDA SOAP API client.

Thin wrapper around the official BRENDA SOAP API (https://www.brenda-enzymes.org/)
using the zeep SOAP client. Implements credential loading, SHA-256 password
hashing, a singleton SOAP client, and the convenience query functions used
throughout this skill.

Authentication:
    BRENDA requires a registered account. Provide credentials via a .env file
    (BRENDA_EMAIL / BRENDA_PASSWORD) or environment variables. The password is
    SHA-256 hashed before being sent, per the BRENDA SOAP specification.

Installation:
    uv pip install zeep requests

Usage:
    from scripts.brenda_client import get_km_values, get_reactions

    km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")
    reactions = get_reactions("1.1.1.1")
"""

import hashlib
import os
from pathlib import Path
from typing import List

from zeep import Client, Settings
from zeep.transports import Transport

WSDL_URL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"

_CLIENT = None  # singleton zeep Client


def load_env_from_file(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Existing environment variables are not overwritten. Lines that are blank
    or start with '#' are ignored.
    """
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_credentials() -> tuple:
    """Return (email, password) from the environment.

    Falls back to the legacy misspelled BRENDA_EMIAL variable for the email.
    Raises RuntimeError if either credential is missing.
    """
    load_env_from_file()
    email = os.environ.get("BRENDA_EMAIL") or os.environ.get("BRENDA_EMIAL")
    password = os.environ.get("BRENDA_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "BRENDA credentials missing. Set BRENDA_EMAIL and BRENDA_PASSWORD "
            "in your environment or a .env file."
        )
    return email, password


def _hash_password(password: str) -> str:
    """Return the SHA-256 hex digest of a plaintext password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_client() -> Client:
    """Initialize (once) and return the singleton zeep SOAP client."""
    global _CLIENT
    if _CLIENT is None:
        settings = Settings(strict=False, xml_huge_tree=True)
        transport = Transport(timeout=60)
        _CLIENT = Client(WSDL_URL, settings=settings, transport=transport)
    return _CLIENT


def call_brenda(action: str, parameters: List[str]) -> str:
    """Execute a BRENDA SOAP action.

    Args:
        action: SOAP method name, e.g. "getKmValue" or "getReaction".
        parameters: Ordered field tokens such as
            ["ecNumber*1.1.1.1", "organism*Homo sapiens", "substrate*ethanol"].
            Email and the SHA-256-hashed password are prepended automatically.

    Returns:
        The raw response string from BRENDA.
    """
    email, password = _get_credentials()
    hashed = _hash_password(password)
    client = _get_client()
    payload = ",".join([email, hashed, *parameters])
    method = getattr(client.service, action)
    return method(payload)


def split_entries(return_text) -> List[str]:
    """Normalize a BRENDA response into a list of entry strings.

    BRENDA separates records with '!'. Handles raw strings as well as list/
    object responses, returning an empty list for empty input.
    """
    if not return_text:
        return []
    if isinstance(return_text, (list, tuple)):
        return [str(item) for item in return_text if str(item).strip()]
    return [entry for entry in str(return_text).split("!") if entry.strip()]


def get_km_values(ec_number: str, organism: str = "*", substrate: str = "*") -> List[str]:
    """Retrieve Km values for an enzyme.

    Args:
        ec_number: Enzyme Commission number (e.g., "1.1.1.1").
        organism: Organism name; "*" matches all organisms.
        substrate: Substrate name; "*" matches all substrates.

    Returns:
        List of raw BRENDA Km data entries.
    """
    parameters = [
        f"ecNumber*{ec_number}",
        f"organism*{'' if organism == '*' else organism}",
        f"substrate*{'' if substrate == '*' else substrate}",
        "kmValue*",
        "kmValueMaximum*",
        "commentary*",
        "ligandStructureId*",
        "literature*",
    ]
    return split_entries(call_brenda("getKmValue", parameters))


def get_reactions(ec_number: str, organism: str = "*", reaction: str = "*") -> List[str]:
    """Retrieve reaction data for an enzyme.

    Args:
        ec_number: Enzyme Commission number (e.g., "1.1.1.1").
        organism: Organism name; "*" matches all organisms.
        reaction: Reaction pattern; "*" matches all reactions.

    Returns:
        List of raw BRENDA reaction data entries.
    """
    parameters = [
        f"ecNumber*{ec_number}",
        f"organism*{'' if organism == '*' else organism}",
        f"reaction*{'' if reaction == '*' else reaction}",
        "commentary*",
        "literature*",
    ]
    return split_entries(call_brenda("getReaction", parameters))
