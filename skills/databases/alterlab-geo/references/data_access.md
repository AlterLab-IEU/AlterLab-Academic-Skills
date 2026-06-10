# Direct FTP / Download Access for GEO Files

GEO data can be downloaded directly via FTP, bypassing GEOparse — preferred for
bulk downloads (no rate limits).

## FTP via Python (`ftplib`)

```python
import ftplib
import os

def download_geo_ftp(accession, file_type="matrix", dest_dir="./data"):
    """Download GEO series files via FTP.

    Each file type lives in its own subdirectory of the series folder
    (matrix/, soft/, miniml/) — the path below must include it.
    """
    if not accession.startswith("GSE"):
        raise ValueError("This helper only handles GSE series accessions")

    # Accession-to-path rule: zero-pad to >=4 digits, replace last 3 with 'nnn'.
    # GSE123456 -> GSE123nnn ; GSE1234 -> GSE1nnn ; GSE567 -> GSEnnn
    gse_num = accession[3:]
    base_num = (gse_num[:-3] or "") + "nnn"

    subdir, filename = {
        "matrix": ("matrix", f"{accession}_series_matrix.txt.gz"),
        "soft":   ("soft",   f"{accession}_family.soft.gz"),
        "miniml": ("miniml", f"{accession}_family.xml.tgz"),
    }[file_type]
    ftp_path = f"/geo/series/GSE{base_num}/{accession}/{subdir}/"

    # Connect to FTP server
    ftp = ftplib.FTP("ftp.ncbi.nlm.nih.gov")
    ftp.login()
    ftp.cwd(ftp_path)

    # Download file
    os.makedirs(dest_dir, exist_ok=True)
    local_file = os.path.join(dest_dir, filename)

    with open(local_file, 'wb') as f:
        ftp.retrbinary(f'RETR {filename}', f.write)

    ftp.quit()
    print(f"Downloaded: {local_file}")
    return local_file

# Download series matrix file
download_geo_ftp("GSE123456", file_type="matrix")

# Download SOFT format file
download_geo_ftp("GSE123456", file_type="soft")
```

## Using wget or curl for Downloads

```bash
# Download series matrix file
wget ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123456/matrix/GSE123456_series_matrix.txt.gz

# Download all supplementary files for a series
wget -r -np -nd ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123456/suppl/

# Download SOFT format family file
wget ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123456/soft/GSE123456_family.soft.gz
```

## FTP Access Notes

- No rate limits for FTP downloads.
- Preferred method for bulk downloads.
- Can download entire directories with `wget -r`.
- The accession-to-path rule: take the numeric part and replace its last three
  digits with `nnn`. `GSE123456` → `GSE123nnn`; `GSE1234` → `GSE1nnn`; series
  below 1000 (e.g. `GSE567`) live in the catch-all `GSEnnn` directory. The same
  rule applies to `samples/GSM…nnn/` and `platforms/GPL…nnn/`.
