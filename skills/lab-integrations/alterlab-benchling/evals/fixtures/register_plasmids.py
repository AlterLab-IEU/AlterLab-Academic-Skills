"""Register plasmid constructs and file them into a freezer box (draft from a postdoc)."""
import os

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers.task_helpers import wait_for_task
from benchling_sdk.models import DnaSequenceCreate

benchling = Benchling(url="https://ourlab.benchling.com",
                      auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"]))

seq = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="pGFP-01",
        bases="ATGAGCAAAGGAGAAGAACTTTTCACTGG",
        is_circular=True,
        folder_id="lib_K9t2Qx",
        registry_id="src_7Hc1Ld",
        entity_registry_id="PLS-0042",
        naming_strategy="NEW_IDS",
    )
)

# move the tube that holds the prep into box A1
benchling.containers.transfer(container_id="con_8f3k2", destination_id="box_A1")

# list what is now in box A1
for page in benchling.containers.list(parent_storage_id="box_A1"):
    for c in page:
        print(c.name, c.barcode)

task = benchling.dna_sequences.bulk_create([])
wait_for_task(benchling, task_id=task.task_id)
