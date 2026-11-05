#!/usr/bin/env python3
"""Deterministic checks on the files an eval's answer arm was asked to produce.

An eval in ``skills/<domain>/<skill>/evals/evals.json`` may declare::

    "artifact_checks": [
      {"path": "out/figure.png", "type": "png",
       "description": "the multi-panel figure",          # optional; shown to both arms
       "checks": [{"kind": "png_dpi", "expected": 300, "tolerance": 1},
                  {"kind": "png_min_size", "min_width": 900, "min_height": 600}]}
    ]

``scripts/run_evals.py --behavioral`` tells both arms (identically) to save each declared
file at its path in their working directory, then, after every run and BEFORE the temporary
workspace is deleted, calls :func:`check_artifacts`. Each declared file is inspected, copied
into the results directory, hashed, and graded. ``exists`` and ``parseable`` are always
checked first; every other check is listed by the eval author. Expected values (``value``,
``expected``, ``tolerance``, ``min`` ...) come from the eval file only — never from the
model's output — and the eval file is never copied into an arm's workspace.

A missing, unreadable, symlinked or unparseable file fails every check declared for it, so it
can never count as completed artifact work.

Check kinds (``kind``) and the types they apply to:

=================  =========================  ================================================
kind               types                      parameters
=================  =========================  ================================================
exists             all                        —
parseable          all                        —   (type-specific parse; see ``_parse``)
json_keys          json                       keys: [str], path?: dotted path to an object
json_path_equals   json                       path: dotted path, value: any JSON value
csv_columns        csv                        columns: [str] (header, case-insensitive)
min_rows           csv json bib md txt        min: int, max?: int, path? (json array)
number_within      json csv                   expected: number, tolerance: number >= 0,
                                              json: path; csv: column + (row | match)
contains_text      json csv md txt bib pptx   text: str | [str] (any one, case-insensitive)
                   pdf (needs pypdf)
png_min_size       png                        min_width: int, min_height: int
png_dpi            png                        expected: number, tolerance: number >= 0
pdf_min_pages      pdf                        min: int
pptx_min_slides    pptx                       min: int
=================  =========================  ================================================

Rows are data rows (CSV header excluded), array items (JSON), entries (BibTeX), or
non-blank lines (md/txt). Dotted JSON paths use integer segments for array indices
(``entries.0.verdict``). Standard library only; ``pypdf`` is used for PDF page counts and
text when importable (a regex fallback counts uncompressed page objects).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import shutil
import struct
import zipfile
import zlib
from pathlib import Path, PurePosixPath

TYPES = ("json", "csv", "png", "pdf", "pptx", "md", "txt", "bib")
_TEXT_TYPES = ("json", "csv", "md", "txt", "bib")

# kind -> (applicable types, required params, optional params)
KINDS: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "exists": (TYPES, (), ()),
    "parseable": (TYPES, (), ()),
    "json_keys": (("json",), ("keys",), ("path",)),
    "json_path_equals": (("json",), ("path", "value"), ()),
    "csv_columns": (("csv",), ("columns",), ()),
    "min_rows": (("csv", "json", "bib", "md", "txt"), ("min",), ("max", "path")),
    "number_within": (("json", "csv"), ("expected", "tolerance"), ("path", "column", "row",
                                                                    "match")),
    "contains_text": (("json", "csv", "md", "txt", "bib", "pptx", "pdf"), ("text",), ()),
    "png_min_size": (("png",), ("min_width", "min_height"), ()),
    "png_dpi": (("png",), ("expected", "tolerance"), ()),
    "pdf_min_pages": (("pdf",), ("min",), ()),
    "pptx_min_slides": (("pptx",), ("min",), ()),
}

MAX_STORE_BYTES = 25 * 1024 * 1024  # larger files are graded but not copied
PASS, FAIL, NA = "PASS", "FAIL", "NA"


# --- Declarations ---------------------------------------------------------------------
def _is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _safe_rel(path: object) -> bool:
    if not isinstance(path, str) or not path.strip() or "\\" in path or "\x00" in path:
        return False
    p = PurePosixPath(path)
    return not p.is_absolute() and ".." not in p.parts and p.parts not in ((), (".",))


def declaration_errors(decls: object, where: str = "artifact_checks") -> list[str]:
    """Human-readable problems with an eval's ``artifact_checks`` value (empty when valid)."""
    if not isinstance(decls, list):
        return [f"{where}: must be an array"]
    errs: list[str] = []
    seen: set[str] = set()
    for i, d in enumerate(decls):
        w = f"{where}/{i}"
        if not isinstance(d, dict):
            errs.append(f"{w}: must be an object")
            continue
        unknown = set(d) - {"path", "type", "description", "checks"}
        if unknown:
            errs.append(f"{w}: unknown key(s) {sorted(unknown)}")
        path, typ = d.get("path"), d.get("type")
        if not _safe_rel(path):
            errs.append(f"{w}/path: must be a relative path inside the workspace (no '..', "
                        "no leading '/')")
        elif path in seen:
            errs.append(f"{w}/path: duplicate path {path!r}")
        else:
            seen.add(path)
        if typ not in TYPES:
            errs.append(f"{w}/type: {typ!r} not in {list(TYPES)}")
        if "description" in d and (not isinstance(d["description"], str)
                                   or not d["description"].strip()):
            errs.append(f"{w}/description: must be a non-empty string")
        checks = d.get("checks", [])
        if not isinstance(checks, list):
            errs.append(f"{w}/checks: must be an array")
            continue
        for j, c in enumerate(checks):
            errs.extend(_check_errors(c, typ, f"{w}/checks/{j}"))
    return errs


def _check_errors(c: object, typ: object, w: str) -> list[str]:
    if not isinstance(c, dict):
        return [f"{w}: must be an object"]
    kind = c.get("kind")
    if kind not in KINDS:
        return [f"{w}/kind: {kind!r} not in {sorted(KINDS)}"]
    types, required, optional = KINDS[kind]
    errs = []
    if typ in TYPES and typ not in types:
        errs.append(f"{w}: {kind} does not apply to type {typ!r} (applies to {list(types)})")
    params = {k: v for k, v in c.items() if k != "kind"}
    for k in required:
        if k not in params:
            errs.append(f"{w}: {kind} needs {k!r}")
    for k in set(params) - set(required) - set(optional):
        errs.append(f"{w}: {kind} does not take {k!r}")
    for k, v in params.items():
        bad = None
        if k in ("keys", "columns"):
            bad = not (isinstance(v, list) and v and all(isinstance(x, str) and x for x in v))
        elif k == "path":
            bad = not (isinstance(v, str) and v)
        elif k in ("min", "max", "min_width", "min_height", "row"):
            bad = not (_is_int(v) and v >= 0)
        elif k == "expected":
            bad = not _is_number(v)
        elif k == "tolerance":
            bad = not (_is_number(v) and v >= 0)
        elif k == "column":
            bad = not (isinstance(v, str) and v)
        elif k == "match":
            bad = not (isinstance(v, dict) and v and all(isinstance(x, str) for x in v.values()))
        elif k == "text":
            bad = not ((isinstance(v, str) and v) or (isinstance(v, list) and v and all(
                isinstance(x, str) and x for x in v)))
        if bad:
            errs.append(f"{w}/{k}: invalid value {v!r}")
    if kind == "number_within" and typ == "json" and "path" not in params:
        errs.append(f"{w}: number_within on json needs 'path'")
    if kind == "number_within" and typ == "csv" and not (
            "column" in params and (("row" in params) != ("match" in params))):
        errs.append(f"{w}: number_within on csv needs 'column' and exactly one of 'row'/'match'")
    if kind == "min_rows" and "path" in params and typ != "json":
        errs.append(f"{w}: min_rows 'path' applies to json only")
    if kind == "min_rows" and _is_int(params.get("max")) and _is_int(params.get("min")) \
            and params["max"] < params["min"]:
        errs.append(f"{w}: min_rows max < min")
    return errs


def prompt_note(decls: list[dict]) -> str:
    """The instruction both arms get: where to save each declared deliverable. Paths, types and
    author descriptions only — never the checks or their expected values."""
    lines = []
    for d in decls:
        desc = f" — {d['description']}" if d.get("description") else ""
        lines.append(f"- {d['path']} ({d['type'].upper()} file){desc}")
    return ("\n\nSave the following output file(s) in your current working directory, at "
            "exactly these relative paths (create folders as needed):\n" + "\n".join(lines))


def clear_artifacts(workspace: Path, decls: list[dict]) -> None:
    """Remove declared outputs left by an earlier run of the same arm, so a later run can never
    be credited with an earlier run's file."""
    for d in decls:
        if not _safe_rel(d.get("path")):
            continue
        p = workspace / d["path"]
        try:
            if p.is_symlink() or p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


# --- Parsing ------------------------------------------------------------------------------
def _png_info(data: bytes) -> dict:
    """Validate a PNG down to its pixel stream; return its header facts. Raises ValueError."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("no PNG signature")
    pos, info, idat, seen_end = 8, {}, [], False
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        crc = data[pos + 8 + length:pos + 12 + length]
        if len(body) != length or len(crc) != 4:
            raise ValueError(f"truncated {ctype!r} chunk")
        if struct.unpack(">I", crc)[0] != zlib.crc32(ctype + body) & 0xFFFFFFFF:
            raise ValueError(f"bad CRC in {ctype!r} chunk")
        if pos == 8 and ctype != b"IHDR":
            raise ValueError("first chunk is not IHDR")
        if ctype == b"IHDR":
            (info["width"], info["height"], info["bit_depth"], info["color_type"], _c, _f,
             info["interlace"]) = struct.unpack(">IIBBBBB", body)
        elif ctype == b"pHYs" and length == 9:
            info["ppu_x"], info["ppu_y"], info["unit"] = struct.unpack(">IIB", body)
        elif ctype == b"IDAT":
            idat.append(body)
        elif ctype == b"IEND":
            seen_end = True
            break
        pos += 12 + length
    if not seen_end:
        raise ValueError("no IEND chunk")
    if not idat:
        raise ValueError("no image data")
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as exc:
        raise ValueError(f"pixel data does not decompress ({exc})") from exc
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(info.get("color_type", -1))
    if channels is None or not info.get("width") or not info.get("height"):
        raise ValueError("invalid IHDR")
    if info["interlace"] == 0:
        row = math.ceil(info["width"] * channels * info["bit_depth"] / 8) + 1
        if len(raw) != row * info["height"]:
            raise ValueError(f"pixel data is {len(raw)} bytes, expected {row * info['height']}")
    return info


def _pdf_pages(data: bytes) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore
        return len(PdfReader(io.BytesIO(data)).pages)
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001 — any pypdf failure means unreadable
        raise ValueError(f"pypdf could not read it ({type(exc).__name__})") from exc
    n = len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", data))
    return n if n or b"/ObjStm" not in data else None


def _pdf_text(data: bytes) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except ModuleNotFoundError:
        return None
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)


_BIB_ENTRY = re.compile(r"@\s*([A-Za-z]+)\s*[{(]\s*([^,\s{}()]*)\s*,")


def _parse(typ: str, data: bytes):
    """The parsed object for a file of ``typ``. Raises ValueError when it is not one."""
    if typ == "png":
        return _png_info(data)
    if typ == "pdf":
        if b"%PDF-" not in data[:1024]:
            raise ValueError("no %PDF- header")
        if b"%%EOF" not in data[-2048:]:
            raise ValueError("no %%EOF trailer (truncated?)")
        pages = _pdf_pages(data)
        if pages == 0:
            raise ValueError("no pages")
        return {"pages": pages}
    if typ == "pptx":
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
            names = set(zf.namelist())
            bad = zf.testzip()
        except (zipfile.BadZipFile, OSError) as exc:
            raise ValueError(f"not a zip package ({exc})") from exc
        if bad:
            raise ValueError(f"corrupt member {bad}")
        for need in ("[Content_Types].xml", "ppt/presentation.xml"):
            if need not in names:
                raise ValueError(f"missing {need}")
        slides = sorted(n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
        text = " ".join(t for n in slides for t in re.findall(
            r"<a:t>([^<]*)</a:t>", zf.read(n).decode("utf-8", "replace")))
        return {"slides": len(slides), "text": text}
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("not UTF-8 text") from exc
    if not text.strip():
        raise ValueError("empty")
    if typ == "json":
        try:
            return {"obj": json.loads(text), "text": text}
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON ({exc.msg} at line {exc.lineno})") from exc
    if typ == "csv":
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(x.strip() for x in r)]
        header = [h.strip() for h in rows[0]]
        if not any(header):
            raise ValueError("no header row")
        ragged = [i + 2 for i, r in enumerate(rows[1:]) if len(r) != len(header)]
        if ragged:
            raise ValueError(f"row(s) {ragged[:5]} do not have {len(header)} fields")
        return {"header": header, "rows": rows[1:], "text": text}
    if typ == "bib":
        entries = [m for m in _BIB_ENTRY.findall(text)
                   if m[0].lower() not in ("string", "comment", "preamble")]
        stripped = re.sub(r"\\[{}]", "", text)
        if stripped.count("{") != stripped.count("}"):
            raise ValueError("unbalanced braces")
        if not entries:
            raise ValueError("no @type{key, ...} entries")
        return {"entries": entries, "text": text}
    return {"lines": [ln for ln in text.splitlines() if ln.strip()], "text": text}  # md / txt


# --- Checks -------------------------------------------------------------------------------
def _json_at(obj, path: str | None):
    if not path:
        return obj
    for seg in path.split("."):
        if isinstance(obj, list) and re.fullmatch(r"-?\d+", seg):
            obj = obj[int(seg)]
        elif isinstance(obj, dict) and seg in obj:
            obj = obj[seg]
        else:
            raise KeyError(path)
    return obj


def _as_number(v) -> float | None:
    if _is_number(v):
        return float(v)
    if isinstance(v, str):
        try:
            f = float(v.strip())
            return f if math.isfinite(f) else None
        except ValueError:
            return None
    return None


def _check_name(c: dict) -> str:
    params = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in c.items()
                       if k != "kind")
    return f"{c['kind']}({params})" if params else c["kind"]


def _run_check(c: dict, typ: str, parsed) -> tuple[str, str]:
    kind = c["kind"]
    try:
        if kind == "json_keys":
            target = _json_at(parsed["obj"], c.get("path"))
            if not isinstance(target, dict):
                return FAIL, f"{c.get('path') or 'root'} is not an object"
            missing = [k for k in c["keys"] if k not in target]
            return (FAIL, f"missing key(s) {missing}") if missing else (PASS, "all keys present")
        if kind == "json_path_equals":
            got, want = _json_at(parsed["obj"], c["path"]), c["value"]
            ok = (got is want) if isinstance(got, bool) or isinstance(want, bool) else got == want
            return (PASS if ok else FAIL), f"{c['path']} = {json.dumps(got)[:80]}"
        if kind == "csv_columns":
            have = {h.lower() for h in parsed["header"]}
            missing = [col for col in c["columns"] if col.strip().lower() not in have]
            return (FAIL, f"missing column(s) {missing}") if missing else (PASS, "all present")
        if kind == "min_rows":
            if typ == "json":
                target = _json_at(parsed["obj"], c.get("path"))
                if not isinstance(target, list):
                    return FAIL, f"{c.get('path') or 'root'} is not an array"
                n = len(target)
            else:
                n = len({"csv": parsed.get("rows"), "bib": parsed.get("entries")}.get(typ)
                        or parsed.get("lines") or [])
            ok = n >= c["min"] and ("max" not in c or n <= c["max"])
            return (PASS if ok else FAIL), f"{n} row(s)"
        if kind == "number_within":
            if typ == "json":
                raw = _json_at(parsed["obj"], c["path"])
            else:
                col = next((i for i, h in enumerate(parsed["header"])
                            if h.lower() == c["column"].strip().lower()), None)
                if col is None:
                    return FAIL, f"no column {c['column']!r}"
                if "row" in c:
                    if c["row"] >= len(parsed["rows"]):
                        return FAIL, f"no data row {c['row']}"
                    raw = parsed["rows"][c["row"]][col]
                else:
                    idx = {h.lower(): i for i, h in enumerate(parsed["header"])}
                    row = next((r for r in parsed["rows"] if all(
                        k.lower() in idx and r[idx[k.lower()]].strip() == v
                        for k, v in c["match"].items())), None)
                    if row is None:
                        return FAIL, f"no row matching {c['match']}"
                    raw = row[col]
            got = _as_number(raw)
            if got is None:
                return FAIL, f"not a number: {str(raw)[:40]!r}"
            ok = abs(got - c["expected"]) <= c["tolerance"]
            return (PASS if ok else FAIL), f"{got:g} vs expected {c['expected']:g} ± {c['tolerance']:g}"
        if kind == "contains_text":
            if typ == "pdf":
                text = parsed.get("text")
                if text is None:
                    return NA, "PDF text extraction needs pypdf, which is not installed"
            else:
                text = parsed["text"]
            needles = c["text"] if isinstance(c["text"], list) else [c["text"]]
            hit = next((n for n in needles if n.lower() in text.lower()), None)
            return (PASS, f"found {hit!r}") if hit else (FAIL, "text absent")
        if kind == "png_min_size":
            w, h = parsed["width"], parsed["height"]
            ok = w >= c["min_width"] and h >= c["min_height"]
            return (PASS if ok else FAIL), f"{w}x{h} px"
        if kind == "png_dpi":
            if parsed.get("unit") != 1 or not parsed.get("ppu_x"):
                return FAIL, "no physical resolution (pHYs in pixels per metre) recorded"
            dx, dy = parsed["ppu_x"] * 0.0254, parsed["ppu_y"] * 0.0254
            ok = all(abs(d - c["expected"]) <= c["tolerance"] for d in (dx, dy))
            return (PASS if ok else FAIL), f"{dx:.1f}x{dy:.1f} dpi"
        if kind == "pdf_min_pages":
            if parsed["pages"] is None:
                return NA, "page count needs pypdf for a PDF with object streams"
            return (PASS if parsed["pages"] >= c["min"] else FAIL), f"{parsed['pages']} page(s)"
        if kind == "pptx_min_slides":
            return (PASS if parsed["slides"] >= c["min"] else FAIL), f"{parsed['slides']} slide(s)"
    except (KeyError, IndexError, TypeError) as exc:
        return FAIL, f"path not found ({exc})"
    return NA, f"unknown check {kind!r}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_artifact(workspace: Path, decl: dict, *, store_dir: Path | None = None,
                   results_dir: Path | None = None, graded: bool = True) -> dict:
    """Inspect one declared file in ``workspace``; copy it to ``store_dir`` when given."""
    path, typ = decl["path"], decl["type"]
    extra = [c for c in decl.get("checks", []) if c.get("kind") not in ("exists", "parseable")]
    rec = {"path": path, "type": typ, "exists": False, "parseable": None, "sha256": None,
           "bytes": None, "stored_as": None, "checks": []}
    names = ["exists", "parseable", *[_check_name(c) for c in extra]]

    def finish(verdicts: list[tuple[str, str]]) -> dict:
        if not graded:
            verdicts = [(NA, f"not graded: the run produced no answer ({d})") for _, d in verdicts]
        rec["checks"] = [{"name": n, "verdict": v, "detail": d}
                         for n, (v, d) in zip(names, verdicts)]
        return rec

    p = workspace / path
    problem = None
    if not _safe_rel(path):
        problem = "declared path is not inside the workspace"
    elif p.is_symlink():
        rec["exists"] = True
        problem = "is a symlink (not followed)"
    elif not p.exists():
        problem = "file missing"
    elif not p.is_file():
        rec["exists"] = True
        problem = "not a regular file"
    if problem:
        rec["parseable"] = False if rec["exists"] else None
        exists_v = (PASS, "present") if rec["exists"] else (FAIL, problem)
        return finish([exists_v] + [(FAIL, problem)] * (len(names) - 1))
    rec["exists"] = True
    try:
        data = p.read_bytes()
    except OSError as exc:
        rec["parseable"] = False
        return finish([(PASS, "present")] + [(FAIL, f"unreadable ({exc})")] * (len(names) - 1))
    rec["sha256"], rec["bytes"] = _sha256(data), len(data)
    if store_dir is not None and len(data) <= MAX_STORE_BYTES:
        dest = store_dir / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        try:
            rec["stored_as"] = dest.relative_to(results_dir).as_posix() if results_dir \
                else str(dest)
        except ValueError:
            rec["stored_as"] = str(dest)
    try:
        parsed = _parse(typ, data)
    except ValueError as exc:
        rec["parseable"] = False
        why = f"not a parseable {typ}: {exc}"
        return finish([(PASS, f"{len(data)} bytes"), (FAIL, why)] + [(FAIL, why)] * len(extra))
    rec["parseable"] = True
    if typ == "pdf":
        try:
            parsed["text"] = _pdf_text(data)
        except Exception:  # noqa: BLE001 — text is optional; a check needing it reports NA
            parsed["text"] = None
    return finish([(PASS, f"{len(data)} bytes"), (PASS, f"valid {typ}")]
                  + [_run_check(c, typ, parsed) for c in extra])


def check_artifacts(workspace: Path, decls: list[dict], *, store_dir: Path | None = None,
                    results_dir: Path | None = None, graded: bool = True) -> list[dict]:
    """One record per declared artifact (see the run record contract in docs/evals.md)."""
    return [check_artifact(workspace, d, store_dir=store_dir, results_dir=results_dir,
                           graded=graded) for d in decls]


def verdicts(records: list[dict]) -> list[str]:
    """Every check verdict, in declaration order — the artifacts dimension's criteria."""
    return [c["verdict"] for r in records for c in r.get("checks", [])]
