import dxpy


def filter_fastq(in_path, out_path, min_mean_quality):
    kept = 0
    with open(in_path) as fin, open(out_path, "w") as fout:
        while True:
            rec = [fin.readline() for _ in range(4)]
            if not rec[0]:
                break
            qual = rec[3].rstrip("\n")
            if sum(ord(c) - 33 for c in qual) / len(qual) >= min_mean_quality:
                fout.writelines(rec)
                kept += 1
    return kept


@dxpy.entry_point("main")
def main(reads, min_mean_quality=30):
    dxpy.download_dxfile(reads["$dnanexus_link"], "reads.fastq")
    filter_fastq("reads.fastq", "filtered.fastq", min_mean_quality)
    out = dxpy.upload_local_file("filtered.fastq")
    return {"filtered": dxpy.dxlink(out)}


dxpy.run()
