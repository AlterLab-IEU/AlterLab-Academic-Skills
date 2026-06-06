# Direct FTP / Download Access for GEO Files

GEO data can be downloaded directly via FTP, bypassing GEOparse — preferred for
bulk downloads (no rate limits).

## FTP via Python (`ftplib`)

```python
import ftplib
import os

def download_geo_ftp(accession, file_type="matrix", dest_dir="./data"):
    """Download GEO files via FTP"""
    # Construct FTP path based on accession type
    if accession.startswith("GSE"):
        # Series files
        gse_num = accession[3:]
        base_num = gse_num[:-3] + "nnn"
        ftp_path = f"/geo/series/GSE{base_num}/{accession}/"

        if file_type == "matrix":
            filename = f"{accession}_series_matrix.txt.gz"
        elif file_type == "soft":
            filename = f"{accession}_family.soft.gz"
        elif file_type == "miniml":
            filename = f"{accession}_family.xml.tgz"

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
- The accession-to-path rule: `GSE123456` → directory `GSE123nnn` (last three
  digits replaced with `nnn`).
