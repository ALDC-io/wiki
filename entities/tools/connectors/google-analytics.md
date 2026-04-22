---
tags: [entity, tool, connector, google-analytics, oauth]
aliases: [Google Analytics Connector, GA4 Connector, Universal Analytics Connector]
sources: [Confluence CONN/645300259]
created: 2026-04-18
updated: 2026-04-18
---

# Google Analytics Connector

Eclipse connector for Google Analytics (GA4 and Universal Analytics). Uses service account credentials for GA4 and OAuth2 for Universal Analytics.

> **Prefect migration note:** This connector must be rebuilt as a Prefect flow. The connection string schema, options dictionary structure, required Python libraries (google-api-python-client, oauth2client, google-analytics-data), and API endpoints documented here are the reference spec for the Prefect implementation.

## Connection Configuration

### Connection String Schema

#### GA4
```python
connection = {
    'GA4_PROPERTY_ID': 'XXXXXXXXXXXXXXX',    # Property settings → PROPERTY ID
    'call_interval': 0.5                       # Seconds between API calls
}
```

#### Universal Analytics
```python
connection = {
    'KEY_FILE_LOCATION_UA': r'C:/path/to/client_secrets.json',  # Service account JSON
    'VIEW_ID_UA': 'XXXXXXXXXXXXXXX',                             # View settings → VIEW ID
    'call_interval': 0.5
}
```

### Options Schema

```python
# GA4
options = {
    'category': 'GA4',
    'dimensions': ['eventName', 'pageTitle'],    # Up to 9; no 'ga:' prefix
    'metrics': ['eventCount'],                   # Up to 10; no 'ga:' prefix
    'date_ranges': {'start_date': '2021-09-05', 'end_date': 'today'}
}

# Universal Analytics
options = {
    'category': 'universal_analytics',
    'dimensions': ['ga:country', 'ga:browser'],  # Up to 9; 'ga:' prefix required
    'metrics': ['ga:sessions', 'ga:pageviews'],  # Up to 10; 'ga:' prefix required
    'date_ranges': {'startDate': '7daysAgo', 'endDate': 'today'}
}
```

## ALDC Support Account

- **Email**: support@aldc.io
- **Password**: `{{GA_SUPPORT_ACCOUNT_PASSWORD}}` — see `vault/infra-credentials.md` § Google Analytics

## Service Account Setup

1. Create service account credentials in Google Cloud Console
2. Download JSON credentials file
3. Provide path as `KEY_FILE_LOCATION_UA` in connection string (UA only; GA4 uses property ID directly)

## Required Python Libraries

```
google-api-python-client
oauth2client
google-analytics-data
pandas
```

### Key Classes

| Library | Class | Purpose |
|---|---|---|
| google-analytics-data | BetaAnalyticsDataClient | GA4 API client |
| google-analytics-data | DateRange, Dimension, Metric, RunReportRequest | GA4 request components |
| oauth2client | ServiceAccountCredentials | UA authentication |
| googleapiclient.discovery | build | UA API client builder |

## Output Format

Dimension columns (object dtype) precede metric columns (int64 dtype). Automatic type conversion is applied after retrieval.

## API References

- GA4 Dimensions & Metrics: https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
- UA Dimensions & Metrics: https://ga-dev-tools.web.app/dimensions-metrics-explorer/
- UA batchGet: https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet

## See Also

- [[eclipse]] — connector platform
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
- [[fusion92]] — primary client using Google Analytics connector
