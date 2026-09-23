#!/usr/bin/env python3
"""
COSMIC Data Download Utility

This script provides functions to download data from the COSMIC database
(Catalogue of Somatic Mutations in Cancer).

Usage:
    from download_cosmic import download_cosmic_file, get_common_file_path

    # Download a specific product archive
    download_cosmic_file(
        email="user@example.com",
        password="password",
        filepath=get_common_file_path("gene_census"),
        # -> "grch38/cosmic/v104/Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar"
    )

Requirements:
    - requests library: uv pip install requests
    - Valid COSMIC account credentials (register at cancer.sanger.ac.uk/cosmic)

How COSMIC scripted downloads work (current download service):
    1. GET https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted
       ?path=<archive path>&bucket=downloads with HTTP Basic auth
       ("Authorization: Basic <base64(email:password)>"; requests' auth=(email,
       password) tuple produces exactly that header). Both query parameters are
       required — omitting either returns HTTP 400; bad credentials return 401.
    2. The response is JSON with a time-limited signed "url"; fetch the file
       from that url WITHOUT the auth header.

    Files are per-product .tar archives (the gzipped TSV/VCF plus a README that
    describes every column), with explicit release versions in the path, e.g.
    grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar.
    The legacy /cosmic/file_download/ endpoint and legacy names such as
    CosmicMutantExport.tsv.gz no longer work for scripts (the endpoint now
    redirects to the login page).

    If COSMIC changes the endpoint, copy the command shown under "Scripted
    download" on https://cancer.sanger.ac.uk/cosmic/download/cosmic and set
    COSMIC_SCRIPTED_URL accordingly.
"""

import os
import sys
from typing import Optional

import requests

SCRIPTED_URL = os.environ.get(
    "COSMIC_SCRIPTED_URL",
    "https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted",
)

# Current COSMIC release as of 2026-09 (v104, released 2026-05-19). COSMIC
# ships two releases a year (May and November); check
# https://cancer.sanger.ac.uk/cosmic/release_notes and pass --version to override.
CURRENT_RELEASE = "v104"

# data_type shortcut -> product archive stem (VCF products live in a VCF/ subfolder)
PRODUCTS = {
    'mutations': 'Cosmic_GenomeScreensMutant_Tsv',           # genome-wide screens (WGS/WES)
    'targeted_mutations': 'Cosmic_CompleteTargetedScreensMutant_Tsv',
    'mutations_vcf': 'VCF/Cosmic_GenomeScreensMutant_Vcf',
    'non_coding_vcf': 'VCF/Cosmic_NonCodingVariants_Vcf',
    'mutation_census': 'Cosmic_MutantCensus_Tsv',             # coding mutations in CGC genes
    'gene_census': 'Cosmic_CancerGeneCensus_Tsv',
    'census_hallmarks': 'Cosmic_CancerGeneCensusHallmarksOfCancer_Tsv',
    'resistance_mutations': 'Cosmic_ResistanceMutations_Tsv',
    'structural_variants': 'Cosmic_StructuralVariants_Tsv',
    'breakpoints': 'Cosmic_Breakpoints_Tsv',
    'fusion_genes': 'Cosmic_Fusion_Tsv',
    'copy_number': 'Cosmic_CompleteCNA_Tsv',
    'gene_expression': 'Cosmic_CompleteGeneExpression_Tsv',
    'methylation': 'Cosmic_CompleteDifferentialMethylation_Tsv',
    'sample_info': 'Cosmic_Sample_Tsv',
    'classification': 'Cosmic_Classification_Tsv',
    'genes': 'Cosmic_Genes_Tsv',
    'transcripts': 'Cosmic_Transcripts_Tsv',
}

SIGNATURES_URL = "https://cancer.sanger.ac.uk/signatures/downloads/"


def download_cosmic_file(
    email: str,
    password: str,
    filepath: str,
    output_filename: Optional[str] = None,
    bucket: str = "downloads",
) -> bool:
    """
    Download a file from COSMIC database.

    The genome assembly and release are encoded in `filepath` (e.g.
    "grch38/cosmic/v104/..."). Use get_common_file_path() to build one.

    Args:
        email: COSMIC account email
        password: COSMIC account password
        filepath: Archive path, e.g. "grch38/cosmic/v104/Cosmic_Genes_Tsv_v104_GRCh38.tar"
        output_filename: Optional custom output filename (default: last part of filepath)
        bucket: Download bucket name expected by the scripted API (default "downloads")

    Returns:
        True if download successful, False otherwise
    """
    # Determine output filename
    if output_filename is None:
        output_filename = os.path.basename(filepath)

    try:
        # Step 1: Get the signed download URL
        print(f"Requesting download URL for: {filepath}")
        r = requests.get(
            SCRIPTED_URL,
            params={"path": filepath, "bucket": bucket},
            auth=(email, password),
            timeout=30
        )

        if r.status_code == 401:
            print("ERROR: Authentication failed. Check email and password.")
            return False
        elif r.status_code == 400:
            print("ERROR: Bad request — check the archive path (release version, "
                  "assembly, product name) against the COSMIC download page.")
            print(f"Response: {r.text}")
            return False
        elif r.status_code == 404:
            print(f"ERROR: File not found: {filepath}")
            return False
        elif r.status_code != 200:
            print(f"ERROR: Request failed with status code {r.status_code}")
            print(f"Response: {r.text}")
            return False

        # Parse response to get download URL
        response_data = r.json()
        download_url = response_data.get("url")

        if not download_url:
            print("ERROR: No download URL in response")
            return False

        # Step 2: Download the file (no auth header on the signed URL)
        print("Downloading file from signed URL")
        file_response = requests.get(download_url, stream=True, timeout=300)

        if file_response.status_code != 200:
            print(f"ERROR: Download failed with status code {file_response.status_code}")
            return False

        # Step 3: Write to disk
        print(f"Saving to: {output_filename}")
        total_size = int(file_response.headers.get('content-length', 0))

        with open(output_filename, 'wb') as f:
            if total_size == 0:
                f.write(file_response.content)
            else:
                downloaded = 0
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Show progress
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
                print()  # New line after progress

        print(f"Successfully downloaded: {output_filename}")
        return True

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False


def get_common_file_path(
    data_type: str,
    genome_assembly: str = "GRCh38",
    version: str = CURRENT_RELEASE
) -> Optional[str]:
    """
    Get the archive path for common COSMIC data products.

    Args:
        data_type: Shortcut from PRODUCTS (e.g. 'mutations', 'gene_census')
        genome_assembly: GRCh37 or GRCh38
        version: COSMIC release, e.g. "v104". Paths carry explicit versions;
            "latest" is mapped to CURRENT_RELEASE.

    Returns:
        Archive path string, or None if the type is unknown or not served
        by the scripted download API (e.g. 'signatures').
    """
    if data_type == 'signatures':
        # Mutational signatures (COSMIC v3.x) are downloaded from the separate
        # signatures site, not the COSMIC product archives.
        return None
    stem = PRODUCTS.get(data_type)
    if stem is None:
        return None
    if version == "latest":
        version = CURRENT_RELEASE
    subdir, _, name = stem.rpartition("/")
    prefix = f"{genome_assembly.lower()}/cosmic/{version}/"
    if subdir:
        prefix += f"{subdir}/"
    return f"{prefix}{name}_{version}_{genome_assembly}.tar"


def main():
    """Command-line interface for downloading COSMIC files."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Download files from COSMIC database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download the Cancer Gene Census (current release, GRCh38)
  %(prog)s user@email.com --data-type gene_census

  # Download a specific archive path
  %(prog)s user@email.com --filepath grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar

  # Download for GRCh37 / a pinned release
  %(prog)s user@email.com --data-type mutations --assembly GRCh37 --version v103
        """
    )

    parser.add_argument('email', help='COSMIC account email')
    parser.add_argument('--password', help='COSMIC account password (will prompt if not provided)')
    parser.add_argument('--filepath', help='Full archive path to download')
    parser.add_argument('--data-type',
                       choices=sorted([*PRODUCTS, 'signatures']),
                       help='Common data type shorthand')
    parser.add_argument('--assembly', default='GRCh38',
                       choices=['GRCh37', 'GRCh38'],
                       help='Genome assembly (default: GRCh38)')
    parser.add_argument('--version', default=CURRENT_RELEASE,
                       help=f'COSMIC release (default: {CURRENT_RELEASE})')
    parser.add_argument('-o', '--output', help='Output filename')

    args = parser.parse_args()

    # Determine filepath
    if args.filepath:
        filepath = args.filepath
    elif args.data_type:
        filepath = get_common_file_path(args.data_type, args.assembly, args.version)
        if not filepath:
            if args.data_type == 'signatures':
                print(f"Mutational signatures are downloaded from {SIGNATURES_URL}")
            else:
                print(f"ERROR: Unknown data type: {args.data_type}")
            return 1
    else:
        print("ERROR: Must provide either --filepath or --data-type")
        parser.print_help()
        return 1

    # Get password if not provided
    if not args.password:
        import getpass
        args.password = getpass.getpass('COSMIC password: ')

    # Download the file
    success = download_cosmic_file(
        email=args.email,
        password=args.password,
        filepath=filepath,
        output_filename=args.output,
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
