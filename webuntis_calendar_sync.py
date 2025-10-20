#!/usr/bin/env python3
"""
WebUntis to iPhone Calendar Sync Script

This script fetches your timetable from WebUntis and converts it to an iCal (.ics) file
that can be imported into iPhone Calendar or subscribed to via a web server.

Key API Endpoints discovered:
- Token refresh: /WebUntis/api/token/new
- Timetable entries: /WebUntis/api/rest/view/v1/timetable/entries

Parameters:
- start: Start date (YYYY-MM-DD)
- end: End date (YYYY-MM-DD)
- format: 4 (grid format)
- resourceType: STUDENT
- resources: <person_id>
- timetableType: MY_TIMETABLE

Authentication: Uses JWT Bearer tokens in Authorization header
Required headers:
- authorization: Bearer <token>
- tenant-id: <tenant_id>
- x-webuntis-api-school-year-id: <school_year_id>
"""

import requests
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from typing import List, Dict, Optional
import pytz


class WebUntisCalendarSync:
    def __init__(self, server: str, school: str = None, username: str = None,
                 password: str = None, session_token: str = None, cookies: str = None):
        """
        Initialize the WebUntis Calendar Sync

        Args:
            server: WebUntis server (e.g., 'peleus.webuntis.com')
            school: School name/identifier (required if using username/password)
            username: Your WebUntis username (optional if using session_token)
            password: Your WebUntis password (optional if using session_token)
            session_token: Existing session token (Bearer JWT) from browser
            cookies: Cookie string from browser (format: "name1=value1; name2=value2")
        """
        self.server = server
        self.school = school
        self.username = username
        self.password = password
        self.base_url = f"https://{server}/WebUntis"

        self.session = requests.Session()
        self.bearer_token = session_token
        self.tenant_id = None
        self.person_id = None
        self.school_year_id = None

        # If cookies provided, add them to session
        if cookies:
            self._parse_cookies(cookies)

        # If session token provided, extract info from it
        if session_token:
            self._parse_session_token(session_token)

    def _parse_cookies(self, cookie_string: str):
        """Parse cookie string and add to session"""
        try:
            # Parse cookies from string format "name1=value1; name2=value2"
            for cookie in cookie_string.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    self.session.cookies.set(name, value, domain=self.server)
            print(f"✓ Added {len(self.session.cookies)} cookies to session")
        except Exception as e:
            print(f"Warning: Could not parse cookies: {str(e)}")

    def _parse_session_token(self, token: str):
        """Parse session token to extract tenant_id and person_id"""
        try:
            import base64
            payload = token.split('.')[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.b64decode(payload))

            self.tenant_id = decoded.get('tenant_id')
            self.person_id = decoded.get('person_id')
            self.username = decoded.get('username', 'user')

            print(f"✓ Parsed session token")
            print(f"  Username: {self.username}")
            print(f"  Person ID: {self.person_id}")
            print(f"  Tenant ID: {self.tenant_id}")

        except Exception as e:
            print(f"Warning: Could not parse session token: {str(e)}")

    def login(self) -> bool:
        """
        Authenticate with WebUntis using JSON-RPC API

        Returns:
            True if login successful, False otherwise
        """
        url = f"{self.base_url}/jsonrpc.do"
        params = {"school": self.school}

        payload = {
            "id": "request_id",
            "method": "authenticate",
            "params": {
                "user": self.username,
                "password": self.password,
                "client": "PythonSync"
            },
            "jsonrpc": "2.0"
        }

        try:
            response = self.session.post(url, json=payload, params=params)
            response.raise_for_status()

            result = response.json()

            if "result" in result:
                # Store session info
                session_id = result["result"]["sessionId"]
                self.person_id = result["result"]["personId"]

                # Get bearer token
                self._get_bearer_token()

                print(f"✓ Successfully logged in as {self.username}")
                print(f"  Person ID: {self.person_id}")
                return True
            else:
                print(f"✗ Login failed: {result.get('error', {}).get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"✗ Login error: {str(e)}")
            return False

    def _get_bearer_token(self):
        """Get/refresh the Bearer token for REST API calls"""
        url = f"{self.base_url}/api/token/new"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            self.bearer_token = response.text.strip('"')

            # Extract tenant_id from token payload (JWT)
            import base64
            payload = self.bearer_token.split('.')[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.b64decode(payload))

            self.tenant_id = decoded.get('tenant_id')
            self.person_id = decoded.get('person_id', self.person_id)

            # Get school year ID from headers if available
            if 'x-sessiondurationmilliseconds' in response.headers:
                print(f"  Session duration: {int(response.headers['x-sessiondurationmilliseconds'])/60000:.0f} minutes")

        except Exception as e:
            print(f"Warning: Could not get bearer token: {str(e)}")

    def get_school_years(self) -> List[Dict]:
        """Get available school years"""
        url = f"{self.base_url}/api/rest/view/v1/schoolyears"

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'tenant-id': str(self.tenant_id)
        }

        try:
            print(f"\nFetching school years...")
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            school_years = response.json()
            print(f"  Found {len(school_years)} school years")

            # Find current school year
            for sy in school_years:
                if sy.get('isCurrent'):
                    self.school_year_id = sy['id']
                    print(f"  ✓ Current school year: {sy['name']} (ID: {sy['id']})")
                    return school_years

            # If no current school year found, use the most recent one
            if school_years and not self.school_year_id:
                self.school_year_id = school_years[0]['id']
                print(f"  ! No current school year found, using: {school_years[0]['name']} (ID: {school_years[0]['id']})")

            return school_years

        except Exception as e:
            print(f"✗ Error getting school years: {str(e)}")
            print(f"  This might cause issues fetching timetable")
            return []

    def fetch_timetable(self, start_date: datetime, end_date: datetime, retry_with_refresh: bool = True) -> Dict:
        """
        Fetch timetable entries for a date range

        Args:
            start_date: Start date
            end_date: End date
            retry_with_refresh: If True, will try to refresh token on 401 error

        Returns:
            Dictionary containing timetable data
        """
        url = f"{self.base_url}/api/rest/view/v1/timetable/entries"

        params = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'format': '4',  # Grid format
            'resourceType': 'STUDENT',
            'resources': str(self.person_id),
            'periodTypes': '',
            'timetableType': 'MY_TIMETABLE'
        }

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'tenant-id': str(self.tenant_id),
            'x-webuntis-api-school-year-id': str(self.school_year_id)
        }

        print(f"\n  Requesting timetable with:")
        print(f"    School Year ID: {self.school_year_id}")
        print(f"    Person ID: {self.person_id}")
        print(f"    Tenant ID: {self.tenant_id}")
        print(f"    Token (first 50 chars): {self.bearer_token[:50]}...")
        print(f"\n  Headers being sent:")
        for key, value in headers.items():
            if key == 'Authorization':
                print(f"    {key}: Bearer {value.split('Bearer ')[1][:50]}...")
            else:
                print(f"    {key}: {value}")
        print(f"\n  Full URL: {url}")

        try:
            response = self.session.get(url, params=params, headers=headers)
            print(f"\n    Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"    Response headers: {dict(response.headers)}")
                try:
                    print(f"    Response body: {response.text[:500]}")
                except:
                    pass

            if response.status_code == 401:
                if retry_with_refresh:
                    print(f"\n  Token expired, attempting to refresh...")
                    self._refresh_token()
                    if self.bearer_token:
                        print(f"  Token refreshed! Retrying...")
                        return self.fetch_timetable(start_date, end_date, retry_with_refresh=False)

                print(f"\n✗ Authentication failed. Possible reasons:")
                print(f"  - Token expired and refresh failed")
                print(f"  - Get a fresh token from your browser")
                print(f"  - Make sure you're logged in to WebUntis")

            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"✗ Error fetching timetable: {str(e)}")
            return {}

    def _refresh_token(self):
        """Try to refresh the Bearer token using the current session"""
        print(f"  ⚠ Token refresh not supported without session cookies")
        print(f"  Please get a fresh token from your browser:")
        print(f"    1. Press F12 → Network tab")
        print(f"    2. Refresh page")
        print(f"    3. Click any API request")
        print(f"    4. Copy the 'Authorization: Bearer ...' token")
        return False

    def convert_to_ical(self, timetable_data: Dict, timezone: str = 'Europe/Berlin') -> Calendar:
        """
        Convert WebUntis timetable data to iCal format

        Args:
            timetable_data: Timetable data from WebUntis API
            timezone: Timezone for events (default: Europe/Berlin)

        Returns:
            Calendar object
        """
        cal = Calendar()
        cal.add('prodid', '-//WebUntis Calendar Sync//Python//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f'WebUntis - {self.username}')
        cal.add('x-wr-timezone', timezone)

        tz = pytz.timezone(timezone)

        days = timetable_data.get('days', [])
        event_count = 0

        for day in days:
            date = day.get('date')
            entries = day.get('gridEntries', [])

            for entry in entries:
                event = Event()

                # Get duration
                duration = entry.get('duration', {})
                start_str = duration.get('start')  # Format: 2025-10-23T07:35
                end_str = duration.get('end')

                if not start_str or not end_str:
                    continue

                # Parse datetime
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)

                # Localize to timezone
                start_dt = tz.localize(start_dt)
                end_dt = tz.localize(end_dt)

                # Get subject
                position2 = entry.get('position2', [])
                subject = position2[0]['current']['shortName'] if position2 else 'Unknown'
                subject_long = position2[0]['current']['longName'] if position2 else subject

                # Get teacher
                position1 = entry.get('position1', [])
                teachers = ', '.join([p['current']['shortName'] for p in position1]) if position1 else ''

                # Get room
                position3 = entry.get('position3', [])
                room = position3[0]['current']['shortName'] if position3 else ''

                # Get status and type
                status = entry.get('status', 'REGULAR')
                entry_type = entry.get('type', 'NORMAL_TEACHING_PERIOD')

                # Build event
                event.add('summary', f"{subject}")

                # Build description
                description_parts = []
                if subject_long != subject:
                    description_parts.append(f"Subject: {subject_long}")
                if teachers:
                    description_parts.append(f"Teacher: {teachers}")
                if room:
                    description_parts.append(f"Room: {room}")
                description_parts.append(f"Status: {status}")

                # Add notes if available
                notes = entry.get('notesAll', '')
                if notes:
                    description_parts.append(f"\nNotes: {notes}")

                event.add('description', '\n'.join(description_parts))
                event.add('dtstart', start_dt)
                event.add('dtend', end_dt)

                if room:
                    event.add('location', room)

                # Add unique ID
                uid = f"{'-'.join(map(str, entry.get('ids', [])))}@{self.server}"
                event.add('uid', uid)

                # Add status
                if status == 'CANCELLED':
                    event.add('status', 'CANCELLED')
                else:
                    event.add('status', 'CONFIRMED')

                # Add categories
                event.add('categories', [subject, 'WebUntis'])

                # Add created/modified timestamps
                now = datetime.now(tz)
                event.add('dtstamp', now)
                event.add('created', now)
                event.add('last-modified', now)

                cal.add_component(event)
                event_count += 1

        print(f"✓ Created calendar with {event_count} events")
        return cal

    def save_ical(self, calendar: Calendar, filename: str):
        """Save calendar to .ics file"""
        with open(filename, 'wb') as f:
            f.write(calendar.to_ical())
        print(f"✓ Saved calendar to: {filename}")

    def sync(self, weeks_ahead: int = 4, output_file: str = 'webuntis_calendar.ics'):
        """
        Main sync function

        Args:
            weeks_ahead: Number of weeks to fetch (default: 4)
            output_file: Output .ics filename
        """
        print("=" * 60)
        print("WebUntis to iPhone Calendar Sync")
        print("=" * 60)

        # Login only if we don't have a session token
        if not self.bearer_token:
            if not self.login():
                return False
        else:
            print("\nUsing provided session token...")

        # Get school years
        self.get_school_years()

        # Calculate date range
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=weeks_ahead)

        print(f"\nFetching timetable from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

        # Fetch timetable
        timetable_data = self.fetch_timetable(start_date, end_date)

        if not timetable_data:
            print("✗ No timetable data received")
            return False

        # Convert to iCal
        print("\nConverting to iCal format...")
        calendar = self.convert_to_ical(timetable_data)

        # Save
        self.save_ical(calendar, output_file)

        print("\n" + "=" * 60)
        print("Sync completed successfully!")
        print("=" * 60)
        print("\nTo add to iPhone:")
        print("1. Email the .ics file to yourself")
        print("2. Open the email on your iPhone")
        print("3. Tap the .ics attachment")
        print("4. Choose 'Add All' to add events to your calendar")
        print("\nAlternatively:")
        print("- Use AirDrop to send the file to your iPhone")
        print("- Host the .ics file on a web server and subscribe via URL")

        return True

    def logout(self):
        """Logout from WebUntis"""
        url = f"{self.base_url}/jsonrpc.do"
        params = {"school": self.school}

        payload = {
            "id": "request_id",
            "method": "logout",
            "params": {},
            "jsonrpc": "2.0"
        }

        try:
            self.session.post(url, json=payload, params=params)
        except:
            pass


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Sync WebUntis timetable to iPhone Calendar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using session token (recommended - get from browser DevTools):
  python webuntis_calendar_sync.py --server peleus.webuntis.com --token "eyJraWQi..."

  # Using username/password:
  python webuntis_calendar_sync.py --server peleus.webuntis.com --school "SchoolName" \\
      --username "student123" --password "mypassword"

To get your session token:
  1. Open WebUntis in your browser
  2. Login normally
  3. Open Developer Tools (F12)
  4. Go to Network tab
  5. Click on any API request
  6. Copy the "authorization: Bearer ..." header value (the long JWT token)
        """
    )
    parser.add_argument('--server', required=True, help='WebUntis server (e.g., peleus.webuntis.com)')
    parser.add_argument('--token', '--session-token', dest='token', help='Session token (Bearer JWT from browser)')
    parser.add_argument('--cookies', help='Cookies from browser (format: "name1=value1; name2=value2")')
    parser.add_argument('--school', help='School name/identifier (required if using username/password)')
    parser.add_argument('--username', help='Your WebUntis username')
    parser.add_argument('--password', help='Your WebUntis password')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to fetch (default: 4)')
    parser.add_argument('--output', default='webuntis_calendar.ics', help='Output filename (default: webuntis_calendar.ics)')
    parser.add_argument('--timezone', default='Europe/Berlin', help='Timezone (default: Europe/Berlin)')

    args = parser.parse_args()

    # Validate authentication method
    if not args.token and not (args.school and args.username and args.password):
        parser.error("Either --token or (--school, --username, --password) must be provided")

    sync = WebUntisCalendarSync(
        server=args.server,
        school=args.school,
        username=args.username,
        password=args.password,
        session_token=args.token,
        cookies=args.cookies
    )

    try:
        sync.sync(weeks_ahead=args.weeks, output_file=args.output)
    finally:
        if not args.token:  # Only logout if we logged in with credentials
            sync.logout()


if __name__ == '__main__':
    main()