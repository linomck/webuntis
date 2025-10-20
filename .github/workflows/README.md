# GitHub Actions Setup für WebUntis Calendar Sync

## Setup-Anleitung

### 1. Repository erstellen

```bash
# In deinem Projektverzeichnis
git init
git add .
git commit -m "Initial commit: WebUntis Calendar Sync"

# Erstelle ein neues GitHub Repository (z.B. "webuntis-calendar")
# Dann pushe deinen Code:
git remote add origin https://github.com/DEIN_USERNAME/webuntis-calendar.git
git branch -M main
git push -u origin main
```

### 2. GitHub Pages aktivieren

1. Gehe zu deinem Repository auf GitHub
2. **Settings** → **Pages**
3. **Source**: Deploy from a branch
4. **Branch**: `main` / `root`
5. **Save**

Nach ein paar Minuten ist dein Calendar verfügbar unter:
```
https://DEIN_USERNAME.github.io/webuntis-calendar/webuntis_calendar.ics
```

### 3. Secrets einrichten

Du musst zwei Secrets in deinem GitHub Repository einrichten:

#### Im Browser: Hol dir Token & Cookies

1. Öffne WebUntis und logge dich ein
2. **F12** → **Network** tab
3. Refresh die Seite
4. Klick auf einen API Request
5. Unter **Request Headers** kopiere:
   - `Authorization: Bearer ...` → Das ist dein **TOKEN**
   - `cookie: ...` → Das sind deine **COOKIES**

#### In GitHub: Speichere als Secrets

1. Gehe zu deinem Repository auf GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Secret 1: WEBUNTIS_TOKEN**
- Name: `WEBUNTIS_TOKEN`
- Value: `eyJraWQiOiI3MzIxNjk2MzYi...` (dein Bearer Token ohne "Bearer ")

**Secret 2: WEBUNTIS_COOKIES**
- Name: `WEBUNTIS_COOKIES`
- Value: `Tenant-Id=4197100; JSESSIONID=...; ...` (der komplette Cookie-String)

### 4. Workflow testen

#### Manuell triggern:
1. Gehe zu **Actions** tab in GitHub
2. Wähle **Sync WebUntis Calendar**
3. Click **Run workflow**

#### Automatisch:
- Läuft täglich um 6:00 Uhr (UTC) = 7:00/8:00 Uhr (DE, je nach Sommer/Winterzeit)
- Läuft auch bei jedem Push (zum Testen)

### 5. iPhone Calendar abonnieren

#### iPhone/iPad:
1. **Einstellungen** → **Kalender** → **Accounts** → **Account hinzufügen**
2. Wähle **Andere** → **Kalender-Abo hinzufügen**
3. Gib die URL ein:
   ```
   https://DEIN_USERNAME.github.io/webuntis-calendar/webuntis_calendar.ics
   ```
4. Tippe **Weiter** und **Sichern**

Der Kalender wird jetzt automatisch synchronisiert!

### 6. Token & Cookies aktualisieren

WebUntis Tokens und Cookies laufen nach einiger Zeit ab. Wenn der Workflow fehlschlägt:

1. Hol dir neue Token & Cookies aus dem Browser (siehe Schritt 3)
2. Gehe zu **Settings** → **Secrets and variables** → **Actions**
3. Klick auf den Secret (z.B. `WEBUNTIS_TOKEN`)
4. **Update secret** → paste den neuen Wert
5. **Update secret**

Wiederhole das für beide Secrets.

## Workflow-Status prüfen

- Gehe zu **Actions** tab
- Sieh dir die letzten Runs an
- Bei Fehlern: Prüfe ob Token/Cookies abgelaufen sind

## Zeitplan anpassen

Im `.github/workflows/sync-calendar.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Täglich um 6:00 UTC
  # '0 */6 * * *'      # Alle 6 Stunden
  # '0 8 * * 1-5'      # Mo-Fr um 8:00 UTC
```

## Troubleshooting

### Workflow schlägt fehl mit 401 Unauthorized
→ Token/Cookies sind abgelaufen, aktualisiere die Secrets

### Calendar wird nicht aktualisiert
→ Prüfe ob GitHub Pages aktiviert ist
→ Cache in iPhone löschen: Settings → Calendar → Accounts → Kalender löschen und neu abonnieren

### iPhone zeigt alte Einträge
→ iPhone cached Kalender, kann 24h dauern bis Updates erscheinen
→ Oder: Kalender-Abo löschen und neu hinzufügen
