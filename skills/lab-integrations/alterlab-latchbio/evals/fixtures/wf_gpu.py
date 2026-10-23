"""Draft Latch workflow a labmate wrote. Meant to give the heavy step a GPU."""
from latch import custom_task, small_task, workflow
from latch.types import LatchFile


@small_task
def preprocess(reads: LatchFile) -> LatchFile:
    return reads


# intended: request a GPU for alignment
@custom_task(cpu=8, memory=32, gpu=1)
def align(reads: LatchFile) -> LatchFile:
    return reads


@workflow
def pipeline(reads: LatchFile) -> LatchFile:
    """GPU alignment pipeline.

    __metadata__:
        display_name: GPU alignment
    Args:
        reads:
          __metadata__:
            display_name: Input reads
    """
    pre = preprocess(reads=reads)
    return align(reads=pre)
