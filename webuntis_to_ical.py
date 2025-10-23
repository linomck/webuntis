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
import os
import time
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from typing import List, Dict, Optional
import pytz
from webuntis_auto_login import WebUntisAutoLogin


class WebUntisCalendarSync:
    def __init__(self, server: str, session_data: dict = None, school: str = None):
        """
        Initialize the WebUntis Calendar Sync

        Args:
            server: WebUntis server (e.g., 'peleus.webuntis.com')
            session_data: Session data dictionary from WebUntisAutoLogin containing cookies, bearer_token, person_id, tenant_id
            school: School name/identifier (optional, for backward compatibility)
        """
        self.server = server
        self.school = school
        self.base_url = f"https://{server}/WebUntis"

        self.session = requests.Session()
        self.bearer_token = None
        self.tenant_id = None
        self.person_id = None
        self.school_year_id = None
        self.username = None

        # If session_data provided, load cookies and token from it
        if session_data:
            self._load_session_data(session_data)

    def _load_session_data(self, session_data: dict):
        """Load session data from WebUntisAutoLogin"""
        try:
            print("✓ Loading session data from auto login")

            cookies = session_data.get('cookies', [])
            self.bearer_token = session_data.get('bearer_token')
            self.person_id = session_data.get('person_id')
            self.tenant_id = session_data.get('tenant_id')
            saved_time = session_data.get('timestamp', 0)

            # Calculate age
            age_minutes = (time.time() - saved_time) / 60
            print(f"  Session age: {age_minutes:.1f} minutes")

            # Load cookies into session
            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie.get('name'),
                    value=cookie.get('value'),
                    domain=cookie.get('domain'),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', False)
                )

            print(f"✓ Loaded {len(cookies)} cookies")

            # Check if bearer token is available
            if self.bearer_token:
                print(f"✓ Bearer token loaded from session")
                print(f"  Person ID: {self.person_id}")
                print(f"  Tenant ID: {self.tenant_id}")
            else:
                print(f"  ⚠ No bearer token in session data")

        except Exception as e:
            print(f"✗ Error loading session data: {str(e)}")
            import traceback
            traceback.print_exc()


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

        print(f"\nFetching timetable from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

        try:
            response = self.session.get(url, params=params, headers=headers)

            if response.status_code == 401:
                print(f"\n✗ Authentication failed. Session may have expired.")
                print(f"  Please run the script again to re-authenticate.")
                return {}

            response.raise_for_status()

            data = response.json()

            # Count events
            event_count = sum(len(day.get('gridEntries', [])) for day in data.get('days', []))
            print(f"✓ Fetched {event_count} timetable entries")

            return data

        except Exception as e:
            print(f"✗ Error fetching timetable: {str(e)}")
            return {}

    def convert_to_ical(self, timetable_data: Dict, timezone: str = 'Europe/Berlin',
                       filter_type: Optional[str] = None, calendar_name_suffix: str = '') -> Calendar:
        """
        Convert WebUntis timetable data to iCal format

        Args:
            timetable_data: Timetable data from WebUntis API
            timezone: Timezone for events (default: Europe/Berlin)
            filter_type: Optional filter to only include specific event types (e.g., 'EXAM')
            calendar_name_suffix: Optional suffix for calendar name

        Returns:
            Calendar object
        """
        cal = Calendar()
        cal.add('prodid', '-//WebUntis Calendar Sync//Python//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')

        cal_name = f'WebUntis - {self.username}'
        if calendar_name_suffix:
            cal_name += f' - {calendar_name_suffix}'
        cal.add('x-wr-calname', cal_name)
        cal.add('x-wr-timezone', timezone)

        tz = pytz.timezone(timezone)

        days = timetable_data.get('days', [])
        event_count = 0

        for day in days:
            date = day.get('date')
            entries = day.get('gridEntries', [])

            for entry in entries:
                # Get status and type early to filter
                entry_type = entry.get('type', 'NORMAL_TEACHING_PERIOD')

                # Apply filter if specified
                if filter_type and entry_type != filter_type:
                    continue
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

    def sync(self, weeks_ahead: int = 4, output_file: str = 'webuntis_calendar.ics',
             exams_output_file: str = 'webuntis_exams.ics'):
        """
        Main sync function

        Args:
            weeks_ahead: Number of weeks to fetch (default: 4)
            output_file: Output .ics filename for all events
            exams_output_file: Output .ics filename for exams only
        """
        print("=" * 60)
        print("WebUntis to iPhone Calendar Sync")
        print("=" * 60)

        # Check if we have a bearer token
        if not self.bearer_token:
            print("\n✗ No session token found. Please provide credentials or session file.")
            return False

        # Get school years
        self.get_school_years()

        # Calculate date range
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=weeks_ahead)

        # Fetch timetable
        timetable_data = self.fetch_timetable(start_date, end_date)

        if not timetable_data:
            print("✗ No timetable data received")
            return False

        # Convert to iCal - All events
        print("\nConverting to iCal format (all events)...")
        calendar = self.convert_to_ical(timetable_data)

        # Save all events calendar
        self.save_ical(calendar, output_file)

        # Convert to iCal - Exams only
        print("\nConverting to iCal format (exams only)...")
        exams_calendar = self.convert_to_ical(timetable_data, filter_type='EXAM',
                                              calendar_name_suffix='Exams')

        # Save exams calendar
        self.save_ical(exams_calendar, exams_output_file)

        print("\n" + "=" * 60)
        print("✓ Sync completed successfully!")
        print("=" * 60)
        print("\nGenerated files:")
        print(f"  - {output_file} (all events)")
        print(f"  - {exams_output_file} (exams only)")
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
    """Main entry point - performs auto login and syncs calendar"""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(
        description='Sync WebUntis timetable to iPhone Calendar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using credentials from .env file:
  python webuntis_to_ical.py

  # Specify number of weeks and output file:
  python webuntis_to_ical.py --weeks 8 --output my_calendar.ics

  # Run in headless mode:
  python webuntis_to_ical.py --headless
        """
    )
    parser.add_argument('--server', default='peleus.webuntis.com',
                        help='WebUntis server (default: peleus.webuntis.com)')
    parser.add_argument('--weeks', type=int, default=4,
                        help='Number of weeks to fetch (default: 4)')
    parser.add_argument('--output', default='webuntis_calendar.ics',
                        help='Output filename for all events (default: webuntis_calendar.ics)')
    parser.add_argument('--exams-output', default='webuntis_exams.ics',
                        help='Output filename for exams only (default: webuntis_exams.ics)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')

    args = parser.parse_args()

    # Get credentials from environment
    username = os.getenv("FSV_USERNAME")
    password = os.getenv("FSV_PASSWORD")

    if not username or not password:
        print("✗ FSV_USERNAME and FSV_PASSWORD must be set in .env file")
        print("\nExample .env file:")
        print("FSV_USERNAME=your_username")
        print("FSV_PASSWORD=your_password")
        return

    # Perform auto login
    print("Performing auto login to WebUntis...")
    with WebUntisAutoLogin(username, password, headless=args.headless) as auto_login:
        session_data = auto_login.login()

        if not session_data:
            print("✗ Auto login failed. Cannot proceed with calendar sync.")
            return

        print("\nSession data received, initializing calendar sync...")

    # Create sync instance with session data
    sync = WebUntisCalendarSync(
        server=args.server,
        session_data=session_data
    )

    try:
        sync.sync(weeks_ahead=args.weeks, output_file=args.output,
                  exams_output_file=args.exams_output)
    finally:
        sync.logout()


if __name__ == '__main__':
    main()

