# PyHealth Datasets and Data Structures

## Core Data Structures

PyHealth 2.x stores every source table as rows of one long, polars-backed event table; the 1.x `Visit` object is deprecated.

### Event
One row from a source table:
- **event_type**: The table it came from (e.g. `"admissions"`, `"diagnoses_icd"`, `"prescriptions"`)
- **timestamp**: `datetime` of the event
- **attributes**: The table's configured columns, readable as attributes (e.g. `event.icd_code`, `event.icd_version`, `event.hadm_id`, `event.dischtime` for MIMIC-IV); column names come from the dataset YAML config

### Patient
All events for one patient, sorted by time:
- **patient_id**: Unique identifier
- **get_events(event_type=..., start=..., end=...)**: Events of one type, optionally within a time window — tasks use this to collect, e.g., the diagnoses recorded during an admission
- Visits/admissions are just events of type `"admissions"` (or the dataset's equivalent)

## BaseDataset Class

In PyHealth 2.x, dataset constructors take an explicit table list naming the source tables to load (table names come from the dataset's YAML config, e.g. `mimic4_ehr.yaml`). Single-source loaders (`MIMIC3Dataset`, `MIMIC4EHRDataset`, `eICUDataset`, `OMOPDataset`) take `root=` + `tables=[...]`; the multimodal `MIMIC4Dataset` takes `ehr_root=` / `note_root=` / `cxr_root=` with `ehr_tables=` / `note_tables=` / `cxr_tables=`. The EHR loaders (MIMIC-III/IV, eICU, OMOP) accept `dev=True` to work on the first 1,000 patients.

**Key Methods:**
- `iter_patients()`: Iterate through all patients
- `stats()`: Print dataset statistics (patient and event counts; returns `None`)
- `set_task(task)`: Apply a prediction task. Pass an **instance** of a task class (e.g. `MortalityPredictionMIMIC4()`), not a bare function.

## Available Datasets

### Electronic Health Record (EHR) Datasets

**MIMIC-III Dataset** (`MIMIC3Dataset`)
- Intensive care unit data from Beth Israel Deaconess Medical Center
- 40,000+ critical care patients
- Diagnoses, procedures, medications, lab results
- Usage: `from pyhealth.datasets import MIMIC3Dataset`

**MIMIC-IV Datasets** (`MIMIC4EHRDataset`, `MIMIC4NoteDataset`, `MIMIC4CXRDataset`, `MIMIC4Dataset`)
- Hospital + ICU EHR from Beth Israel Deaconess (MIMIC-IV), with optional notes and chest X-rays
- `MIMIC4EHRDataset(root=..., tables=[...])` for structured EHR only
- `MIMIC4Dataset(ehr_root=..., ehr_tables=[...], note_root=..., cxr_root=...)` to combine modalities
- Usage: `from pyhealth.datasets import MIMIC4EHRDataset`

**eICU Dataset** (`eICUDataset`)
- Multi-center critical care database
- 200,000+ admissions from 200+ hospitals
- Standardized ICU data across facilities
- Usage: `from pyhealth.datasets import eICUDataset`

**OMOP Dataset** (`OMOPDataset`)
- Observational Medical Outcomes Partnership format
- Standardized common data model
- Interoperability across healthcare systems
- Usage: `from pyhealth.datasets import OMOPDataset`

**EHRShot Dataset** (`EHRShotDataset`)
- Benchmark dataset for few-shot learning
- Specialized for testing model generalization
- Usage: `from pyhealth.datasets import EHRShotDataset`

### Physiological Signal Datasets

**Sleep EEG Datasets:**
- `SleepEDFDataset`: Sleep-EDF database for sleep staging
- `SHHSDataset`: Sleep Heart Health Study data
- `ISRUCDataset`: ISRUC-Sleep database

**Temple University EEG Datasets:**
- `TUEVDataset`: Abnormal EEG events detection
- `TUABDataset`: Abnormal/normal EEG classification
- `TUSZDataset`: Seizure detection

**All signal datasets support:**
- Multi-channel EEG signals
- Standardized sampling rates
- Expert annotations
- Sleep stage or abnormality labels

### Medical Imaging Datasets

**COVID-19 CXR Dataset** (`COVID19CXRDataset`)
- Chest X-ray images for COVID-19 classification
- Multi-class labels (COVID-19, pneumonia, normal)
- Usage: `from pyhealth.datasets import COVID19CXRDataset`

### Text-Based Datasets

**Medical Transcriptions Dataset** (`MedicalTranscriptionsDataset`)
- Clinical notes and transcriptions
- Medical specialty classification
- Text-based prediction tasks
- Usage: `from pyhealth.datasets import MedicalTranscriptionsDataset`

**Cardiology Dataset** (`CardiologyDataset`)
- Cardiac patient records
- Cardiovascular disease prediction
- Usage: `from pyhealth.datasets import CardiologyDataset`

### Preprocessed Datasets

**MIMIC Extract Dataset** (`MIMICExtractDataset`)
- Pre-extracted MIMIC features
- Ready-to-use benchmarking data
- Reduced preprocessing requirements
- Usage: `from pyhealth.datasets import MIMICExtractDataset`

## SampleDataset Class

Converts raw datasets into task-specific formatted samples.

**Purpose:** Transform patient-level data into model-ready input/output pairs

**Key Attributes:**
- `input_schema`: Defines input data structure
- `output_schema`: Defines target labels/predictions
- `samples`: List of processed samples

**Usage Pattern:**
```python
# After setting a task (a task-class instance) on a BaseDataset
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())
```

## Data Splitting Functions

**Patient-Level Split** (`split_by_patient`)
- Ensures no patient appears in multiple splits
- Prevents data leakage
- Recommended for clinical prediction tasks

**Visit-Level Split** (`split_by_visit`)
- Splits by individual visits
- Allows same patient across splits (use cautiously)

**Sample-Level Split** (`split_by_sample`)
- Random sample splitting
- Most flexible but may cause leakage

**Parameters:**
- `dataset`: SampleDataset to split
- `ratios`: Tuple of split ratios (e.g., [0.7, 0.1, 0.2])
- `seed`: Random seed for reproducibility

## Common Workflow

```python
from pyhealth.datasets import MIMIC4EHRDataset, split_by_patient
from pyhealth.tasks import MortalityPredictionMIMIC4

# 1. Load dataset (declare the tables you need)
dataset = MIMIC4EHRDataset(
    root="/path/to/data",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)

# 2. Set prediction task (instantiate the task class)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())

# 3. Split data
train, val, test = split_by_patient(sample_dataset, [0.7, 0.1, 0.2])

# 4. Get statistics (prints; returns None)
dataset.stats()
```

## Performance Notes

- PyHealth 2.x uses a **polars-backed** data layer for fast, memory-efficient processing
- Optimized for large-scale EHR datasets
- Memory-efficient patient iteration
- Vectorized operations for feature extraction
