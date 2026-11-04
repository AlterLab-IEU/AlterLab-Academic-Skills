version 1.0

workflow align_and_sort {
  input {
    File reads
    File reference
  }
  call bwa_mem { input: reads = reads, ref = reference }
  call sort_bam { input: bam = bwa_mem.bam }
  output {
    File sorted = sort_bam.sorted_bam
  }
}

task bwa_mem {
  input {
    File reads
    File ref
  }
  command <<<
    bwa mem ~{ref} ~{reads} | samtools view -b - > out.bam
  >>>
  output {
    File bam = "out.bam"
  }
  runtime {
    docker: "biocontainers/bwa:v0.7.17_cv1"
  }
}

task sort_bam {
  input {
    File bam
  }
  command <<<
    samtools sort -o sorted.bam ~{bam} -@ ~{threads}
  >>>
  output {
    File sorted_bam = "sorted.bam"
  }
}
