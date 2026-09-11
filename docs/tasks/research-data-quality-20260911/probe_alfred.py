"""Two bounded FRED vintage reads using the existing configured key; no database writes."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen
from stockanalysis.operations.env_file import load_env_file_values

values = load_env_file_values('/opt/stockanalysis/runtime/data-operations.env')
key = values.get('STOCKANALYSIS_FRED_API_KEY')
result = {'observed_at': datetime.now(timezone.utc).isoformat(), 'database_writes': False, 'samples': []}
if not key:
    result['status'] = 'existing_key_not_configured'
else:
    for vintage in ('2024-03-08', '2026-09-10'):
        query = {'api_key': key, 'file_type': 'json', 'series_id': 'UNRATE',
                 'observation_start': '2024-01-01', 'observation_end': '2024-02-01',
                 'realtime_start': vintage, 'realtime_end': vintage}
        try:
            with urlopen('https://api.stlouisfed.org/fred/series/observations?' + urlencode(query), timeout=20) as response:
                data = json.load(response)
                result['samples'].append({'vintage': vintage, 'http_status': response.status,
                                          'observations': data.get('observations', [])})
        except Exception as error:
            # Never include request URL, response body, or credentials in errors.
            result['samples'].append({'vintage': vintage, 'error_type': type(error).__name__,
                                      'http_status': getattr(error, 'code', None)})
print(json.dumps(result, ensure_ascii=False))
