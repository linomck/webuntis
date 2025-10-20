# How to Find Your WebUntis School Name

## Method 1: Check the Login URL ⭐ Recommended

1. Open your browser
2. Go to https://webuntis.com
3. Search for and select your school
4. Look at the URL in your browser's address bar
5. Find `?school=XXXXX` in the URL

**Example:**
```
https://peleus.webuntis.com/WebUntis/?school=myschoolname
                                            ^^^^^^^^^^^^^
                                            This is your school name
```

## Method 2: Check Browser Developer Tools

1. Open https://peleus.webuntis.com in your browser
2. Press F12 to open Developer Tools
3. Go to the "Network" tab
4. Log into WebUntis
5. Look for requests to `jsonrpc.do`
6. Click on one of these requests
7. Look at the URL - it will show `?school=XXXXX`

## Method 3: Check During Login

When you're at the login page, the URL already contains the school parameter.

**Your URL format:**
```
https://peleus.webuntis.com/WebUntis/?school=XXXXX#/basic/login
```

## Common Examples

- `?school=gymnasium-berlin`
- `?school=realschule123`
- `?school=htl-example`

## Special Characters

Note: Umlauts and spaces are converted:
- ö → oe
- ä → ae
- ü → ue
- spaces → - or removed

## Still Can't Find It?

Check with your school's IT department or administration - they can tell you the exact school name used in WebUntis.
