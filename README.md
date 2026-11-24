# Evidence-Based Location-Aware Business Lead Discovery

A starter implementation based on the supplied project brief and the uploaded project archive. It includes location geocoding, OpenStreetMap discovery, an approved user-provided CSV source connector, normalization, cross-source matching, evidence records, preliminary relevance scoring, search history, Leaflet map/list views, lead details and selected CSV export.

## Important scope and accuracy notes

- OpenStreetMap/Overpass is the live discovery connector. The second connector imports a CSV dataset that the user is authorized to use; it is not a second live public API. Obtain task-owner approval for the second source before production.
- Every record starts as `unverified`. Records found in several sources are merged and keep one evidence row per source, but source count alone never changes the status. `partially_verified`, `verified` and `rejected` are assigned only when a record carries explicit verification evidence (name/address/website matches against reliable evidence, independent-source confirmation, or an identity conflict) - see `determine_verification_status` in `backend/services/business_service.py`. No current connector produces that evidence, so all records currently stay `unverified` until a verification workflow and policy are approved.
- Product/service score is a transparent keyword heuristic. It is not proof that a business needs or will buy the service. Scores are preliminary prioritization aids, not probabilities.
- The app does not crawl business websites or harvest phone/email data. Add website checks only after reviewing each source/site's terms, robots rules, privacy obligations and rate limits.
- Nominatim's public service has a usage policy. Configure a real contact in `APP_USER_AGENT`, respect its rate limit, cache requests, and review current policy before deployment. Overpass is a shared public service; throttle/cache and expect temporary unavailability.
- Leaflet map tiles use OpenStreetMap tile services; follow the tile usage policy and attribution requirements.

## Windows setup (Command Prompt)

```bat
cd Business_Lead_Discovery_Future
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and replace the example contact email with a real project contact. Then run:

```bat
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`. API docs: `http://127.0.0.1:8000/docs`.

## Use the website on an Android phone (same Wi-Fi)

1. Start the backend on your Windows computer with:
   ```bat
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. On Windows, run `ipconfig` and find the computer's **IPv4 Address** under the active Wi-Fi adapter (for example `192.168.1.8`).
3. Connect the Android phone to the same Wi-Fi network.
4. Open Chrome on Android and visit `http://192.168.1.8:8000` using your computer's actual IPv4 address.
5. If Windows Firewall asks, allow Python/Uvicorn on **Private networks**. If needed, create an inbound TCP rule for port `8000` on the Private profile only.

Do not type `localhost` or `127.0.0.1` on the phone; those addresses point to the phone itself. Do not expose the development server directly to the public internet. For access from outside your Wi-Fi, deploy behind HTTPS using a production hosting setup.

The frontend uses responsive CSS and touch-friendly controls for Android Chrome. It is a mobile-friendly website; it does not require an Android APK or app installation.

## Overpass timeout handling

The connector now:
- Uses a 10-second connection timeout and 60-second response timeout, separately from the Overpass query's 45-second server-side timeout.
- Tries the configured endpoints sequentially: the primary `overpass-api.de` endpoint, then the separately operated `overpass.private.coffee` fallback.
- Caches successful identical searches in memory for five minutes and serializes requests from this application to avoid parallel bursts.
- Shows a user-friendly temporary-unavailable message if both endpoints fail.

Public Overpass servers are shared community services and do not guarantee availability. A timeout can still happen. Try again later or reduce the radius (for example, from 15 km to 5 km). Do not repeatedly submit the same failed search. Configure endpoints and timeout values in `.env`; check each provider's current usage terms before production use.

## Search example

- Location: `Vellore`
- Product/service: `Website Development`
- Category: `Education`
- Keywords: `engineering college`
- Radius: `15`

The current Overpass connector uses category filters. Product/service and keywords contribute to a preliminary score; they do not currently perform semantic search over website descriptions.

## Import a second approved source

CSV columns required: `name,latitude,longitude`. Optional: `category,location,website,source_url`. Header names are matched case-insensitively and must be UTF-8 encoded; rows with a missing name or invalid coordinates are skipped. In the UI, upload only datasets you have permission to reuse. The connector records the source as `Approved CSV Dataset` and preserves the supplied source URL.

## Tests

```bat
pytest -q
```

Tests include basic API routing, normalization, score behavior, CSV parsing, Overpass fallback/caching and the save/merge/score service layer (using an in-memory database, never `data/business_leads.db`). Live Nominatim/Overpass integration, source licensing, verification correctness, large-scale performance and browser/mobile acceptance still require separate tests.

## API endpoints

- `GET /api/health`
- `POST /api/search/businesses`
- `GET /api/leads`
- `GET /api/leads/{lead_id}`
- `GET /api/history`
- `POST /api/import/approved-csv`
- `GET /api/export/csv?ids=1,2,3`

## Project structure

See `UNDERSTANDING.md` for the architecture, data flow, risks and milestones. Do not commit `.env`, virtual environments, caches or live database records.
