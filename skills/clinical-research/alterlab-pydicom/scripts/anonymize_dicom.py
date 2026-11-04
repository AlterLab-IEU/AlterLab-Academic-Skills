#!/usr/bin/env python3
"""
Anonymize DICOM files by removing or replacing Protected Health Information (PHI).

This is a first-pass tag scrubber, not a validated de-identification profile: it applies
the tag list below at every level, including inside sequences (e.g. an Accession Number
repeated in Request Attributes Sequence), but it does not shift other dates, replace UIDs,
or detect text burned into the pixel data; it only warns when Burned In Annotation is YES.
For data leaving your institution, use a DICOM PS3.15 Annex E based tool (e.g. `deid` or
`dicognito`) and review the output.

Usage:
    python anonymize_dicom.py input.dcm output.dcm
    python anonymize_dicom.py input.dcm output.dcm --patient-id ANON001
    python anonymize_dicom.py input.dcm output.dcm --keep-private   # keep vendor private tags
"""

import argparse
import sys
from pathlib import Path

try:
    import pydicom
except ImportError:
    print("Error: pydicom is not installed. Run this script with: "
          "uv run --python \">=3.11\" --with \"pydicom>=3.0\" python anonymize_dicom.py ...")
    sys.exit(1)


# Tags commonly containing PHI (Protected Health Information)
PHI_TAGS = [
    'PatientName', 'PatientID', 'PatientBirthDate', 'PatientBirthTime',
    'PatientSex', 'PatientAge', 'PatientSize', 'PatientWeight',
    'PatientAddress', 'PatientTelephoneNumbers', 'PatientMotherBirthName',
    'MilitaryRank', 'EthnicGroup', 'Occupation', 'PatientComments',
    'InstitutionName', 'InstitutionAddress', 'InstitutionalDepartmentName',
    'ReferringPhysicianName', 'ReferringPhysicianAddress',
    'ReferringPhysicianTelephoneNumbers', 'ReferringPhysicianIdentificationSequence',
    'PerformingPhysicianName', 'PerformingPhysicianIdentificationSequence',
    'OperatorsName', 'PhysiciansOfRecord', 'PhysiciansOfRecordIdentificationSequence',
    'NameOfPhysiciansReadingStudy', 'PhysiciansReadingStudyIdentificationSequence',
    'StudyDescription', 'SeriesDescription', 'AdmittingDiagnosesDescription',
    'DerivationDescription', 'RequestingPhysician', 'RequestingService',
    'RequestedProcedureDescription', 'ScheduledPerformingPhysicianName',
    'PerformedLocation', 'PerformedStationName',
    'AccessionNumber', 'OtherPatientIDs', 'OtherPatientNames', 'OtherPatientIDsSequence',
    'PatientBirthName', 'StationName', 'DeviceSerialNumber',
]


def anonymize_dicom(input_path, output_path, patient_id='ANONYMOUS', patient_name='ANONYMOUS',
                    remove_private=True):
    """
    Anonymize a DICOM file by removing or replacing PHI.

    Args:
        input_path: Path to input DICOM file
        output_path: Path to output anonymized DICOM file
        patient_id: Replacement patient ID (default: 'ANONYMOUS')
        patient_name: Replacement patient name (default: 'ANONYMOUS')
        remove_private: Remove vendor private tags, which often hold identifiers (default: True)
    """
    try:
        # Read DICOM file
        ds = pydicom.dcmread(input_path)

        # Track what was anonymized
        anonymized = []

        # Remove or replace sensitive data at every nesting level: identifiers are often
        # repeated inside sequences (Request Attributes, Referenced Patient, ...), which a
        # loop over the top-level dataset never reaches.
        phi = set(PHI_TAGS)

        def scrub(dataset, elem):
            tag = elem.keyword
            if tag not in phi:
                return
            where = '' if dataset is ds else ' (inside a sequence)'
            if tag == 'PatientName':
                dataset.PatientName = patient_name
                anonymized.append(f"{tag}{where}: replaced with '{patient_name}'")
            elif tag == 'PatientID':
                dataset.PatientID = patient_id
                anonymized.append(f"{tag}{where}: replaced with '{patient_id}'")
            elif tag == 'PatientBirthDate':
                dataset.PatientBirthDate = '19000101'
                anonymized.append(f"{tag}{where}: replaced with '19000101'")
            else:
                del dataset[elem.tag]
                anonymized.append(f"{tag}{where}: removed")

        ds.walk(scrub)

        # Tags cannot remove text drawn into the image itself
        if str(ds.get('BurnedInAnnotation', '')).upper() == 'YES':
            print(f"WARNING: {input_path}: BurnedInAnnotation is YES - the pixels may show "
                  "names or IDs; review the image or exclude it before sharing", file=sys.stderr)
            anonymized.append("BurnedInAnnotation is YES: pixel data needs manual review")

        # Vendor private tags frequently carry names, IDs, or dates
        if remove_private:
            ds.remove_private_tags()
            anonymized.append("private tags: removed")

        ds.PatientIdentityRemoved = 'YES'

        # Anonymize UIDs if present (optional - maintains referential integrity)
        # Uncomment if you want to anonymize UIDs as well
        # if hasattr(ds, 'StudyInstanceUID'):
        #     ds.StudyInstanceUID = pydicom.uid.generate_uid()
        # if hasattr(ds, 'SeriesInstanceUID'):
        #     ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        # if hasattr(ds, 'SOPInstanceUID'):
        #     ds.SOPInstanceUID = pydicom.uid.generate_uid()

        # Save anonymized file
        ds.save_as(output_path)

        return True, anonymized

    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description='Anonymize DICOM files by removing or replacing PHI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python anonymize_dicom.py input.dcm output.dcm
  python anonymize_dicom.py input.dcm output.dcm --patient-id ANON001
  python anonymize_dicom.py input.dcm output.dcm --patient-id ANON001 --patient-name "Anonymous^Patient"
        """
    )

    parser.add_argument('input', type=str, help='Input DICOM file')
    parser.add_argument('output', type=str, help='Output anonymized DICOM file')
    parser.add_argument('--patient-id', type=str, default='ANONYMOUS',
                       help='Replacement patient ID (default: ANONYMOUS)')
    parser.add_argument('--patient-name', type=str, default='ANONYMOUS',
                       help='Replacement patient name (default: ANONYMOUS)')
    parser.add_argument('--keep-private', action='store_true',
                       help='Keep vendor private tags (removed by default because they often contain PHI)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed anonymization information')

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)

    # Anonymize the file
    print(f"Anonymizing: {args.input}")
    success, result = anonymize_dicom(args.input, args.output,
                                     args.patient_id, args.patient_name,
                                     remove_private=not args.keep_private)

    if success:
        print(f"✓ Successfully anonymized DICOM file: {args.output}")
        if args.verbose:
            print(f"\nAnonymized {len(result)} fields:")
            for item in result:
                print(f"  - {item}")
    else:
        print(f"✗ Error: {result}")
        sys.exit(1)


if __name__ == '__main__':
    main()
