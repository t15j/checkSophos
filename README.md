# Sophos XDR Alert Check für Nagios / OMD / Checkmk

## Übersicht

Dieses Python-Skript überwacht Sophos Central XDR Alerts über die Sophos Central API und stellt die Ergebnisse im klassischen Nagios-Plugin-Format bereit.

Der Check eignet sich für:

* Nagios
* OMD
* Checkmk (aktive Checks)
* Icinga
* Naemon
* andere Nagios-kompatible Monitoring-Systeme

Das Skript authentifiziert sich mittels OAuth2 an der Sophos Central API, ermittelt automatisch die zuständige API-Region und wertet die vorhandenen Alerts aus.

---

## Funktionen

* OAuth2-Authentifizierung gegen Sophos Central
* Automatische Ermittlung von Tenant-ID und API-Region
* Auswertung von Sophos XDR Alerts
* Konfigurierbare Schwellwerte
* Nagios-konforme Exit-Codes
* Performance-Daten für Graphen und Trends
* Unterstützung für OMD, Nagios und Checkmk

---

## Voraussetzungen

### Python

Getestet mit:

* Python 3.9+
* Python 3.10+
* Python 3.11+

### Python-Modul

```bash
pip install requests
```

---

## API-Berechtigungen

In Sophos Central muss ein API-Client erstellt werden.

Pfad:

```text
Sophos Central
→ Global Settings
→ API Credentials
→ Add Credential
```

Benötigt werden:

* Client ID
* Client Secret

Diese Werte werden im Skript hinterlegt oder über Umgebungsvariablen geladen.

---

## Konfiguration

### Zugangsdaten

```python
CLIENT_ID = "xxxxxxxxxxxxxxxx"
CLIENT_SECRET = "xxxxxxxxxxxxxxxx"
```

### Zeitraum

```python
LOOKBACK_HOURS = 24
```

Beispiel:

```python
LOOKBACK_HOURS = 168
```

wertet die letzten sieben Tage aus.

---

## Schwellwerte

### High Severity

```python
WARN_HIGH_ALERTS = 1
CRIT_HIGH_ALERTS = 3
```

### Medium Severity

```python
WARN_MEDIUM_ALERTS = 5
CRIT_MEDIUM_ALERTS = 10
```

Diese Werte können individuell an die Umgebung angepasst werden.

---

## Nagios Exit Codes

| Exit Code | Status   |
| --------- | -------- |
| 0         | OK       |
| 1         | WARNING  |
| 2         | CRITICAL |
| 3         | UNKNOWN  |

---

## Beispielausgaben

### OK

```text
OK - Sophos XDR Alerts last 24h: total=0, high=0, medium=0, low=0 | 'total'=0 'high'=0;1;3;0; 'medium'=0;5;10;0; 'low'=0;0;0;0;
```

### WARNING

```text
WARNING - Sophos XDR Alerts last 24h: total=4, high=1, medium=2, low=1 | 'total'=4 'high'=1;1;3;0; 'medium'=2;5;10;0; 'low'=1;0;0;0;
```

### CRITICAL

```text
CRITICAL - Sophos XDR Alerts last 24h: total=12, high=5, medium=4, low=3 | 'total'=12 'high'=5;1;3;0; 'medium'=4;5;10;0; 'low'=3;0;0;0;
```

---

## Installation unter OMD / Checkmk

### Skript kopieren

```bash
mkdir -p ~/local/lib/nagios/plugins
cp check_sophos_xdr.py ~/local/lib/nagios/plugins/
chmod +x ~/local/lib/nagios/plugins/check_sophos_xdr.py
```

### Test

```bash
~/local/lib/nagios/plugins/check_sophos_xdr.py
```

---

## Beispiel für Active Check

```text
check_sophos_xdr
```

Command:

```bash
$USER1$/check_sophos_xdr.py
```

---

## Fehleranalyse

### HTTP 400 Bad Request

Mögliche Ursachen:

* Falsche Client-ID
* Falsches Client-Secret
* Fehlerhafte API-Berechtigungen
* Ungültige Parameter für den Alert-Endpunkt

Empfohlen:

```python
print(response.text)
```

zur Analyse der API-Antwort.

---

### HTTP 401 Unauthorized

Mögliche Ursachen:

* Abgelaufenes Secret
* Falsche Zugangsdaten
* API-Credential gelöscht

---

### HTTP 403 Forbidden

Mögliche Ursachen:

* Fehlende Berechtigungen
* Tenant-Zugriff nicht erlaubt

---

### Keine Alerts trotz vorhandener Vorfälle

Prüfen:

* Zeitraum (`LOOKBACK_HOURS`)
* Severity-Filter
* Alert-Status in Sophos Central
* API-Rückgabe mittels Debug-Ausgabe

---

## Sicherheitshinweise

Es wird empfohlen, Client-ID und Client-Secret nicht direkt im Skript zu speichern.

Stattdessen sollten Umgebungsvariablen oder eine geschützte Konfigurationsdatei verwendet werden:

```bash
export SOPHOS_CLIENT_ID="..."
export SOPHOS_CLIENT_SECRET="..."
```

oder

```bash
/etc/check_sophos_xdr.conf
```

mit Berechtigungen:

```bash
chmod 600
```

---

## Lizenz

Dieses Skript verwendet ausschließlich die öffentliche Sophos Central API und kann frei an die eigene Monitoring-Umgebung angepasst werden.
