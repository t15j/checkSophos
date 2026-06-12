# Sophos XDR Check für Nagios / OMD / Checkmk

## Übersicht

Dieses Python-Skript überwacht Sophos Central XDR über die Sophos Central APIs und stellt die Ergebnisse im klassischen Nagios-Plugin-Format bereit.

Der Check eignet sich für:

* Nagios
* OMD
* Checkmk
* Icinga
* Naemon
* andere Nagios-kompatible Monitoring-Systeme

Das Skript authentifiziert sich per OAuth2 an Sophos Central, ermittelt automatisch Tenant-ID und API-Region und wertet anschließend folgende Datenquellen aus:

* Sophos Central Alerts
* Sophos SIEM Events
* Sophos Cases

Die Ausgabe erfolgt Nagios-kompatibel inklusive Exit-Code und Performance-Daten.

---

## Funktionen

* OAuth2-Authentifizierung gegen Sophos Central
* Automatische Ermittlung von Tenant-ID und API-Region
* Abfrage von Sophos Central Alerts
* Abfrage von Sophos SIEM Events
* Abfrage von Sophos Cases
* Bewertung von High- und Medium-Severity Alerts
* Erkennung kritischer SIEM Events
* Bewertung offener oder in Bearbeitung befindlicher Cases
* Nagios-kompatible Ausgabe
* Performance-Daten für Graphing und Trendanalyse

---

## Überwachte Datenquellen

### Sophos Central Alerts

Endpoint:

```text
/common/v1/alerts
```

Ausgewertet werden Alerts im definierten Zeitraum.

Bewertet werden:

* `high`
* `medium`
* `low`
* Gesamtanzahl der Alerts

---

### Sophos SIEM Events

Endpoint:

```text
/siem/v1/events
```

Ausgewertet werden SIEM Events im definierten Zeitraum.

Als relevante High Events gelten aktuell:

```text
severity = high
severity = High
type = Event::Endpoint::Threat::Detected
```

Die Anzahl dieser Events wird als `high_events` in die Bewertung einbezogen.

---

### Sophos Cases

Endpoint:

```text
/cases/v1/cases
```

Ausgewertet werden Cases mit folgendem Status:

```text
new
investigating
```

Diese werden als offene bzw. aktive Cases betrachtet und in die Bewertung einbezogen.

---

## Voraussetzungen

### Betriebssystem

Das Skript kann auf Linux-Systemen eingesetzt werden, auf denen Python 3 verfügbar ist.

Typische Zielsysteme:

* OMD Server
* Checkmk Site
* Nagios Server
* Icinga Server

---

### Python-Version

Empfohlen:

```text
Python 3.9 oder neuer
```

---

### Python-Abhängigkeiten

Benötigt wird das Modul `requests`.

Installation:

```bash
pip3 install requests
```

Alternativ systemweit über Paketmanager, je nach Distribution:

```bash
sudo apt install python3-requests
```

---

## Sophos API Credentials

In Sophos Central muss ein API Credential erstellt werden.

Pfad:

```text
Sophos Central
→ Global Settings
→ API Credentials
→ Add Credential
```

Benötigt werden:

```text
Client ID
Client Secret
```

Diese Werte werden im Skript eingetragen:

```python
CLIENT_ID = "<CLIENT_ID>"
CLIENT_SECRET = "<CLIENT_SECRET>"
```

---

## Konfiguration

### Zeitraum der Abfrage

```python
LOOKBACK_HOURS = 24
```

Der Standardwert prüft die letzten 24 Stunden.

Beispiele:

```python
LOOKBACK_HOURS = 12
```

prüft die letzten 12 Stunden.

```python
LOOKBACK_HOURS = 168
```

prüft die letzten 7 Tage.

---

## Schwellwerte

### Alerts mit High Severity

```python
WARN_HIGH_ALERTS = 1
CRIT_HIGH_ALERTS = 3
```

Bedeutung:

| Anzahl High Alerts | Status   |
| -----------------: | -------- |
|                  0 | OK       |
|               ab 1 | WARNING  |
|               ab 3 | CRITICAL |

---

### Alerts mit Medium Severity

```python
WARN_MEDIUM_ALERTS = 5
CRIT_MEDIUM_ALERTS = 10
```

Bedeutung:

| Anzahl Medium Alerts | Status   |
| -------------------: | -------- |
|                  0-4 | OK       |
|                 ab 5 | WARNING  |
|                ab 10 | CRITICAL |

---

### SIEM High Events

SIEM High Events verwenden aktuell dieselben Schwellwerte wie High Alerts:

```python
WARN_HIGH_ALERTS = 1
CRIT_HIGH_ALERTS = 3
```

Bedeutung:

| Anzahl High Events | Status   |
| -----------------: | -------- |
|                  0 | OK       |
|               ab 1 | WARNING  |
|               ab 3 | CRITICAL |

---

### Cases

Die Schwellwerte für Cases sind im Skript innerhalb der Main-Logik definiert:

```python
WARN_CASES = 1
CRIT_CASES = 3
```

Bedeutung:

| Anzahl aktiver Cases | Status   |
| -------------------: | -------- |
|                    0 | OK       |
|                 ab 1 | WARNING  |
|                 ab 3 | CRITICAL |

Als aktive Cases gelten:

```text
new
investigating
```

---

## Nagios-kompatible Ausgabe

Das Skript verwendet das klassische Nagios-Plugin-Format:

```text
STATUS - Meldung | Performance-Daten
```

Beispiel:

```text
WARNING - Sophos XDR Alerts last 24h: total=2, high=1, medium=0, low=1, high_events=1, cases=0 | 'total'=2 'high'=1;1;3;0; 'medium'=0;5;10;0; 'low'=1;0;0;0;'high_events'=1;1;3;0;'cases'=0;1;3;0;
```

---

## Exit Codes

| Exit Code | Status   | Bedeutung                                   |
| --------: | -------- | ------------------------------------------- |
|         0 | OK       | Keine relevanten Auffälligkeiten            |
|         1 | WARNING  | Warnschwelle erreicht                       |
|         2 | CRITICAL | Kritische Schwelle erreicht oder API-Fehler |
|         3 | UNKNOWN  | Unerwarteter Fehler im Skript               |

---

## Performance-Daten

Das Skript liefert folgende Performance-Daten:

| Metrik        | Beschreibung                       |
| ------------- | ---------------------------------- |
| `total`       | Gesamtanzahl der Sophos Alerts     |
| `high`        | Anzahl High-Severity Alerts        |
| `medium`      | Anzahl Medium-Severity Alerts      |
| `low`         | Anzahl Low-Severity Alerts         |
| `high_events` | Anzahl relevanter High SIEM Events |
| `cases`       | Anzahl aktiver Cases               |

---

## Installation unter OMD / Checkmk

### Skript ablegen

Beispiel für eine OMD-Site:

```bash
mkdir -p ~/local/lib/nagios/plugins
cp check_sophos_xdr.py ~/local/lib/nagios/plugins/
chmod +x ~/local/lib/nagios/plugins/check_sophos_xdr.py
```

---

### Skript testen

```bash
~/local/lib/nagios/plugins/check_sophos_xdr.py
```

Beispielausgabe:

```text
OK - Sophos XDR Alerts last 24h: total=0, high=0, medium=0, low=0, high_events=0, cases=0 | 'total'=0 'high'=0;1;3;0; 'medium'=0;5;10;0; 'low'=0;0;0;0;'high_events'=0;1;3;0;'cases'=0;1;3;0;
```

---

## Beispiel für Nagios-/OMD-Command

Beispielhafte Command-Definition:

```text
define command {
    command_name    check_sophos_xdr
    command_line    $USER1$/check_sophos_xdr.py
}
```

---

## Beispiel für Service-Definition

```text
define service {
    use                     generic-service
    host_name               sophos-central
    service_description     Sophos XDR Security Status
    check_command           check_sophos_xdr
}
```

---

## Sicherheitshinweise

Es wird empfohlen, Client-ID und Client-Secret nicht dauerhaft im Skript zu speichern.

Besser ist die Nutzung von Umgebungsvariablen oder einer geschützten Konfigurationsdatei.

Beispiel mit Umgebungsvariablen:

```bash
export SOPHOS_CLIENT_ID="..."
export SOPHOS_CLIENT_SECRET="..."
```

Die Zugangsdaten sollten nur für den Monitoring-Benutzer lesbar sein.

Beispiel:

```bash
chmod 600 /pfad/zur/config
chown omd:omd /pfad/zur/config
```

---

## Fehleranalyse

### HTTP 400 Bad Request

Mögliche Ursachen:

* Ungültiger API-Parameter
* Falsches Datumsformat
* Nicht unterstützter Filter
* API-Endpunkt erwartet andere Parameter

Empfohlene Prüfung:

```python
print(r.text)
print(r.url)
```

---

### HTTP 401 Unauthorized

Mögliche Ursachen:

* Client ID falsch
* Client Secret falsch
* Secret wurde erneuert oder gelöscht
* OAuth-Token konnte nicht korrekt erzeugt werden

---

### HTTP 403 Forbidden

Mögliche Ursachen:

* API Credential hat keine ausreichenden Rechte
* Zugriff auf den Tenant ist nicht erlaubt
* Endpoint ist für den Tenant nicht freigeschaltet

---

### HTTP 404 Not Found

Mögliche Ursachen:

* API-Endpunkt ist in der verwendeten Sophos-Region nicht verfügbar
* Endpoint-Pfad ist falsch
* Feature ist im Tenant nicht lizenziert oder nicht aktiv

---

### Werte sind immer 0

Mögliche Ursachen:

* Im Zeitraum gibt es keine passenden Alerts, Events oder Cases
* `LOOKBACK_HOURS` ist zu klein gewählt
* Severity-Werte werden anders geschrieben
* Cases haben andere Statuswerte
* SIEM Events liefern andere Event-Typen

Zur Analyse kann der Zeitraum testweise erhöht werden:

```python
LOOKBACK_HOURS = 168
```

---

## Debugging

Für eine kontrollierte Analyse können temporär Rohdaten ausgegeben werden.

Beispiel für Alerts:

```python
print(alerts[:5])
```

Beispiel für SIEM Events:

```python
print(events[:5])
```

Beispiel für Cases:

```python
print(cases[:5])
```

Debug-Ausgaben sollten im produktiven Monitoring wieder entfernt werden, da sie die Nagios-kompatible Ausgabe stören können.

---

## Hinweise zum Betrieb

Empfohlener Prüfintervall:

```text
5 bis 15 Minuten
```

Empfohlener Zeitraum:

```text
24 Stunden
```

Der Zeitraum sollte nicht zu klein gewählt werden, da Security Events sonst zwischen zwei Prüfintervallen übersehen werden können.

Für produktive Umgebungen empfiehlt sich zusätzlich:

* dedizierter API-Client für Monitoring
* dokumentierte Schwellwerte
* Eskalationsregeln für CRITICAL
* keine Secrets in Git-Repositories
* regelmäßige Prüfung der API-Antworten nach Sophos-Änderungen

---

## Aktueller Bewertungsansatz

Der finale Status ergibt sich aus der höchsten Bewertung der folgenden Bereiche:

1. High- und Medium-Severity Alerts
2. High SIEM Events
3. Aktive Cases

Wenn einer dieser Bereiche CRITICAL erreicht, ist der Gesamtstatus CRITICAL.

Wenn keiner CRITICAL ist, aber mindestens ein Bereich WARNING erreicht, ist der Gesamtstatus WARNING.

Nur wenn alle Bereiche unterhalb der Warnschwelle liegen, ist der Gesamtstatus OK.

---

## Beispielstatus

### OK

```text
OK - Sophos XDR Alerts last 24h: total=0, high=0, medium=0, low=0, high_events=0, cases=0 | 'total'=0 'high'=0;1;3;0; 'medium'=0;5;10;0; 'low'=0;0;0;0;'high_events'=0;1;3;0;'cases'=0;1;3;0;
```

### WARNING

```text
WARNING - Sophos XDR Alerts last 24h: total=3, high=1, medium=1, low=1, high_events=1, cases=1 | 'total'=3 'high'=1;1;3;0; 'medium'=1;5;10;0; 'low'=1;0;0;0;'high_events'=1;1;3;0;'cases'=1;1;3;0;
```

### CRITICAL

```text
CRITICAL - Sophos XDR Alerts last 24h: total=8, high=3, medium=2, low=3, high_events=4, cases=3 | 'total'=8 'high'=3;1;3;0; 'medium'=2;5;10;0; 'low'=3;0;0;0;'high_events'=4;1;3;0;'cases'=3;1;3;0;
```

---

## Lizenz / Nutzung

Das Skript kann frei an die eigene Monitoring- und Security-Umgebung angepasst werden.

Es verwendet die Sophos Central APIs und benötigt gültige Sophos Central API Credentials.
