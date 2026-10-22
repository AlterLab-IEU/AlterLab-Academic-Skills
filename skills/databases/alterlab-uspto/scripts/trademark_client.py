#!/usr/bin/env python3
"""
USPTO Trademark API Helper

Retrieves trademark status, owners, goods/services and prosecution history.

Backends:
    web (default without a key) - the public TSDR status page
        (tsdr.uspto.gov/statusview/sn<serial>), parsed by uspto_public.py; no key.
    api (default with a key)    - the TSDR API (tsdrapi.uspto.gov) with a TSDR key from
        https://account.uspto.gov/api-manager/ (separate from the ODP key), sent in the
        "USPTO-API-KEY" header; 60 requests/minute, 4/minute for PDF and ZIP downloads.
        --backend api without a key exits with an error instead of using the web page.

Environment variables:
    USPTO_TSDR_API_KEY - optional TSDR API key (USPTO_API_KEY is accepted as a fallback)

The old Trademark Assignment Search host (assignment-api.uspto.gov) no longer
resolves (verified 2026-09); ownership changes are in the TSDR status record
and in the USPTO trademark assignment bulk data on data.uspto.gov.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any

try:
    import requests  # only the keyed TSDR API backend needs it
except ImportError:  # pragma: no cover
    requests = None

try:
    import uspto_public
except ImportError:  # imported as scripts.trademark_client
    from scripts import uspto_public


class TrademarkClient:
    """Client for USPTO Trademark APIs."""

    TSDR_BASE_URL = "https://tsdrapi.uspto.gov/ts/cd"
    TIMEOUT = 60

    def __init__(self, api_key: Optional[str] = None, backend: str = "auto"):
        """
        Initialize the client.

        Args:
            api_key: optional TSDR API key (defaults to USPTO_TSDR_API_KEY, then USPTO_API_KEY)
            backend: "auto" (api with a key, else the keyless web page), "web", or "api"
        """
        self.api_key = api_key or os.getenv("USPTO_TSDR_API_KEY") or os.getenv("USPTO_API_KEY")
        if backend == "api" and not self.api_key:
            raise ValueError("The TSDR API backend needs USPTO_TSDR_API_KEY (account.uspto.gov/"
                             "api-manager) or api_key=. Without a key use backend='web' "
                             "(the public TSDR status page).")
        self.backend = "api" if (backend == "api" or (backend == "auto" and self.api_key)) else "web"
        if self.backend == "web":
            if backend == "auto":
                print("USPTO_TSDR_API_KEY not set: using the keyless TSDR status page "
                      "(tsdr.uspto.gov/statusview).", file=sys.stderr)
            self.headers = {}
            return

        # TSDR reads the key from "USPTO-API-KEY"; an X-Api-Key header is ignored
        # and the request is treated as keyless (HTTP 401).
        self.headers = {"USPTO-API-KEY": self.api_key}

    def get_trademark_by_serial(self, serial_number: str) -> Optional[Dict]:
        """
        Get trademark information by serial number.

        Args:
            serial_number: Trademark serial number (e.g., "87654321")

        Returns:
            Trademark data dictionary or None if not found
        """
        if self.backend == "web":
            return self._web(serial_number, registration=False)
        # casestatus = case status record; casedocs would return the document list
        url = f"{self.TSDR_BASE_URL}/casestatus/sn{serial_number}/info.json"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_trademark_by_registration(self, registration_number: str) -> Optional[Dict]:
        """
        Get trademark information by registration number.

        Args:
            registration_number: Trademark registration number (e.g., "5678901")

        Returns:
            Trademark data dictionary or None if not found
        """
        if self.backend == "web":
            return self._web(registration_number, registration=True)
        url = f"{self.TSDR_BASE_URL}/casestatus/rn{registration_number}/info.json"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def _web(self, number: str, registration: bool) -> Optional[Dict]:
        try:
            return uspto_public.trademark(number, registration=registration)
        except SystemExit:  # not found / unavailable
            return None

    def get_trademark_status(self, serial_or_registration: str) -> Dict[str, Any]:
        """
        Get current status summary for a trademark.

        Args:
            serial_or_registration: Serial or registration number

        Returns:
            Status summary dictionary with:
                - mark_text: Text of the mark
                - status: Current status
                - filing_date: Application filing date
                - registration_number: Registration number if registered
                - registration_date: Registration date if registered
        """
        # Try serial number first
        data = self.get_trademark_by_serial(serial_or_registration)

        # If not found, try registration number
        if not data:
            data = self.get_trademark_by_registration(serial_or_registration)

        if not data:
            return {}

        if self.backend == "web":
            return {
                'mark_text': data.get('mark_text'),
                'status': " - ".join(x for x in (data.get('tm5_status'), data.get('status')) if x),
                'status_date': data.get('status_date'),
                'filing_date': data.get('filing_date'),
                'application_number': data.get('serial_number'),
                'registration_number': data.get('registration_number'),
                'registration_date': data.get('registration_date'),
                'mark_drawing_code': None,
                'is_registered': data.get('is_registered', False),
                'source': data.get('source'),
            }

        tm = data.get('TradeMarkAppln', {})

        return {
            'mark_text': tm.get('MarkVerbalElementText'),
            'status': tm.get('MarkCurrentStatusExternalDescriptionText'),
            'status_date': tm.get('MarkCurrentStatusDate'),
            'filing_date': tm.get('ApplicationDate'),
            'application_number': tm.get('ApplicationNumber'),
            'registration_number': tm.get('RegistrationNumber'),
            'registration_date': tm.get('RegistrationDate'),
            'mark_drawing_code': tm.get('MarkDrawingCode'),
            'is_registered': tm.get('RegistrationNumber') is not None
        }

    def get_goods_and_services(self, serial_or_registration: str) -> List[Dict]:
        """
        Get goods and services classification for a trademark.

        Args:
            serial_or_registration: Serial or registration number

        Returns:
            List of goods/services entries with classes
        """
        data = self.get_trademark_by_serial(serial_or_registration)
        if not data:
            data = self.get_trademark_by_registration(serial_or_registration)

        if not data:
            return []

        if self.backend == "web":
            return data.get('goods_and_services', [])
        tm = data.get('TradeMarkAppln', {})
        return tm.get('GoodsAndServices', [])

    def get_owner_info(self, serial_or_registration: str) -> List[Dict]:
        """
        Get owner/applicant information for a trademark.

        Args:
            serial_or_registration: Serial or registration number

        Returns:
            List of owner entries
        """
        data = self.get_trademark_by_serial(serial_or_registration)
        if not data:
            data = self.get_trademark_by_registration(serial_or_registration)

        if not data:
            return []

        if self.backend == "web":
            return [{'name': data.get('owner_name'), 'entity_type': data.get('owner_entity_type')}]
        tm = data.get('TradeMarkAppln', {})
        return tm.get('Owners', [])

    def get_prosecution_history(self, serial_or_registration: str) -> List[Dict]:
        """
        Get prosecution history for a trademark.

        Args:
            serial_or_registration: Serial or registration number

        Returns:
            List of prosecution events
        """
        data = self.get_trademark_by_serial(serial_or_registration)
        if not data:
            data = self.get_trademark_by_registration(serial_or_registration)

        if not data:
            return []

        if self.backend == "web":
            return data.get('prosecution_history', [])
        tm = data.get('TradeMarkAppln', {})
        return tm.get('ProsecutionHistoryEntry', [])

    def check_trademark_health(self, serial_or_registration: str) -> Dict[str, Any]:
        """
        Check trademark health and identify issues.

        Args:
            serial_or_registration: Serial or registration number

        Returns:
            Health check dictionary with alerts and status
        """
        status = self.get_trademark_status(serial_or_registration)

        if not status:
            return {'error': 'Trademark not found'}

        current_status = status.get('status', '').upper()
        alerts = []

        # Check for problematic statuses (TM5 descriptors on the web backend: LIVE/... or DEAD/...)
        if current_status.startswith('DEAD/'):
            alerts.append('⚠️  DEAD - ' + current_status.split(' - ')[0])
        elif 'ABANDON' in current_status:
            alerts.append('⚠️  ABANDONED - Mark is no longer active')
        elif 'CANCELLED' in current_status:
            alerts.append('⚠️  CANCELLED - Registration cancelled')
        elif 'EXPIRED' in current_status:
            alerts.append('⚠️  EXPIRED - Registration has expired')
        elif 'SUSPENDED' in current_status:
            alerts.append('⏸️  SUSPENDED - Examination suspended')
        elif 'PUBLISHED' in current_status:
            alerts.append('📢 PUBLISHED - In opposition period')
        elif 'REGISTERED' in current_status or current_status.startswith('LIVE/REGISTRATION'):
            alerts.append('✅ ACTIVE - Mark is registered and active')
        elif 'PENDING' in current_status:
            alerts.append('⏳ PENDING - Application under examination')

        next_deadline = _next_maintenance(status.get('registration_date'))
        if next_deadline and status.get('is_registered'):
            alerts.append(f"📅 Next maintenance filing due {next_deadline['due']} "
                          f"({next_deadline['filing']}; window opens {next_deadline['window_opens']}, "
                          f"6-month grace period after)")

        return {
            'mark': status.get('mark_text'),
            'status': current_status,
            'status_date': status.get('status_date'),
            'alerts': alerts,
            'next_maintenance': next_deadline,
            'needs_attention': len([a for a in alerts if '⚠️' in a]) > 0
        }


def _next_maintenance(registration_date: Optional[str]) -> Optional[Dict[str, str]]:
    """Next Section 8 (year 6) or Sections 8 & 9 (every 10 years) deadline after today."""
    from datetime import date, datetime

    if not registration_date:
        return None
    for fmt in ("%b. %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            reg = datetime.strptime(registration_date.replace("Sept.", "Sep."), fmt).date()
            break
        except ValueError:
            continue
    else:
        return None
    today = date.today()

    def anniversary(years: int) -> date:
        try:
            return reg.replace(year=reg.year + years)
        except ValueError:  # 29 Feb
            return reg.replace(year=reg.year + years, day=28)

    if anniversary(6) >= today:
        due, filing = anniversary(6), "Section 8 declaration of use (between years 5 and 6)"
    else:
        n = 10
        while anniversary(n) < today:
            n += 10
        due, filing = anniversary(n), f"Sections 8 & 9 renewal ({n}-year)"
    return {"due": due.isoformat(), "window_opens": anniversary(
        (6 if "Section 8 declaration" in filing else int(filing.split("(")[1].split("-")[0])) - 1
    ).isoformat(), "filing": filing}


def main():
    """Command-line interface for trademark search."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Query USPTO Trademark Status & Document Retrieval (TSDR) API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get trademark by serial number
  %(prog)s --serial 87654321

  # Get trademark by registration number
  %(prog)s --registration 5678901

  # Get status summary
  %(prog)s --status 87654321

  # Check trademark health
  %(prog)s --health 87654321

  # Get goods and services
  %(prog)s --goods 87654321

  # Get owner information
  %(prog)s --owner 87654321

  # Get prosecution history
  %(prog)s --prosecution 87654321

Environment:
  Keyless by default (the public TSDR status page). Optionally set USPTO_TSDR_API_KEY
  (or USPTO_API_KEY) to a TSDR key from https://account.uspto.gov/api-manager/ to use
  the TSDR API instead (--backend api).
        """
    )

    # Main operation arguments (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--serial', '-s', help='Get trademark by serial number')
    group.add_argument('--registration', '-r', help='Get trademark by registration number')
    group.add_argument('--status', help='Get status summary (serial or registration number)')
    group.add_argument('--health', help='Check trademark health (serial or registration number)')
    group.add_argument('--goods', '-g', help='Get goods and services (serial or registration number)')
    group.add_argument('--owner', '-o', help='Get owner information (serial or registration number)')
    group.add_argument('--prosecution', '-p', help='Get prosecution history (serial or registration number)')

    # API key option
    parser.add_argument('--api-key', '-k', help='TSDR API key (overrides USPTO_TSDR_API_KEY)')
    parser.add_argument('--backend', choices=['auto', 'web', 'api'], default='auto',
                        help='auto (default): api with a key, else the keyless TSDR status page')

    args = parser.parse_args()

    try:
        client = TrademarkClient(api_key=args.api_key, backend=args.backend)

        if args.serial:
            result = client.get_trademark_by_serial(args.serial)
        elif args.registration:
            result = client.get_trademark_by_registration(args.registration)
        elif args.status:
            result = client.get_trademark_status(args.status)
        elif args.health:
            result = client.check_trademark_health(args.health)
        elif args.goods:
            result = client.get_goods_and_services(args.goods)
        elif args.owner:
            result = client.get_owner_info(args.owner)
        elif args.prosecution:
            result = client.get_prosecution_history(args.prosecution)

        if result:
            print(json.dumps(result, indent=2))
        else:
            number = (args.serial or args.registration or args.status or
                     args.health or args.goods or args.owner or args.prosecution)
            print(f"Trademark {number} not found", file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        parser.error(str(e))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
