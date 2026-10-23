"""
BRENDA client: keyless by default, SOAP API when you have a BRENDA login.

Backends (environment variable BRENDA_BACKEND):
    auto (default) - SOAP when BRENDA_EMAIL and BRENDA_PASSWORD are set, otherwise the
                     keyless web backend (scripts/brenda_web.py), noted once on stderr.
    web            - BRENDA's public enzyme pages + the DSMZ SPARQL endpoint; no login.
    soap           - the official SOAP API; fails with a clear error if the login is
                     missing instead of answering from the web pages.
get_km_values() and get_reactions() return the same "field*value#field*value" strings
on both backends, so the parsers in brenda_queries work unchanged.

SOAP authentication (optional):
    The SOAP API needs a free BRENDA account. Provide BRENDA_EMAIL / BRENDA_PASSWORD
    via a .env file or environment variables. The password is SHA-256 hashed before
    being sent, per the BRENDA SOAP specification.

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
    nothing for the keyless web backend; `uv pip install zeep` for SOAP

Usage:
    from scripts.brenda_client import get_km_values, get_reactions

    km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")
    reactions = get_reactions("1.1.1.1")
"""

import hashlib
import os
import sys
import time
from pathlib import Path
from typing import List

try:  # brenda_web sits next to this file
    from scripts import brenda_web
except ImportError:  # pragma: no cover - module-path fallback
    import brenda_web

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
            "BRENDA SOAP login missing: set BRENDA_EMAIL and BRENDA_PASSWORD (free account at "
            "https://www.brenda-enzymes.org/register.php), or use the keyless web backend "
            "(unset BRENDA_BACKEND or set it to 'web'; see scripts/brenda_web.py)."
        )
    return email, password


_NOTED = False


def active_backend() -> str:
    """'soap' or 'web' per BRENDA_BACKEND (auto: soap only when a login is configured)."""
    global _NOTED
    load_env_from_file()
    choice = os.environ.get("BRENDA_BACKEND", "auto").strip().lower() or "auto"
    if choice not in ("auto", "soap", "web"):
        raise RuntimeError(f"BRENDA_BACKEND must be auto, soap or web (got {choice!r})")
    if choice == "soap":
        _get_credentials()  # raises with the keyless alternative when missing
        return "soap"
    if choice == "auto":
        has_login = (os.environ.get("BRENDA_EMAIL") or os.environ.get("BRENDA_EMIAL")) \
            and os.environ.get("BRENDA_PASSWORD")
        if has_login:
            return "soap"
    if not _NOTED:
        print("BRENDA login not set: using the keyless web backend (public enzyme pages + "
              "SPARQL).", file=sys.stderr)
        _NOTED = True
    return "web"


def _hash_password(password: str) -> str:
    """Return the SHA-256 hex digest of a plaintext password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_client():
    """Initialize (once) and return the singleton zeep SOAP client."""
    global _CLIENT
    if _CLIENT is None:
        from zeep import Client, Settings  # only the SOAP backend needs zeep
        from zeep.transports import Transport

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
    if active_backend() != "soap":
        raise RuntimeError(
            f"call_brenda({action!r}) is SOAP-only and needs BRENDA_EMAIL/BRENDA_PASSWORD. "
            "Keyless: brenda_web.get_table(ec, table) covers the same BRENDA tables.")
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
    if active_backend() == "web":
        if ec_number in ("*", ""):
            raise RuntimeError(
                "The keyless web backend reads one EC page at a time. Find EC numbers for a "
                "substrate first: brenda_web.enzymes_for(substrate) (SPARQL), then call "
                "get_km_values(ec, substrate=...) per EC.")
        _, rows = brenda_web.get_table(
            ec_number, "km", substrate=None if substrate == "*" else substrate,
            organism=None if organism == "*" else organism)
        return [_web_entry(r, kmValue=r.get("VALUE", ""), kmValueMaximum="",
                           substrate=r.get("SUBSTRATE", ""), ligandStructureId="")
                for r in rows]
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
    if active_backend() == "web":
        pattern = "" if reaction == "*" else reaction.strip("*")
        if ec_number in ("*", ""):
            if not pattern:
                raise RuntimeError("Give an EC number or a compound pattern on the web backend.")
            return [f"ecNumber*{r['ec']}#reaction*{r['equation']}#commentary*#literature*#organism*"
                    for r in brenda_web.reactions_for(pattern)]
        _, rows = brenda_web.get_table(ec_number, "substrate",
                                       organism=None if organism == "*" else organism)
        entries = [_web_entry(r, reaction=f"{r.get('SUBSTRATE', '')} = {r.get('PRODUCT', '')}")
                   for r in rows]
        return [e for e in entries if pattern.lower() in e.lower()] if pattern else entries
    parameters = [
        f"ecNumber*{ec_number}",
        f"organism*{'' if organism == '*' else organism}",
        f"reaction*{'' if reaction == '*' else reaction}",
        "commentary*",
        "literature*",
    ]
    return split_entries(call_brenda("getReaction", parameters))


def _web_entry(row: dict, **fields) -> str:
    """Render a brenda_web table row in the SOAP 'field*value#...' entry format."""
    base = {"ecNumber": row.get("EC", ""), **fields,
            "organism": row.get("ORGANISM", ""), "commentary": row.get("COMMENTARY", ""),
            "literature": row.get("LITERATURE", "")}
    return "#".join(f"{k}*{str(v).replace('#', ' ').replace('*', ' ')}" for k, v in base.items())
