# Android access and Overpass timeout troubleshooting

## Overpass timeout

The application uses sequential endpoint fallback, separate connect/read timeouts, successful-result caching and a single-request lock. The public endpoints are best-effort, not an uptime guarantee. A fallback endpoint is not a guarantee either.

If both endpoints time out:
1. Wait one or two minutes before trying again.
2. Reduce the radius to 5 km and choose a specific category.
3. Check that the PC has internet access and that a firewall/proxy is not blocking HTTPS.
4. Check the configured provider status and terms.
5. For regular or commercial production traffic, arrange a hosted Overpass provider or self-host an instance rather than relying on free shared infrastructure.

Do not rotate through many public endpoints or send parallel retries. Respect HTTP 429/406 responses and stop repeated requests when a provider rejects them.

## Android Chrome on the same Wi-Fi

Run Uvicorn with `--host 0.0.0.0 --port 8000`, find the Windows PC's Wi-Fi IPv4 address with `ipconfig`, and open `http://PC_IPV4:8000` on the Android phone connected to the same Wi-Fi. Allow inbound TCP 8000 on the Windows Private network profile if prompted. `localhost` on Android is the phone, not the PC.

For internet access outside the local network, deploy behind HTTPS and a production ASGI server/reverse proxy. Do not publish the development server directly.

## Map

Leaflet map tiles are requested from OpenStreetMap. Keep the visible attribution and comply with the tile usage policy. Public map tiles are best-effort; if tiles fail, the business list and API can still work.
