# So holst du deinen WebUntis Session-Token (JSESSIONID)

Da deine Schule SSO (Single Sign-On) verwendet, ist es am einfachsten, den Session-Token direkt aus deinem Browser zu kopieren.

## Methode 1: Chrome / Edge (Empfohlen)

1. **Login bei WebUntis**
   - Gehe zu https://peleus.webuntis.com
   - Logge dich mit SSO ein

2. **Developer Tools öffnen**
   - Drücke `F12` oder `Strg + Shift + I`
   - Oder: Rechtsklick → "Untersuchen" / "Inspect"

3. **Zum Application Tab**
   - Klicke oben auf den Tab **"Application"**
   - Falls du ihn nicht siehst, klicke auf `>>` und wähle "Application"

4. **Cookies finden**
   - Links in der Sidebar: **Storage** → **Cookies** → `https://peleus.webuntis.com`

5. **JSESSIONID kopieren**
   - Suche in der Liste nach dem Cookie mit dem Namen **`JSESSIONID`**
   - Doppelklick auf den **Value** (Wert) → Kopieren (`Strg + C`)
   - Der Wert sieht ungefähr so aus: `ABC123DEF456GHI789...`

## Methode 2: Firefox

1. **Login bei WebUntis**
   - Gehe zu https://peleus.webuntis.com
   - Logge dich mit SSO ein

2. **Developer Tools öffnen**
   - Drücke `F12` oder `Strg + Shift + I`

3. **Zum Storage Tab**
   - Klicke oben auf den Tab **"Speicher"** / **"Storage"**

4. **Cookies finden**
   - Links in der Sidebar: **Cookies** → `https://peleus.webuntis.com`

5. **JSESSIONID kopieren**
   - Suche nach **`JSESSIONID`**
   - Kopiere den Wert aus der "Wert" / "Value" Spalte

## Methode 3: Direkt aus dem Network Tab

1. **Login bei WebUntis**
   - Gehe zu https://peleus.webuntis.com
   - **NOCH NICHT** einloggen!

2. **Developer Tools öffnen**
   - Drücke `F12`
   - Gehe zum Tab **"Network"** / **"Netzwerk"**

3. **Jetzt einloggen**
   - Logge dich mit SSO ein
   - Beobachte die Requests im Network Tab

4. **jsonrpc.do Request finden**
   - Suche nach einem Request zu `jsonrpc.do`
   - Klicke drauf

5. **Cookie kopieren**
   - Gehe zum Tab **"Headers"** / **"Kopfzeilen"**
   - Scroll zu **"Request Headers"**
   - Finde **`Cookie:`**
   - Kopiere nur den Wert nach `JSESSIONID=` (bis zum nächsten Semikolon `;`)

## Beispiel

Wenn du im Cookie-Tab das siehst:

```
Name:     JSESSIONID
Value:    A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
Domain:   peleus.webuntis.com
Path:     /WebUntis
```

Dann kopierst du nur: `A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6`

## In das Script einfügen

Öffne `webuntis_scraper.py` und füge deinen Token ein:

```python
SCHOOL = "Ferd.von+Steinbeis"
SESSION_TOKEN = "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"  # ← Hier einfügen!
```

## Wichtig!

⚠️ **Session-Tokens laufen ab!** Normalerweise nach:
- 30-60 Minuten Inaktivität
- Beim Logout
- Nach einem Browser-Neustart (manchmal)

Wenn du einen Fehler bekommst wie "session expired", musst du einen neuen Token holen.

## Sicherheit

🔒 **Teile deinen Session-Token NIEMALS!**
- Damit hat jemand Zugriff auf deinen WebUntis Account
- Behandle ihn wie ein Passwort
- Lösche ihn aus dem Code, wenn du ihn teilst

## Script starten

Wenn du den Token eingefügt hast:

```bash
python3 webuntis_scraper.py
```

Das Script sollte jetzt funktionieren ohne Login! 🎉
