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

Calling convention (brenda_zeep.wsdl):
    Every operation takes SEPARATE string arguments in WSDL order —
    email, password-hash, then "field*value" tokens — i.e.
    ``client.service.getKmValue(email, pw_hash, "ecNumber*1.1.1.1", ...)``.
    Passing one comma-joined string (the pre-zeep SOAPpy style) fails in zeep
    with "Missing element password". Results come back as lists of typed
    objects; split_entries() renders each one as the legacy
    "field*value#field*value" string that the parsers in brenda_queries expect.

Usage policy:
    BRENDA asks for at most one request per second; call_brenda() enforces it.
    Data are licensed CC BY 4.0 — cite BRENDA when you use them.

Installation:
    uv pip install zeep requests

Usage:
    from scripts.brenda_client import get_km_values, get_reactions

    km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")
    reactions = get_reactions("1.1.1.1")
"""

import hashlib
import os
import time
from pathlib import Path
from typing import List

from zeep import Client, Settings
from zeep.transports import Transport

WSDL_URL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"

_CLIENT = None  # singleton zeep Client
_MIN_INTERVAL = 1.0  # seconds between calls (BRENDA: max one request per second)
_last_call = 0.0


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


def call_brenda(action: str, parameters: List[str]):
    """Execute a BRENDA SOAP action.

    Args:
        action: SOAP method name, e.g. "getKmValue" or "getReaction".
        parameters: Field tokens in the operation's WSDL order, such as
            ["ecNumber*1.1.1.1", "organism*Homo sapiens", "kmValue*", ...].
            Email and the SHA-256-hashed password are prepended automatically.

    Returns:
        The raw zeep response (usually a list of typed result objects).
    """
    global _last_call
    email, password = _get_credentials()
    hashed = _hash_password(password)
    client = _get_client()
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    method = getattr(client.service, action)
    try:
        # zeep maps positional arguments onto the WSDL message parts in order.
        return method(email, hashed, *parameters)
    finally:
        _last_call = time.monotonic()


def _entry_to_string(item) -> str:
    """Render one zeep result object as a legacy 'field*value#field*value' string."""
    from zeep.helpers import serialize_object

    data = serialize_object(item)
    if not isinstance(data, dict):
        return str(data)
    parts = []
    for key, value in data.items():
        if value is None:
            value = ""
        elif isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        parts.append(f"{key}*{value}")
    return "#".join(parts)


def split_entries(return_text) -> List[str]:
    """Normalize a BRENDA response into a list of entry strings.

    The zeep WSDL returns a list of typed objects; each is rendered as the
    legacy "field*value#field*value" string. Plain-string responses (older
    SOAP clients) separate records with '!'. Returns [] for empty input.
    """
    if not return_text:
        return []
    if isinstance(return_text, (list, tuple)):
        entries = [_entry_to_string(item) for item in return_text]
        return [entry for entry in entries if entry.strip()]
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
    # WSDL order: ecNumber, organism, kmValue, kmValueMaximum, substrate,
    # commentary, ligandStructureId, literature.
    parameters = [
        f"ecNumber*{ec_number}",
        f"organism*{'' if organism == '*' else organism}",
        "kmValue*",
        "kmValueMaximum*",
        f"substrate*{'' if substrate == '*' else substrate}",
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
