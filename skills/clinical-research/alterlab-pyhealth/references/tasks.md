# PyHealth Clinical Prediction Tasks

## Overview

PyHealth provides 20+ predefined clinical prediction tasks for common healthcare AI applications. Each task transforms raw patient data into structured input-output pairs for model training.

> **Naming convention (PyHealth 2.x).** Tasks are **classes** (mostly `{Task}{Dataset}`, e.g. `MortalityPredictionMIMIC4`, `ReadmissionPredictionMIMIC3`, `DrugRecommendationMIMIC3`). You **instantiate** the class and pass the instance to `set_task`. The names below are the class names exported by `pyhealth.tasks` in 2.0.2; the naming is not fully regular (e.g. `LengthOfStayPredictioneICU`, `MIMIC3ICD9Coding`, `EEGAbnormalTUAB`), so copy them rather than deriving them. A few legacy snake-case functions (`sleep_staging_isruc_fn`, `sleep_staging_shhs_fn`, `patient_linkage_mimic3_fn`, `drug_recommendation_*_fn`) are still exported for older signal/linkage workflows. When unsure, run `dir(pyhealth.tasks)` in the installed version.

## Task Structure

Each task subclasses `BaseTask` (`from pyhealth.tasks.base_task import BaseTask`) and defines:

- **task_name**: String identifier
- **input_schema**: Dict mapping feature keys to processor types (e.g. `{"conditions": "sequence"}`; tuple form `("stagenet", {"padding": 0})` passes processor kwargs)
- **output_schema**: Dict mapping the label key to its type (e.g. `{"mortality": "binary"}`)
- **`__call__(patient)`**: Returns the list of sample dicts for one patient

**Usage Pattern:**
```python
from pyhealth.datasets import MIMIC4EHRDataset
from pyhealth.tasks import MortalityPredictionMIMIC4

dataset = MIMIC4EHRDataset(
    root="/path/to/data",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())
```

## Electronic Health Record (EHR) Tasks

### Mortality Prediction

**Purpose:** Predict patient death risk at next visit or within specified timeframe

**MIMIC-III Mortality** (`MortalityPredictionMIMIC3`; multimodal variant `MultimodalMortalityPredictionMIMIC3`)
- Predicts death at next hospital visit
- Binary classification task
- Input: Historical diagnoses, procedures, medications
- Output: Binary label (deceased/alive)

**MIMIC-IV Mortality** (`MortalityPredictionMIMIC4`; multimodal variant `MultimodalMortalityPredictionMIMIC4`)
- Updated version for MIMIC-IV dataset
- Enhanced feature set
- Improved label quality

**eICU Mortality** (`MortalityPredictionEICU`, `MortalityPredictionEICU2`)
- Multi-center ICU mortality prediction
- Accounts for hospital-level variation

**OMOP Mortality** (`MortalityPredictionOMOP`)
- Standardized mortality prediction
- Works with OMOP common data model

**In-Hospital Mortality** (`InHospitalMortalityMIMIC4`; MEDS-format data: `InHospitalMortalityMEDS`)
- Predicts death during current hospitalization
- Real-time risk assessment
- Earlier prediction window than next-visit mortality

**StageNet Mortality** (`MortalityPredictionStageNetMIMIC4`; inputs `icd_codes` + `labs`)
- Specialized for StageNet model architecture
- Temporal stage-aware prediction

### Hospital Readmission Prediction

**Purpose:** Identify patients at risk of hospital readmission within specified timeframe (typically 30 days)

**MIMIC-III Readmission** (`ReadmissionPredictionMIMIC3`)
- 30-day readmission prediction
- Binary classification
- Input: Diagnosis history, medications, demographics
- Output: Binary label (readmitted/not readmitted)

**MIMIC-IV Readmission** (`ReadmissionPredictionMIMIC4`)
- Enhanced readmission features
- Improved temporal modeling

**eICU Readmission** (`ReadmissionPredictionEICU`)
- ICU-specific readmission risk
- Multi-site data

**OMOP Readmission** (`ReadmissionPredictionOMOP`)
- Standardized readmission prediction

### Length of Stay Prediction

**Purpose:** Estimate hospital stay duration for resource planning and patient management

**MIMIC-III Length of Stay** (`LengthOfStayPredictionMIMIC3`)
- Regression task
- Input: Admission diagnoses, vitals, demographics
- Output: Continuous value (days)

**MIMIC-IV Length of Stay** (`LengthOfStayPredictionMIMIC4`; StageNet format: `LengthOfStayStageNetMIMIC4`)
- Enhanced features for LOS prediction
- Better temporal granularity

**eICU Length of Stay** (`LengthOfStayPredictioneICU`)
- ICU stay duration prediction
- Multi-hospital data

**OMOP Length of Stay** (`LengthOfStayPredictionOMOP`)
- Standardized LOS prediction

### Drug Recommendation

**Purpose:** Suggest appropriate medications based on patient history and current conditions

**MIMIC-III Drug Recommendation** (`DrugRecommendationMIMIC3`)
- Multi-label classification
- Input: Diagnoses, previous medications, demographics
- Output: Set of recommended drug codes
- Considers drug-drug interactions

**MIMIC-IV Drug Recommendation** (`DrugRecommendationMIMIC4`)
- Updated medication data
- Enhanced interaction modeling

**eICU Drug Recommendation** (`DrugRecommendationEICU`)
- Critical care medication recommendations

**OMOP Drug Recommendation** (`DrugRecommendationOMOP`)
- Standardized drug recommendation

**Key Considerations:**
- Handles polypharmacy scenarios
- Multi-label prediction (multiple drugs per patient)
- Can integrate with SafeDrug/GAMENet models for safety-aware recommendations

## Specialized Clinical Tasks

### Medical Coding

**MIMIC-III ICD-9 Coding** (`MIMIC3ICD9Coding`)
- Assigns ICD-9 diagnosis/procedure codes to clinical notes
- Multi-label text classification
- Input: Clinical text/documentation
- Output: Set of ICD-9 codes
- Supports both diagnosis and procedure coding

### Patient Linkage

**MIMIC-III Patient Linking** (`PatientLinkageMIMIC3Task`; legacy function `patient_linkage_mimic3_fn`)
- Record matching and deduplication
- Binary classification (same patient or not)
- Input: Demographic and clinical features from two records
- Output: Match probability

## Physiological Signal Tasks

### Sleep Staging

**Purpose:** Classify sleep stages from EEG/physiological signals for sleep disorder diagnosis

**ISRUC Sleep Staging** (legacy function `sleep_staging_isruc_fn`)
- Multi-class classification (Wake, N1, N2, N3, REM)
- Input: Multi-channel EEG signals
- Output: Sleep stage per epoch (typically 30 seconds)

**SleepEDF Sleep Staging** (`SleepStagingSleepEDF`; legacy function `sleep_staging_sleepedf_fn`)
- Standard sleep staging task
- PSG signal processing

**SHHS Sleep Staging** (legacy function `sleep_staging_shhs_fn`)
- Large-scale sleep study data
- Population-level sleep analysis

**Standardized Labels:**
- Wake (W)
- Non-REM Stage 1 (N1)
- Non-REM Stage 2 (N2)
- Non-REM Stage 3 (N3/Deep Sleep)
- REM (Rapid Eye Movement)

### EEG Analysis

**Abnormality Detection** (`EEGAbnormalTUAB`)
- Binary classification (normal/abnormal EEG)
- Clinical screening application
- Input: Multi-channel EEG recordings
- Output: Binary label

**Event Detection** (`EEGEventsTUEV`)
- Identify specific EEG events (spikes, seizures)
- Multi-class classification
- Input: EEG time series
- Output: Event type and timing

**Seizure Detection** (no built-in TUSZ task class in 2.0.2)
- Write a custom `BaseTask` over your EEG loader, or use the TUEV event task
- Input: Continuous EEG
- Output: Seizure/non-seizure classification

## Medical Imaging Tasks

### COVID-19 Chest X-ray Classification

**COVID-19 CXR** (`COVID19CXRClassification`; also `ChestXray14BinaryClassification`, `ChestXray14MultilabelClassification`)
- Multi-class image classification
- Classes: COVID-19, bacterial pneumonia, viral pneumonia, normal
- Input: Chest X-ray images
- Output: Disease classification

## Text-Based Tasks

### Medical Transcription Classification

**Medical Specialty Classification** (`MedicalTranscriptionsClassification`)
- Classify clinical notes by medical specialty
- Multi-class text classification
- Input: Clinical transcription text
- Output: Medical specialty (Cardiology, Neurology, etc.)

## Custom Task Creation

### Creating Custom Tasks

Subclass `BaseTask`, declare `input_schema` / `output_schema`, and implement `__call__` to emit one flat sample dict per prediction. Sample keys must match the schema keys; PyHealth wires up the matching processors automatically.

```python
from datetime import datetime, timedelta
from typing import Any, Dict, List
from pyhealth.tasks import BaseTask


class ThirtyDayReadmissionMIMIC4(BaseTask):
    task_name: str = "ThirtyDayReadmissionMIMIC4"
    # The model reads its inputs and label from these schemas.
    input_schema: Dict[str, str] = {
        "conditions": "sequence",
        "procedures": "sequence",
    }
    output_schema: Dict[str, str] = {"readmitted": "binary"}

    def __call__(self, patient: Any) -> List[Dict[str, Any]]:
        samples: List[Dict[str, Any]] = []
        admissions = patient.get_events(event_type="admissions")

        for i in range(len(admissions) - 1):
            adm, nxt = admissions[i], admissions[i + 1]
            discharge = datetime.strptime(adm.dischtime, "%Y-%m-%d %H:%M:%S")

            # Events are table rows; filter them to this admission's time window
            diagnoses = patient.get_events(
                event_type="diagnoses_icd", start=adm.timestamp, end=discharge
            )
            procedures = patient.get_events(
                event_type="procedures_icd", start=adm.timestamp, end=discharge
            )
            conditions = [e.icd_code for e in diagnoses if getattr(e, "icd_code", None)]
            procs = [e.icd_code for e in procedures if getattr(e, "icd_code", None)]
            if not conditions or not procs:
                continue

            samples.append({
                "patient_id": patient.patient_id,
                "visit_id": adm.hadm_id,
                "conditions": conditions,
                "procedures": procs,
                "readmitted": int(nxt.timestamp - discharge <= timedelta(days=30)),
            })

        return samples


# Apply the custom task (instantiate it); the dataset must load the
# "diagnoses_icd" and "procedures_icd" tables
sample_dataset = dataset.set_task(ThirtyDayReadmissionMIMIC4())
```

> The pattern mirrors the built-in `MortalityPredictionMIMIC4`: `patient.get_events(event_type=<table>, start=..., end=...)` returns rows whose columns are attributes (`icd_code`, `hadm_id`, `dischtime`, ...). Column names come from the dataset's YAML config, so confirm them for other datasets before relying on a specific attribute.

### Task Function Components

1. **Input Schema Definition**
   - Specify which features to extract
   - Define feature types (codes, sequences, values)
   - Set temporal windows

2. **Output Schema Definition**
   - Define prediction targets
   - Set label types (binary, multi-class, multi-label, regression)
   - Specify evaluation metrics

3. **Filtering Logic**
   - Exclude patients/visits with insufficient data
   - Apply inclusion/exclusion criteria
   - Handle missing data

4. **Sample Generation**
   - Create input-output pairs
   - Maintain patient/visit identifiers
   - Preserve temporal ordering

## Task Selection Guidelines

### Clinical Prediction Tasks
**Use when:** Working with structured EHR data (diagnoses, medications, procedures)

**Datasets:** MIMIC-III, MIMIC-IV, eICU, OMOP

**Common tasks:**
- Mortality prediction for risk stratification
- Readmission prediction for care transition planning
- Length of stay for resource allocation
- Drug recommendation for clinical decision support

### Signal Processing Tasks
**Use when:** Working with physiological time-series data

**Datasets:** SleepEDF, SHHS, ISRUC, TUEV, TUAB

**Common tasks:**
- Sleep staging for sleep disorder diagnosis
- EEG abnormality detection for screening
- Seizure detection for epilepsy monitoring

### Imaging Tasks
**Use when:** Working with medical images

**Datasets:** COVID-19 CXR

**Common tasks:**
- Disease classification from radiographs
- Abnormality detection

### Text Tasks
**Use when:** Working with clinical notes and documentation

**Datasets:** Medical Transcriptions, MIMIC-III (with notes)

**Common tasks:**
- Medical coding from clinical text
- Specialty classification
- Clinical information extraction

## Task Output Structure

`set_task` returns a `SampleDataset` of flat sample dicts whose keys match the task's `input_schema` / `output_schema`:

```python
sample = {
    "patient_id": "unique_patient_id",
    # feature keys from input_schema, e.g.:
    "conditions": ["428.0", "401.9"],
    "procedures": ["9904", "3893"],
    "drugs": ["Metoprolol", "Lisinopril"],
    # label key from output_schema, e.g.:
    "mortality": 0,
}
```

## Integration with Models

Models read their inputs and label directly from the task's `input_schema` / `output_schema`, so no key arguments are passed:

```python
from pyhealth.datasets import MIMIC4EHRDataset
from pyhealth.tasks import MortalityPredictionMIMIC4
from pyhealth.models import Transformer

# 1. Create task-specific dataset
dataset = MIMIC4EHRDataset(
    root="/path/to/data",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())

# 2. The model picks up "conditions"/"procedures"/"drugs" -> "mortality" (binary)
model = Transformer(dataset=sample_dataset, embedding_dim=128)
```

## Best Practices

1. **Match task to clinical question**: Choose predefined tasks when available for standardized benchmarking

2. **Consider temporal windows**: Ensure sufficient history for meaningful predictions

3. **Handle class imbalance**: Many clinical outcomes are rare (mortality, readmission)

4. **Validate clinical relevance**: Ensure prediction windows align with clinical decision-making timelines

5. **Use appropriate metrics**: Different tasks require different evaluation metrics (AUROC for binary, macro-F1 for multi-class)

6. **Document exclusion criteria**: Track which patients/visits are filtered and why

7. **Preserve patient privacy**: Always use de-identified data and follow HIPAA/GDPR guidelines
