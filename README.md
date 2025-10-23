# WebUntis Calendar Sync

Automatically sync your WebUntis timetable to an iCal (.ics) file that can be subscribed to in your calendar app.

## Features

- **Automated Login**: Uses Selenium to automatically log in to WebUntis via FSV-Zugang SSO
- **Session Management**: Extracts cookies and bearer tokens directly (no file-based session storage)
- **Calendar Generation**: Converts WebUntis timetable to iCal (.ics) format
- **GitHub Pages Deployment**: Automatically publishes the calendar to GitHub Pages
- **Scheduled Updates**: Runs every 6 hours to keep your calendar up-to-date

## Setup

### 1. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:
   - `FSV_USERNAME`: Your WebUntis/FSV username
   - `FSV_PASSWORD`: Your WebUntis/FSV password

### 2. Enable GitHub Pages

1. Go to repository Settings → Pages
2. Under "Source", select "Deploy from a branch"
3. Select the `gh-pages` branch
4. Click "Save"

### 3. Run the Workflow

The workflow runs automatically:
- Every 6 hours (at 00:00, 06:00, 12:00, 18:00 UTC)
- On every push to main/master branch
- Manually via the Actions tab

To trigger manually:
1. Go to the "Actions" tab
2. Select "Sync WebUntis Calendar"
3. Click "Run workflow"

### 4. Subscribe to Your Calendar

After the first successful run, your calendar will be available at:

```
https://<your-username>.github.io/<repository-name>/webuntis_calendar.ics
```

#### In iPhone Calendar:
1. Open Settings → Calendar → Accounts
2. Add Account → Other → Add Subscribed Calendar
3. Enter the URL above
4. The calendar will auto-update when changes are published

#### In Google Calendar:
1. Open Google Calendar
2. Click the "+" next to "Other calendars"
3. Select "From URL"
4. Enter the URL above
5. Click "Add calendar"

## Local Usage

### Prerequisites

- Python 3.11+
- Chrome browser
- ChromeDriver

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with your credentials:

```env
FSV_USERNAME=your_username
FSV_PASSWORD=your_password
```

### Run the Sync

```bash
# Generate calendar file
python webuntis_to_ical.py

# With custom options
python webuntis_to_ical.py --weeks 8 --output my_calendar.ics --headless
```

### Command Line Options

- `--server`: WebUntis server (default: peleus.webuntis.com)
- `--weeks`: Number of weeks to fetch (default: 4)
- `--output`: Output filename (default: webuntis_calendar.ics)
- `--headless`: Run browser in headless mode

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── sync-calendar.yml    # GitHub Actions workflow
├── webuntis_auto_login.py       # Auto-login handler
├── webuntis_to_ical.py          # Calendar sync script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## How It Works

1. **Auto-Login**: `webuntis_auto_login.py` uses Selenium to:
   - Navigate to WebUntis login page
   - Click the FSV-Zugang SSO button
   - Fill in credentials and submit
   - Extract session cookies and bearer token using Chrome DevTools Protocol

2. **Calendar Sync**: `webuntis_to_ical.py`:
   - Receives session data from auto-login
   - Fetches timetable entries via WebUntis REST API
   - Converts to iCal format with all event details
   - Saves to `.ics` file

3. **GitHub Actions**: The workflow:
   - Runs on a schedule or manually
   - Sets up Python and Chrome environment
   - Executes the sync script
   - Deploys the `.ics` file to GitHub Pages

## Troubleshooting

### Workflow fails with authentication error

- Check that your GitHub secrets are correctly set
- Verify your FSV credentials are correct
- Check the Actions logs for detailed error messages

### Calendar not updating

- Check the workflow run status in the Actions tab
- Verify GitHub Pages is enabled for the `gh-pages` branch
- Force a manual workflow run to test

### Browser errors in workflow

- The workflow uses headless Chrome
- Check the workflow logs for Selenium errors
- Ensure ChromeDriver setup is successful

## Security

- Credentials are stored as GitHub encrypted secrets
- Sessions are ephemeral (not stored in files)
- Only the `.ics` file is published to GitHub Pages
- No sensitive data is committed to the repository

## License

This project is for personal use. Please respect WebUntis terms of service.

## Contributing

Feel free to open issues or submit pull requests for improvements!
