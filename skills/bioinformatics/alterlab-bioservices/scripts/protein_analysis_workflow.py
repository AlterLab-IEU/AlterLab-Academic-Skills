#!/usr/bin/env python3
"""
Complete Protein Analysis Workflow

This script performs a comprehensive protein analysis pipeline:
1. UniProt search and identifier retrieval
2. FASTA sequence retrieval
3. BLAST similarity search
4. KEGG pathway discovery
5. STRING interaction mapping
6. GO annotation retrieval

Usage:
    python protein_analysis_workflow.py PROTEIN_NAME EMAIL [--skip-blast]

Examples:
    python protein_analysis_workflow.py ZAP70_HUMAN user@example.com
    python protein_analysis_workflow.py P43403 user@example.com --skip-blast

Note: BLAST searches can take several minutes. Use --skip-blast to skip this step.
"""

import sys
import time
import argparse
from bioservices import UniProt, KEGG, NCBIblast, STRING, QuickGO


def search_protein(query):
    """Search UniProt for protein and retrieve basic information."""
    print(f"\n{'='*70}")
    print("STEP 1: UniProt Search")
    print(f"{'='*70}")

    u = UniProt(verbose=False)

    print(f"Searching for: {query}")

    # Try direct retrieval first (if query looks like accession)
    if len(query) == 6 and query[0] in "OPQ":
        try:
            entry = u.retrieve(query, frmt="txt")
            if entry:
                uniprot_id = query
                print(f"✓ Found UniProt entry: {uniprot_id}")
                return u, uniprot_id
        except Exception:
            pass

    # Otherwise search
    results = u.search(
        query,
        frmt="tsv",
        columns="accession,gene_names,organism_name,length,protein_name",
        limit=5,
    )

    if not results:
        print("✗ No results found")
        return u, None

    lines = results.strip().split("\n")
    if len(lines) < 2:
        print("✗ No entries found")
        return u, None

    # Display results
    print(f"\n✓ Found {len(lines)-1} result(s):")
    for i, line in enumerate(lines[1:], 1):
        fields = line.split("\t")
        print(f"  {i}. {fields[0]} - {fields[1]} ({fields[2]})")

    # Use first result
    first_entry = lines[1].split("\t")
    uniprot_id = first_entry[0]
    gene_names = first_entry[1] if len(first_entry) > 1 else "N/A"
    organism = first_entry[2] if len(first_entry) > 2 else "N/A"
    length = first_entry[3] if len(first_entry) > 3 else "N/A"
    protein_name = first_entry[4] if len(first_entry) > 4 else "N/A"

    print(f"\nUsing first result:")
    print(f"  UniProt ID: {uniprot_id}")
    print(f"  Gene names: {gene_names}")
    print(f"  Organism: {organism}")
    print(f"  Length: {length} aa")
    print(f"  Protein: {protein_name}")

    return u, uniprot_id


def retrieve_sequence(uniprot, uniprot_id):
    """Retrieve FASTA sequence for protein."""
    print(f"\n{'='*70}")
    print("STEP 2: FASTA Sequence Retrieval")
    print(f"{'='*70}")

    try:
        sequence = uniprot.retrieve(uniprot_id, frmt="fasta")

        if sequence:
            # Extract sequence only (remove header)
            lines = sequence.strip().split("\n")
            header = lines[0]
            seq_only = "".join(lines[1:])

            print(f"✓ Retrieved sequence:")
            print(f"  Header: {header}")
            print(f"  Length: {len(seq_only)} residues")
            print(f"  First 60 residues: {seq_only[:60]}...")

            return seq_only
        else:
            print("✗ Failed to retrieve sequence")
            return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def run_blast(sequence, email, skip=False):
    """Run BLAST similarity search."""
    print(f"\n{'='*70}")
    print("STEP 3: BLAST Similarity Search")
    print(f"{'='*70}")

    if skip:
        print("⊘ Skipped (--skip-blast flag)")
        return None

    if not email or "@" not in email:
        print("⊘ Skipped (valid email required for BLAST)")
        return None

    try:
        print(f"Submitting BLASTP job...")
        print(f"  Database: uniprotkb")
        print(f"  Sequence length: {len(sequence)} aa")

        s = NCBIblast(verbose=False)

        jobid = s.run(
            program="blastp",
            sequence=sequence,
            stype="protein",
            database="uniprotkb",
            email=email
        )

        print(f"✓ Job submitted: {jobid}")
        print(f"  Waiting for completion...")

        # Poll for completion
        max_wait = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = s.get_status(jobid)
            elapsed = int(time.time() - start_time)
            print(f"  Status: {status} (elapsed: {elapsed}s)", end="\r")

            if status == "FINISHED":
                print(f"\n✓ BLAST completed in {elapsed}s")

                # Retrieve results
                results = s.get_result(jobid, "out")

                # Parse and display summary
                lines = results.split("\n")
                print(f"\n  Results preview:")
                for line in lines[:20]:
                    if line.strip():
                        print(f"    {line}")

                return results

            elif status in ("ERROR", "FAILURE", "NOT_FOUND"):
                print(f"\n✗ BLAST job did not complete: {status}")
                return None

            time.sleep(5)

        print(f"\n✗ Timeout after {max_wait}s")
        return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def discover_pathways(uniprot, kegg, uniprot_id):
    """Discover KEGG pathways for protein."""
    print(f"\n{'='*70}")
    print("STEP 4: KEGG Pathway Discovery")
    print(f"{'='*70}")

    try:
        # Map UniProt → KEGG. mapping() returns UniProt's job payload:
        # {"results": [{"from": ..., "to": ...}], "failedIds": [...]}
        print(f"Mapping {uniprot_id} to KEGG...")
        job = uniprot.mapping(fr="UniProtKB_AC-ID", to="KEGG", query=uniprot_id)

        kegg_ids = [
            row["to"] for row in (job or {}).get("results", []) if row["from"] == uniprot_id
        ]
        if not kegg_ids:
            print("✗ No KEGG mapping found")
            return []
        print(f"✓ KEGG ID(s): {kegg_ids}")

        # Get pathways for first KEGG ID
        kegg_id = kegg_ids[0]
        organism, gene_id = kegg_id.split(":")

        print(f"\nSearching pathways for {kegg_id}...")
        pathways = kegg.get_pathway_by_gene(gene_id, organism)

        if not pathways:
            print("✗ No pathways found")
            return []

        print(f"✓ Found {len(pathways)} pathway(s):\n")

        # get_pathway_by_gene returns the parsed PATHWAY block, which current
        # bioservices gives as {pathway_id: name}; tolerate a plain sequence too.
        if isinstance(pathways, dict):
            pathway_pairs = list(pathways.items())
        else:
            pathway_pairs = [(pid, None) for pid in pathways]

        pathway_info = []
        for pathway_id, pathway_name in pathway_pairs:
            if not pathway_name:
                try:
                    entry = kegg.get(pathway_id)
                    pathway_name = "Unknown"
                    for line in entry.split("\n"):
                        if line.startswith("NAME"):
                            pathway_name = line.replace("NAME", "").strip()
                            break
                except Exception:
                    pathway_name = "[Error retrieving name]"

            pathway_info.append((pathway_id, pathway_name))
            print(f"  • {pathway_id}: {pathway_name}")

        return pathway_info

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def find_interactions(protein_query):
    """Find protein-protein interactions via STRING."""
    print(f"\n{'='*70}")
    print("STEP 5: Protein-Protein Interactions")
    print(f"{'='*70}")

    try:
        s = STRING()

        # PSICQUIC and BioGRID were removed from bioservices in 1.14; STRING answers
        # the same question. species is an NCBI taxid, required_score is 0-1000.
        print("Querying STRING for human interaction partners...")
        print(f"  Query: {protein_query} (taxid 9606, score >= 400)")

        rows = s.get_interaction_partners(
            protein_query, species=9606, required_score=400, limit=25
        )

        if not rows:
            print("✗ No interactions found in STRING")
            return []

        print(f"✓ Found {len(rows)} interaction(s):\n")

        interactions = []
        for i, row in enumerate(rows[:10], 1):
            protein_a = row.get("preferredName_A", "?")
            protein_b = row.get("preferredName_B", "?")
            score = row.get("score")
            interactions.append((protein_a, protein_b, score))
            print(f"  {i}. {protein_a} ↔ {protein_b} (score {score})")

        if len(rows) > 10:
            print(f"  ... and {len(rows)-10} more")

        return interactions

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def get_go_annotations(uniprot_id):
    """Retrieve GO annotations."""
    print(f"\n{'='*70}")
    print("STEP 6: Gene Ontology Annotations")
    print(f"{'='*70}")

    try:
        g = QuickGO()

        print(f"Retrieving GO annotations for {uniprot_id}...")
        # QuickGO REST parameters: geneProductId is prefixed and limit maxes out at 100.
        annotations = g.Annotation(
            geneProductId=f"UniProtKB:{uniprot_id}",
            includeFields="goName",
            limit=100,
        )

        rows = (annotations or {}).get("results") if isinstance(annotations, dict) else None
        if not rows:
            print("✗ No GO annotations found")
            return {}

        print(f"✓ Found {annotations.get('numberOfHits', len(rows))} annotation(s)\n")

        # Group by aspect; goAspect is spelled out (biological_process, ...)
        aspect_keys = {"biological_process": "P", "molecular_function": "F", "cellular_component": "C"}
        aspects = {"P": [], "F": [], "C": []}
        for row in rows:
            key = aspect_keys.get(row.get("goAspect"))
            if key:
                aspects[key].append((row["goId"], row.get("goName", "")))

        # Display summary
        print(f"  Biological Process (P): {len(aspects['P'])} terms")
        for go_id, go_term in aspects['P'][:5]:
            print(f"    • {go_id}: {go_term}")
        if len(aspects['P']) > 5:
            print(f"    ... and {len(aspects['P'])-5} more")

        print(f"\n  Molecular Function (F): {len(aspects['F'])} terms")
        for go_id, go_term in aspects['F'][:5]:
            print(f"    • {go_id}: {go_term}")
        if len(aspects['F']) > 5:
            print(f"    ... and {len(aspects['F'])-5} more")

        print(f"\n  Cellular Component (C): {len(aspects['C'])} terms")
        for go_id, go_term in aspects['C'][:5]:
            print(f"    • {go_id}: {go_term}")
        if len(aspects['C']) > 5:
            print(f"    ... and {len(aspects['C'])-5} more")

        return aspects

    except Exception as e:
        print(f"✗ Error: {e}")
        return {}


def main():
    """Main workflow."""
    parser = argparse.ArgumentParser(
        description="Complete protein analysis workflow using BioServices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python protein_analysis_workflow.py ZAP70_HUMAN user@example.com
  python protein_analysis_workflow.py P43403 user@example.com --skip-blast
        """
    )
    parser.add_argument("protein", help="Protein name or UniProt ID")
    parser.add_argument("email", help="Email address (required for BLAST)")
    parser.add_argument("--skip-blast", action="store_true",
                       help="Skip BLAST search (faster)")

    args = parser.parse_args()

    print("=" * 70)
    print("BIOSERVICES: Complete Protein Analysis Workflow")
    print("=" * 70)

    # Step 1: Search protein
    uniprot, uniprot_id = search_protein(args.protein)
    if not uniprot_id:
        print("\n✗ Failed to find protein. Exiting.")
        sys.exit(1)

    # Step 2: Retrieve sequence
    sequence = retrieve_sequence(uniprot, uniprot_id)
    if not sequence:
        print("\n⚠ Warning: Could not retrieve sequence")

    # Step 3: BLAST search
    if sequence:
        _blast_results = run_blast(sequence, args.email, args.skip_blast)
    # Step 4: Pathway discovery
    kegg = KEGG()
    pathways = discover_pathways(uniprot, kegg, uniprot_id)

    # Step 5: Interaction mapping
    interactions = find_interactions(args.protein)

    # Step 6: GO annotations
    go_terms = get_go_annotations(uniprot_id)

    # Summary
    print(f"\n{'='*70}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*70}")
    print(f"  Protein: {args.protein}")
    print(f"  UniProt ID: {uniprot_id}")
    print(f"  Sequence: {'✓' if sequence else '✗'}")
    print(f"  BLAST: {'✓' if not args.skip_blast and sequence else '⊘'}")
    print(f"  Pathways: {len(pathways)} found")
    print(f"  Interactions: {len(interactions)} found")
    print(f"  GO annotations: {sum(len(v) for v in go_terms.values())} found")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
