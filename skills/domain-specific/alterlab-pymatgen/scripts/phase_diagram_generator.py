#!/usr/bin/env python3
"""
Phase-stability report for a chemical system.

KEYLESS DEFAULT (--source optimade): queries the Materials Project OPTIMADE endpoint
(https://optimade.materialsproject.org, no API key) for every structure whose elements are
a subset of the chemical system, reads each structure's precomputed thermodynamics
(``_mp_stability``: energy_above_hull, formation_energy_per_atom), lists the stable phases,
and — with ``--analyze`` — reports a target composition's energy above hull and stability
status (stable / metastable / unstable). This answers "is X stable?" with no credential.

RICHER OPTIONAL BACKEND (--source mp): uses pymatgen's MPRester to pull full computed
entries, build an actual convex-hull ``PhaseDiagram``, list decomposition products, compute
chemical potentials, and write a phase-diagram plot. This needs the ``mp-api`` package and a
free ``MP_API_KEY``; without the key the script exits non-zero and points back to the
keyless OPTIMADE path rather than silently falling back.

Usage:
    python phase_diagram_generator.py Li-Fe-O                      # keyless stability list
    python phase_diagram_generator.py Li-Fe-O --analyze "LiFeO2"   # keyless: is it stable?
    python phase_diagram_generator.py Li-Fe-O --source mp --analyze "LiFeO2" --output pd.png
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

OPTIMADE_BASE = "https://optimade.materialsproject.org/v1/structures"
STABLE_TOL = 0.001   # eV/atom; on the convex hull
META_TOL = 0.05      # eV/atom; "nearly stable"


def _normalize_elements(chemsys: str) -> list[str]:
    els = [e.strip() for e in chemsys.split("-") if e.strip()]
    if len(els) < 2:
        print("Error: Chemical system must contain at least 2 elements (e.g. Li-Fe-O)")
        sys.exit(1)
    return sorted(els)


def _optimade_reduced_formula(formula: str) -> str:
    """OPTIMADE chemical_formula_reduced: element symbols in alphabetical order with
    integer proportions reduced by their GCD (a count of 1 is written without a digit)."""
    try:
        from pymatgen.core import Composition
    except ImportError:
        print("Error: pymatgen is not installed. Run install-free: uv run --python \">=3.11\" --with pymatgen python " + sys.argv[0] + " ...")
        sys.exit(1)
    comp = Composition(formula)
    reduced_comp, _ = comp.get_reduced_composition_and_factor()
    amts = reduced_comp.get_el_amt_dict()
    parts = []
    for el in sorted(amts):
        n = int(round(amts[el]))
        parts.append(el if n == 1 else f"{el}{n}")
    return "".join(parts)


def _fetch_optimade(filter_str: str, fields: str, cap: int = 2000) -> list[dict]:
    """Page through an OPTIMADE query (keyless) and return the list of structure records."""
    params = {"filter": filter_str, "response_fields": fields, "page_limit": 100}
    url = OPTIMADE_BASE + "?" + urllib.parse.urlencode(params)
    out: list[dict] = []
    while url and len(out) < cap:
        req = urllib.request.Request(url, headers={"User-Agent": "alterlab-pymatgen/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed host)
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"Error: OPTIMADE request failed: {exc}")
            sys.exit(1)
        out.extend(payload.get("data", []))
        url = (payload.get("links") or {}).get("next")
        if isinstance(url, dict):
            url = url.get("href")
    return out


def _e_above_hull(attrs: dict):
    """Pull the GGA/GGA+U energy_above_hull (eV/atom) from _mp_stability, preferring the
    mixed functional set, then plain gga_gga+u, then r2scan."""
    stab = attrs.get("_mp_stability") or {}
    for key in ("gga_gga+u_r2scan", "gga_gga+u", "r2scan"):
        if key in stab and stab[key].get("energy_above_hull") is not None:
            return stab[key]["energy_above_hull"], stab[key].get("formation_energy_per_atom")
    return None, None


def run_optimade(chemsys: str, args) -> None:
    els = _normalize_elements(chemsys)
    quoted = ",".join(f'"{e}"' for e in els)
    print(f"\n{'='*60}\nPHASE STABILITY (keyless, MP OPTIMADE): {'-'.join(els)}\n{'='*60}\n")
    print("Fetching structures from optimade.materialsproject.org (no API key)...")
    records = _fetch_optimade(
        f"elements HAS ONLY {quoted}",
        "chemical_formula_reduced,_mp_stability",
    )
    rows = []
    for rec in records:
        attrs = rec.get("attributes", {})
        eah, fe = _e_above_hull(attrs)
        if eah is None:
            continue
        rows.append((rec.get("id"), attrs.get("chemical_formula_reduced"), eah, fe))
    print(f"✓ Retrieved {len(records)} structures ({len(rows)} with thermodynamics)")
    if not rows:
        print(f"Error: no thermodynamics returned for {'-'.join(els)}")
        sys.exit(1)

    stable = sorted((r for r in rows if r[2] <= STABLE_TOL), key=lambda r: r[1] or "")
    print(f"\n--- STABLE PHASES (E_above_hull <= {STABLE_TOL} eV/atom) ---")
    seen = set()
    for mp_id, formula, eah, fe in stable:
        if formula in seen:
            continue
        seen.add(formula)
        fe_s = f"{fe:+.4f}" if fe is not None else "   n/a"
        print(f"  {formula:<16} {mp_id:<14} E_f = {fe_s} eV/atom")

    if args.analyze:
        target = _optimade_reduced_formula(args.analyze)
        print(f"\n--- STABILITY ANALYSIS: {args.analyze} (OPTIMADE reduced: {target}) ---")
        polymorphs = [r for r in rows if r[1] == target]
        if not polymorphs:
            print(f"No structure with reduced formula {target} in Materials Project.")
            print("The composition may be off the known set; use --source mp for a full "
                  "convex-hull decomposition of a hypothetical composition.")
            return
        best = min(polymorphs, key=lambda r: r[2])
        mp_id, _, eah, fe = best
        print(f"Lowest-energy polymorph: {mp_id}")
        print(f"Energy above hull:       {eah:.4f} eV/atom")
        if fe is not None:
            print(f"Formation energy:        {fe:+.4f} eV/atom")
        if eah <= STABLE_TOL:
            print("Status:                  STABLE (on the convex hull)")
        elif eah < META_TOL:
            print("Status:                  METASTABLE (nearly stable)")
        else:
            print("Status:                  UNSTABLE")
            print("Run with --source mp for the explicit decomposition products.")
    print(f"\n{'='*60}\n")
    print("Note: thermodynamics are Materials Project GGA/GGA+U values served keyless via "
          "OPTIMADE. For convex-hull plots, decomposition products and chemical potentials, "
          "re-run with --source mp (needs a free MP_API_KEY).")


def run_mp(chemsys: str, args) -> None:
    import os

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        print("Error: --source mp requires a free Materials Project API key in MP_API_KEY.")
        print("Get one at https://next-gen.materialsproject.org/ , then "
              "export MP_API_KEY='your_key'.")
        print("Or omit --source to use the keyless OPTIMADE stability report "
              "(the default) instead.")
        sys.exit(2)

    try:
        from pymatgen.core import Composition
        from pymatgen.analysis.phase_diagram import PhaseDiagram, PDPlotter
    except ImportError:
        print("Error: pymatgen is not installed. Run install-free: uv run --python \">=3.11\" --with pymatgen python " + sys.argv[0] + " ...")
        sys.exit(1)
    try:
        from mp_api.client import MPRester
    except ImportError:
        print("Error: mp-api is not installed. Run install-free: uv run --python \">=3.11\" --with pymatgen --with mp-api python " + sys.argv[0] + " ...")
        sys.exit(1)

    print(f"\n{'='*60}\nPHASE DIAGRAM (MP API): {chemsys}\n{'='*60}\n")
    print("Fetching data from Materials Project...")
    with MPRester(api_key) as mpr:
        entries = mpr.get_entries_in_chemsys(chemsys)
    print(f"✓ Retrieved {len(entries)} entries")
    if not entries:
        print(f"Error: No entries found for chemical system {chemsys}")
        sys.exit(1)

    pd = PhaseDiagram(entries)
    print(f"✓ Phase diagram with {len(pd.stable_entries)} stable phases")
    print("\n--- STABLE PHASES ---")
    for entry in pd.stable_entries:
        print(f"  {entry.composition.reduced_formula:<20} "
              f"E = {entry.energy_per_atom:.4f} eV/atom")

    if args.analyze:
        print(f"\n--- STABILITY ANALYSIS: {args.analyze} ---")
        comp = Composition(args.analyze)
        matches = [e for e in entries
                   if e.composition.reduced_formula == comp.reduced_formula]
        closest = min(matches, key=lambda e: e.energy_per_atom) if matches else None
        if closest:
            eah = pd.get_e_above_hull(closest)
            print(f"Energy above hull:    {eah:.4f} eV/atom")
            if eah < STABLE_TOL:
                print("Status:               STABLE (on convex hull)")
            elif eah < META_TOL:
                print("Status:               METASTABLE (nearly stable)")
            else:
                print("Status:               UNSTABLE")
                print("\nDecomposes to:")
                for entry, frac in pd.get_decomposition(comp).items():
                    print(f"  {frac:.3f} × {entry.composition.reduced_formula}")
                print(f"\nDecomposition energy: {eah:.4f} eV/atom")
        else:
            print(f"No entry for {args.analyze}; checking hypothetical composition...")
            for entry, frac in pd.get_decomposition(comp).items():
                print(f"  {frac:.3f} × {entry.composition.reduced_formula}")

    if args.output:
        from pathlib import Path
        p = Path(args.output)
        PDPlotter(pd, show_unstable=args.show_unstable).write_image(
            str(p), image_format=p.suffix[1:])
        print(f"✓ Phase diagram saved to {p}")
    print(f"\n{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase-stability report (keyless OPTIMADE by default; MP API optional).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("chemsys", help="Chemical system, e.g. Li-Fe-O")
    parser.add_argument("--source", choices=["optimade", "mp"], default="optimade",
                        help="optimade = keyless MP OPTIMADE stability (default); "
                             "mp = full PhaseDiagram via MPRester (needs MP_API_KEY)")
    parser.add_argument("--analyze", "-a", help="Report stability of this formula, e.g. LiFeO2")
    parser.add_argument("--output", "-o", help="(mp only) write phase-diagram plot (PNG/PDF/SVG)")
    parser.add_argument("--show-unstable", action="store_true",
                        help="(mp only) include unstable phases in the plot")
    args = parser.parse_args()

    if args.source == "mp":
        run_mp(args.chemsys, args)
    else:
        if args.output or args.show_unstable:
            print("Note: --output/--show-unstable need --source mp; the keyless OPTIMADE "
                  "report is text-only.", file=sys.stderr)
        run_optimade(args.chemsys, args)


if __name__ == "__main__":
    main()
