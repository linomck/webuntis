# WebUntis to iPhone Calendar Sync

A Python script that fetches your WebUntis timetable and converts it to an iCal (.ics) file that can be imported into iPhone Calendar.

## Features

- Fetches timetable data from WebUntis API
- Converts to standard iCal format compatible with iPhone Calendar
- Supports both session token and username/password authentication
- Includes all relevant information: subjects, teachers, rooms, times
- Handles cancelled/modified classes

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Using Session Token (Recommended)

This is the easiest method - you just copy your session token from your browser:

1. Open WebUntis in your browser and log in
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Click on any API request (refresh the page if needed)
5. In the request headers, find `authorization: Bearer ...`
6. Copy the long JWT token (starts with `eyJ...`)

Then run:

```bash
python webuntis_calendar_sync.py --server YOUR_SERVER.webuntis.com --token "eyJraWQi..."
```

Example:
```bash
python webuntis_calendar_sync.py \
    --server peleus.webuntis.com \
    --token "eyJraWQiOiI3MzIxNjk2MzYiLCJhbGciOiJSUzI1NiJ9..." \
    --weeks 8
```

### Method 2: Using Username/Password

```bash
python webuntis_calendar_sync.py \
    --server YOUR_SERVER.webuntis.com \
    --school "YOUR_SCHOOL_NAME" \
    --username "your_username" \
    --password "your_password" \
    --weeks 4
```

## Options

- `--server`: WebUntis server hostname (required)
- `--token`: Session token from browser (recommended method)
- `--school`: School identifier (required for username/password method)
- `--username`: Your WebUntis username
- `--password`: Your WebUntis password
- `--weeks`: Number of weeks to fetch (default: 4)
- `--output`: Output filename (default: webuntis_calendar.ics)
- `--timezone`: Timezone for events (default: Europe/Berlin)

## Adding to iPhone Calendar

### Option 1: Email

1. Email the generated `webuntis_calendar.ics` file to yourself
2. Open the email on your iPhone
3. Tap the .ics attachment
4. Choose "Add All" to add events to your calendar

### Option 2: AirDrop

1. Use AirDrop to send the .ics file to your iPhone
2. Open the file and tap "Add All"

### Option 3: Subscribe (requires web server)

1. Host the .ics file on a web server
2. On iPhone, go to Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar
3. Enter the URL to your .ics file
4. The calendar will auto-update when you regenerate the file

## API Endpoints Discovered

During development with Chrome DevTools, the following WebUntis API endpoints were identified:

### Authentication
- `POST /WebUntis/jsonrpc.do?school={school}` - JSON-RPC authentication
- `GET /WebUntis/api/token/new` - Get/refresh Bearer token

### Timetable Data
- `GET /WebUntis/api/rest/view/v1/schoolyears` - Get school years
- `GET /WebUntis/api/rest/view/v1/timetable/entries` - Get timetable entries
  - Parameters:
    - `start`: Start date (YYYY-MM-DD)
    - `end`: End date (YYYY-MM-DD)
    - `format`: 4 (grid format)
    - `resourceType`: STUDENT
    - `resources`: Person ID
    - `timetableType`: MY_TIMETABLE

### Required Headers
- `Authorization: Bearer {token}` - JWT Bearer token
- `tenant-id: {tenant_id}` - Tenant ID from token
- `x-webuntis-api-school-year-id: {id}` - Current school year ID

## Troubleshooting

### Session Token Expired

Session tokens typically expire after 30 minutes. If you get authentication errors:
1. Go back to your browser
2. Refresh the WebUntis page
3. Get a new session token using the same steps

### No Events Generated

- Make sure you have upcoming classes in your timetable
- Try increasing the `--weeks` parameter
- Check that your WebUntis account has access to view your timetable

### Import Issues on iPhone

- Make sure the .ics file was generated without errors
- Try importing a smaller date range first
- Check that the timezone is set correctly

## Automation

You can automate this sync with a cron job or scheduled task. Example crontab:

```bash
# Sync WebUntis calendar every day at 6 AM
0 6 * * * cd /path/to/script && python webuntis_calendar_sync.py --token "..." --server your.webuntis.com
```

Note: You'll need to update the token periodically as they expire.

## Security Note

- Never commit your session token or password to version control
- Session tokens expire, so they're safer than storing passwords
- Consider using environment variables for credentials

## License

MIT License - Feel free to modify and use as needed
