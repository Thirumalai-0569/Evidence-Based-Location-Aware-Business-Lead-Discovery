# Implementation status

Included in this starter ZIP: FastAPI routing, Nominatim geocoding with process-local caching and one-second spacing, Overpass category discovery, approved CSV import connector, basic normalization, cross-source candidate matching, evidence storage, conservative verification states, preliminary score explanation, SQLite search history, Leaflet map, list/detail views, selected CSV export and basic tests.

Not production-complete: second live API source, robust persistent cache/central rate limiting, queue/background jobs, approved verification/rejection policy, website evidence checks, human correction workflow/audit UI, advanced entity resolution, semantic relevance, AI integration, pagination/authentication/RBAC, monitoring, deployment, load testing and full mobile/browser acceptance.

The second connector currently means a user-provided approved CSV dataset, not a second automatic public API. Confirm with the task owner whether that satisfies the source requirement.


## Reliability and Android update
- Overpass client now has sequential fallback endpoints, separate connection/read timeouts, five-minute in-process caching and serialized requests.
- The UI has responsive mobile styles and touch-sized controls for Android Chrome.
- Local Android access instructions are in README.md. Use the PC's Wi-Fi IPv4 address and run Uvicorn on 0.0.0.0.
- Public Overpass services remain best-effort; fallback reduces but cannot eliminate timeouts. Production usage should use an approved hosted or self-hosted provider.


## Progress update - 24 Nov 2026

### Fixed
- **Frontend did not work at all.** `app.js` called `escapeHtml`, `loadLeads`, `loadDetail` and `loadHistory` without defining them, had no search-form handler, and bound to `importButton`/`csvFile`/`importMessage`, which did not exist in `index.html`, so the script crashed on load. All are now implemented; the CSV import panel and the verification status guide were added to the page.
- **`style.css` was truncated** (only the verification guide and map rules remained). Base, form, table, status-badge, detail and mobile styles were restored; existing rules were kept unchanged.
- **CSV import:** headers such as `Name,Latitude,Longitude` passed the column check but imported 0 rows (keys were not normalized); fixed. The upload route re-opened a `NamedTemporaryFile` by name, which fails on Windows; it now parses the uploaded bytes directly.
- **Scoring:** category fit was always 5/25 because OSM stores raw tags (`college`) while users choose labels (`Education`). Results now carry the category filter that produced them (`matched_category`).
- **Distance:** a business found again from a different search centre kept its first distance; it is now refreshed on every search.
- **Tests:** `TestClient` was imported by name into `test_api.py` and pytest tried to collect it (visible in `.pytest_cache`); replaced with a module import. Added 16 regression tests (CSV, scoring, connector, save/merge service). 22 tests pass locally; the 2 API tests need FastAPI installed and were not run in the review environment.
- **Docs:** README/UNDERSTANDING described a "two sources = partially_verified" rule that the code does not implement; they now describe the actual evidence-based policy. Fixed the setup folder name.

### Still open (needs task-owner decision or follow-up)
- No connector supplies verification evidence, so every lead is `unverified` (167 of 167 in the current database). Define the verification policy and workflow.
- `.env` uses a placeholder contact (`sample@gmail.com`) in `APP_USER_AGENT`; replace it with a real contact to comply with Nominatim/Overpass usage policies.
- Domain-based matching merges all branches that share one website domain; review for multi-branch chains.
- Live map tiles and Leaflet load from public CDNs; check in a real browser/Android Chrome run (map could not be exercised offline).
