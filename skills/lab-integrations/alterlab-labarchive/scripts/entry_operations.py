#!/usr/bin/env python3
"""
LabArchives Entry Operations

Create text entries and upload file attachments on a notebook page.

LabArchives stores entries on *pages*: every write needs the notebook ID
(``nbid``) and the page's tree ID (``pid``). The API methods used here are
``entries/add_entry`` (POST, form field ``entry_data``) and
``entries/add_attachment`` (POST, raw file bytes as the body). Both are signed
the same way as every other call — ``akid`` + ``expires`` + ``sig`` query
parameters — so the access password is never sent over the wire.

The ``labarchivespy`` wrapper only issues GET requests; this script reuses its
signing helpers for the POSTs. For a maintained client that also handles page
creation and path navigation, see ``labapi`` (``uv pip install labapi``).
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import yaml


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        print("   Run setup_config.py first to create configuration")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)


def init_client(config):
    """Initialize LabArchives API client"""
    try:
        from labarchivespy.client import Client
        return Client(
            config['api_url'],
            config['access_key_id'],
            config['access_password']
        )
    except ImportError:
        print("❌ labarchives-py package not installed")
        print('   Install with: uv pip install "git+https://github.com/mcmero/labarchives-py"')
        sys.exit(1)


def get_user_id(client, config):
    """Get user ID via authentication"""
    login_params = {
        'login_or_email': config['user_email'],
        'password': config['user_external_password']
    }

    try:
        response = client.make_call('users', 'user_access_info', params=login_params)

        if response.status_code == 200:
            uid = ET.fromstring(response.content)[0].text
            return uid
        else:
            print(f"❌ Authentication failed: HTTP {response.status_code}")
            print(f"   Response: {response.content.decode('utf-8')[:200]}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        sys.exit(1)


def signed_post(client, config, api_class, api_method, params, data=None):
    """POST to a LabArchives API method with the standard akid/expires/sig signing.

    Parameters are URL-encoded here (the wrapper's GET helper does not encode
    them). ``data`` is either a dict (form fields) or bytes (a raw file body).
    """
    import requests

    expires = client.get_expires_time()
    sig = client.get_signature(api_method, expires)  # already URL-quoted by the wrapper
    query = urlencode(params)
    url = (
        f"{config['api_url']}/{api_class}/{api_method}?{query}"
        f"&akid={config['access_key_id']}&expires={expires}&sig={sig}"
    )
    return requests.post(url, data=data, timeout=120)


def _entry_id(response):
    """Extract the new entry ID (``eid``) from an XML response, if present."""
    try:
        node = ET.fromstring(response.content).find('.//eid')
        return node.text if node is not None else None
    except ET.ParseError:
        return None


def create_entry(client, config, uid, nbid, pid, content, part_type='text entry'):
    """Add a text entry to a page (``entries/add_entry``)."""
    print(f"\n📝 Adding {part_type} to page {pid}")

    if part_type == 'text entry' and not content.lstrip().startswith('<'):
        content = f'<p>{content}</p>'  # rich-text entries expect HTML

    params = {'uid': uid, 'nbid': nbid, 'pid': pid, 'part_type': part_type}
    try:
        response = signed_post(client, config, 'entries', 'add_entry', params,
                               data={'entry_data': content})
    except Exception as e:
        print(f"❌ Error creating entry: {e}")
        return None

    if response.status_code == 200:
        eid = _entry_id(response)
        print(f"✅ Entry created{f' (eid {eid})' if eid else ''}")
        return eid or True

    print(f"❌ Entry creation failed: HTTP {response.status_code}")
    print(f"   Response: {response.content.decode('utf-8', 'replace')[:200]}")
    return None


def upload_attachment(client, config, uid, nbid, pid, file_path, caption=None):
    """Upload a file as a new attachment entry on a page (``entries/add_attachment``)."""
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    print(f"\n📎 Uploading attachment: {file_path.name}")
    print(f"   Size: {file_path.stat().st_size / 1024:.2f} KB")

    params = {
        'uid': uid,
        'nbid': nbid,
        'pid': pid,
        'filename': file_path.name,
        'caption': caption or file_path.name,
        'change_description': 'File uploaded via API',
    }
    try:
        response = signed_post(client, config, 'entries', 'add_attachment', params,
                               data=file_path.read_bytes())
    except Exception as e:
        print(f"❌ Error uploading attachment: {e}")
        return False

    if response.status_code == 200:
        print("✅ Attachment uploaded successfully")
        return True

    print(f"❌ Upload failed: HTTP {response.status_code}")
    print(f"   Response: {response.content.decode('utf-8', 'replace')[:200]}")
    return False


def batch_upload(client, config, uid, nbid, pid, directory):
    """Upload all files from a directory as attachments on one page"""
    directory = Path(directory)

    if not directory.is_dir():
        print(f"❌ Directory not found: {directory}")
        return

    files = [f for f in sorted(directory.glob('*')) if f.is_file()]

    if not files:
        print(f"❌ No files found in {directory}")
        return

    print(f"\n📦 Batch uploading {len(files)} files from {directory}")

    successful = 0
    failed = 0

    for file_path in files:
        if upload_attachment(client, config, uid, nbid, pid, file_path):
            successful += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"Batch upload complete: {successful} successful, {failed} failed")
    print("="*60)


def main():
    """Main command-line interface"""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--config', default='config.yaml',
                        help='Path to configuration file (default: config.yaml)')
    common.add_argument('--nbid', required=True, help='Notebook ID')
    common.add_argument('--pid', required=True,
                        help='Page tree ID (entries and attachments live on pages)')
    common.add_argument('--uid',
                        help='User ID (default: resolved from config via users/user_access_info)')

    parser = argparse.ArgumentParser(
        description='LabArchives Entry Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a rich-text entry to a page
  python3 entry_operations.py create --nbid 12345 --pid 67890 \\
    --content "PCR amplification successful"

  # Add an HTML entry
  python3 entry_operations.py create --nbid 12345 --pid 67890 \\
    --content "<p>Results:</p><ul><li>Sample A: Positive</li></ul>"

  # Upload an attachment to a page
  python3 entry_operations.py upload --nbid 12345 --pid 67890 --file data.csv

  # Upload every file in a directory
  python3 entry_operations.py batch-upload --nbid 12345 --pid 67890 \\
    --directory ./experiment_data/
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    create_parser = subparsers.add_parser('create', parents=[common],
                                          help='Add a text entry to a page')
    create_parser.add_argument('--content', required=True,
                               help='Entry content (HTML supported)')
    create_parser.add_argument('--part-type', default='text entry',
                               choices=['text entry', 'plain text entry', 'heading'],
                               help='Entry type (default: text entry)')
    create_parser.add_argument('--attachments', nargs='+',
                               help='Files to upload to the same page afterwards')

    upload_parser = subparsers.add_parser('upload', parents=[common],
                                          help='Upload an attachment to a page')
    upload_parser.add_argument('--file', required=True, help='File to upload')
    upload_parser.add_argument('--caption', help='Attachment caption (default: file name)')

    batch_parser = subparsers.add_parser('batch-upload', parents=[common],
                                         help='Upload all files from a directory')
    batch_parser.add_argument('--directory', required=True,
                              help='Directory containing files to upload')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load configuration and initialize
    config = load_config(args.config)
    client = init_client(config)
    uid = args.uid or get_user_id(client, config)

    # Execute command
    if args.command == 'create':
        created = create_entry(client, config, uid, args.nbid, args.pid,
                               args.content, args.part_type)
        if created and args.attachments:
            for attachment_path in args.attachments:
                upload_attachment(client, config, uid, args.nbid, args.pid, attachment_path)

    elif args.command == 'upload':
        upload_attachment(client, config, uid, args.nbid, args.pid, args.file, args.caption)

    elif args.command == 'batch-upload':
        batch_upload(client, config, uid, args.nbid, args.pid, args.directory)


if __name__ == '__main__':
    main()
