# Diagnostic Report Templates (radiology, pathology, laboratory)

Long-form structure for the three diagnostic report types. Standards and lexicons
(ACR, CAP, LOINC) are in `diagnostic_reports_standards.md`; this file holds the
section-by-section templates extracted from the skill body.

## Radiology Reports

Radiology reports follow a standardized structure to ensure clarity and completeness.

**1. Patient Demographics**
- Patient name (or ID in research contexts)
- Date of birth or age
- Medical record number
- Examination date and time

**2. Clinical Indication**
- Reason for examination
- Relevant clinical history
- Specific clinical question to be answered
- Example: "Rule out pulmonary embolism in patient with acute dyspnea"

**3. Technique**
- Imaging modality (X-ray, CT, MRI, ultrasound, PET, etc.)
- Anatomical region examined
- Contrast administration (type, route, volume)
- Protocol or sequence used
- Technical quality and limitations
- Example: "Contrast-enhanced CT of the chest, abdomen, and pelvis was performed using 100 mL of intravenous iodinated contrast. Oral contrast was not administered."

**4. Comparison**
- Prior imaging studies available for comparison
- Dates of prior studies
- Stability or change from prior imaging
- Example: "Comparison: CT chest from [date]"

**5. Findings**
- Systematic description of imaging findings
- Organ-by-organ or region-by-region approach
- Positive findings first, then pertinent negatives
- Measurements of lesions or abnormalities
- Use of standardized terminology (ACR lexicon, RadLex)
- Example:
  - Lungs: Bilateral ground-glass opacities, predominant in the lower lobes. No consolidation or pleural effusion.
  - Mediastinum: No lymphadenopathy. Heart size normal.
  - Abdomen: Liver, spleen, pancreas unremarkable. No free fluid.

**6. Impression/Conclusion**
- Concise summary of key findings
- Answers to the clinical question
- Differential diagnosis if applicable
- Recommendations for follow-up or additional studies
- Level of suspicion or diagnostic certainty
- Example:
  - "1. Bilateral ground-glass opacities consistent with viral pneumonia or atypical infection. COVID-19 cannot be excluded. Clinical correlation recommended.
  - 2. No evidence of pulmonary embolism.
  - 3. Recommend follow-up imaging in 4-6 weeks to assess resolution."

**Structured Reporting:**

Many radiology departments use structured reporting templates for common examinations:
- Lung nodule reporting (Lung-RADS)
- Breast imaging (BI-RADS)
- Liver imaging (LI-RADS)
- Prostate imaging (PI-RADS)
- CT colonography (C-RADS)

Structured reports improve consistency, reduce ambiguity, and facilitate data extraction.

## Pathology Reports

Pathology reports document microscopic findings from tissue specimens and provide diagnostic conclusions.

**1. Patient Information**
- Patient name and identifiers
- Date of birth, age, sex
- Ordering physician
- Medical record number
- Specimen received date

**2. Specimen Information**
- Specimen type (biopsy, excision, resection)
- Anatomical site
- Laterality if applicable
- Number of specimens/blocks/slides
- Example: "Skin, left forearm, excisional biopsy"

**3. Clinical History**
- Relevant clinical information
- Indication for biopsy
- Prior diagnoses
- Example: "History of melanoma. New pigmented lesion, rule out recurrence."

**4. Gross Description**
- Macroscopic appearance of specimen
- Size, weight, color, consistency
- Orientation markers if present
- Sectioning and sampling approach
- Example: "The specimen consists of an ellipse of skin measuring 2.5 x 1.0 x 0.5 cm. A pigmented lesion measuring 0.6 cm in diameter is present on the surface. The specimen is serially sectioned and entirely submitted in cassettes A1-A3."

**5. Microscopic Description**
- Histological findings
- Cellular characteristics
- Architectural patterns
- Presence of malignancy
- Margins if applicable
- Special stains or immunohistochemistry results

**6. Diagnosis**
- Primary diagnosis
- Grade and stage if applicable (cancer)
- Margin status
- Lymph node status if applicable
- Synoptic reporting for cancers (CAP protocols)
- Example:
  - "MALIGNANT MELANOMA, SUPERFICIAL SPREADING TYPE
  - Breslow thickness: 1.2 mm
  - Clark level: IV
  - Mitotic rate: 3/mm²
  - Ulceration: Absent
  - Margins: Negative (closest margin 0.4 cm)
  - Lymphovascular invasion: Not identified"

**7. Comment** (if needed)
- Additional context or interpretation
- Differential diagnosis
- Recommendations for additional studies
- Clinical correlation suggestions

**Synoptic Reporting:**

The College of American Pathologists (CAP) provides synoptic reporting templates for cancer specimens. These checklists ensure all relevant diagnostic elements are documented. Key elements for cancer reporting:
- Tumor site
- Tumor size
- Histologic type
- Histologic grade
- Extent of invasion
- Lymph-vascular invasion
- Perineural invasion
- Margins
- Lymph nodes (number examined, number positive)
- Pathologic stage (TNM classification)
- Ancillary studies (molecular markers, biomarkers)

## Laboratory Reports

Laboratory reports communicate test results for clinical specimens (blood, urine, tissue, etc.).

**1. Patient and Specimen Information**
- Patient identifiers
- Specimen type (blood, serum, urine, CSF, etc.)
- Collection date and time
- Received date and time
- Ordering provider

**2. Test Name and Method**
- Full test name
- Methodology (immunoassay, spectrophotometry, PCR, etc.)
- Laboratory accession number

**3. Results**
- Quantitative or qualitative result
- Units of measurement
- Reference range (normal values)
- Flags for abnormal values (H = high, L = low)
- Critical values highlighted
- Example:
  - Hemoglobin: 8.5 g/dL (L) [Reference: 12.0-16.0 g/dL]
  - White Blood Cell Count: 15.2 x10³/μL (H) [Reference: 4.5-11.0 x10³/μL]

**4. Interpretation** (when applicable)
- Clinical significance of results
- Suggested follow-up or additional testing
- Correlation with diagnosis
- Drug levels and therapeutic ranges

**5. Quality Control Information**
- Specimen adequacy
- Specimen quality issues (hemolyzed, lipemic, clotted)
- Delays in processing
- Technical limitations

**Critical Value Reporting:**
- Life-threatening results require immediate notification
- Examples: glucose <40 or >500 mg/dL, potassium <2.5 or >6.5 mEq/L
- Document notification time and recipient
