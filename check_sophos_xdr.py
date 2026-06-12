#!/usr/bin/env python3
import requests
import sys
from datetime import datetime, timedelta, timezone

CLIENT_ID = "DEINE_CLIENT_ID"
CLIENT_SECRET = "DEIN_CLIENT_SECRET"

AUTH_URL = "https://id.sophos.com/api/v2/oauth2/token"
WHOAMI_URL = "https://api.central.sophos.com/whoami/v1"

# Schwellwerte
WARN_HIGH_ALERTS = 1
CRIT_HIGH_ALERTS = 3
WARN_MEDIUM_ALERTS = 5
CRIT_MEDIUM_ALERTS = 10

# Zeitraum für Alert-Abfrage
LOOKBACK_HOURS = 24


def checkmk_output(state, service, perfdata, text):
    print(f'{state} "{service}" {perfdata} {text}')

def nagios_exit(state, text, perfdata=""):
    status_map = {
        0: "OK",
        1: "WARNING",
        2: "CRITICAL",
        3: "UNKNOWN"
    }

    status = status_map.get(state, "UNKNOWN")

    if perfdata:
        print(f"{status} - {text} | {perfdata}")
    else:
        print(f"{status} - {text}")

    sys.exit(state)

def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "token"
    }

    r = requests.post(AUTH_URL, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def get_tenant_info(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(WHOAMI_URL, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def get_cases(token, tenant_id, api_host):
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    url = f"{api_host}/cases/v1/cases"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
        "Accept": "application/json"
    }

    params = {
        "from": since.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "pageSize": 50,
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if not r.ok:
        raise Exception(
            f"Sophos Cases request failed: HTTP {r.status_code} - {r.text}"
        )

    return r.json().get("items", [])

def get_siem_events(token, tenant_id, api_host):
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    url = f"{api_host}/siem/v1/events"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
        "Accept": "application/json"
    }

    params = {
        "from_date": int(since.timestamp()),
        "limit": 1000
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if not r.ok:
        raise Exception(
            f"Sophos SIEM events request failed: HTTP {r.status_code} - {r.text}"
        )

    return r.json().get("items", [])


def get_alerts(token, tenant_id, api_host):
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    url = f"{api_host}/common/v1/alerts"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
        "Accept": "application/json"
    }

    params = {
        "from": since.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "pageSize": 50
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if not r.ok:
        raise Exception(
            f"Sophos alerts request failed: HTTP {r.status_code} - {r.text} - URL: {r.url}"
        )

    return r.json().get("items", [])


def main():
    try:
        token = get_access_token()
        tenant = get_tenant_info(token)

        tenant_id = tenant.get("id")
        api_hosts = tenant.get("apiHosts", {})
        api_host = api_hosts.get("dataRegion")

        if not tenant_id or not api_host:
            checkmk_output(2, "Sophos XDR API", "-", "Tenant-ID oder API-Host konnte nicht ermittelt werden")
            sys.exit(0)

        alerts = get_alerts(token, tenant_id, api_host)

        high = sum(1 for a in alerts if a.get("severity") == "high")
        medium = sum(1 for a in alerts if a.get("severity") == "medium")
        low = sum(1 for a in alerts if a.get("severity") == "low")
        total = len(alerts)

        state = 0
        if high >= CRIT_HIGH_ALERTS or medium >= CRIT_MEDIUM_ALERTS:
            state = 2
        elif high >= WARN_HIGH_ALERTS or medium >= WARN_MEDIUM_ALERTS:
            state = 1

        perfdata = (
            f"'total'={total} "
            f"'high'={high};{WARN_HIGH_ALERTS};{CRIT_HIGH_ALERTS};0; "
            f"'medium'={medium};{WARN_MEDIUM_ALERTS};{CRIT_MEDIUM_ALERTS};0; "
            f"'low'={low};0;0;0;"
        )

        text = (
            f"Sophos XDR Alerts last {LOOKBACK_HOURS}h: "
            f"total={total}, high={high}, medium={medium}, low={low}"
        )

        events = get_siem_events(token, tenant_id, api_host)

        # High-Severity Events filtern
        high_events = [
            e for e in events
            if e.get("severity") in ("high", "High") 
            or e.get("type") == "Event::Endpoint::Threat::Detected"
        ]

        high_event_count = len(high_events)

        # In State-Berechnung einbeziehen
        if high_event_count >= CRIT_HIGH_ALERTS:
            state = 2
        elif high_event_count >= WARN_HIGH_ALERTS:
            state = 1

        # In perfdata und text ergänzen
        perfdata += f"'high_events'={high_event_count};{WARN_HIGH_ALERTS};{CRIT_HIGH_ALERTS};0;"
        text += f", high_events={high_event_count}"

        cases = get_cases(token, tenant_id, api_host)
        case_count = sum(1 for c in cases if c.get("status", "").lower() in ("new", "investigating"))

        # Cases in State-Berechnung einbeziehen
        WARN_CASES = 1
        CRIT_CASES = 3

        if case_count >= CRIT_CASES:
            state = 2
        elif case_count >= WARN_CASES:
            state = 1

        # In perfdata und text ergänzen
        perfdata += f"'cases'={case_count};{WARN_CASES};{CRIT_CASES};0;"
        text += f", cases={case_count}"

        nagios_exit(state, text, perfdata)

    except requests.exceptions.HTTPError as e:
        nagios_exit(2, f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        nagios_exit(2, f"Connection error: {e}")
    except Exception as e:
        nagios_exit(3, f"Unknown error: {e}")


if __name__ == "__main__":
    main()
