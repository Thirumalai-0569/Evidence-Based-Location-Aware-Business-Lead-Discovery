const $ = id => document.getElementById(id);
let leads = [];
let map = null;
let markers = null;

async function readApiResponse(response) {
    const text = await response.text();

    let data;

    try {
        data = text ? JSON.parse(text) : {};
    } catch (error) {
        console.error("Server returned non-JSON response:", text);

        throw new Error(
            `Server error (${response.status}). Check backend terminal.`
        );
    }

    if (!response.ok) {
        // FastAPI returns validation errors as a list in `detail`.
        const detail = Array.isArray(data.detail)
            ? data.detail.map(d => d.msg).join('; ')
            : data.detail;

        throw new Error(
            detail || data.message || `Request failed (${response.status})`
        );
    }

    return data;
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
}

// Only allow http(s) links so stored data can never inject javascript: URLs.
function safeUrl(url) {
    if (!url) return '';
    try {
        const u = new URL(/^https?:\/\//i.test(url) ? url : 'https://' + url);
        return (u.protocol === 'http:' || u.protocol === 'https:') ? u.href : '';
    } catch (error) {
        return '';
    }
}

function statusClass(status) {
    return String(status || 'unverified').replace(/_/g, '-');
}

function statusLabel(status) {
    return String(status || 'unverified').replace(/_/g, ' ');
}

function initMap() {
    if (!window.L) return;
    map = L.map('map').setView([12.9165, 79.1325], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    markers = L.layerGroup().addTo(map);
    setTimeout(() => { map.invalidateSize(); }, 300);
}

function showMessage(text, error = false) {
    $('message').textContent = text;
    $('message').style.color = error ? '#b42318' : '#16803c';
}

function renderRows(items) {
    leads = items;
    $('resultCount').textContent = `(${items.length})`;
    $('resultsBody').innerHTML = '';
    if (markers) markers.clearLayers();

    items.forEach(b => {
        const tr = document.createElement('tr');
        const evidence = (b.evidence || []).length;
        tr.innerHTML =
            `<td><input type="checkbox" class="lead-check" value="${escapeHtml(b.id)}" aria-label="Select ${escapeHtml(b.name)}"></td>` +
            `<td><button type="button" class="link-button" data-id="${escapeHtml(b.id)}">${escapeHtml(b.name)}</button></td>` +
            `<td>${escapeHtml(b.category || '')}</td>` +
            `<td>${b.distance_km == null ? '—' : escapeHtml(b.distance_km) + ' km'}</td>` +
            `<td>${Number(b.relevance_score || 0).toFixed(1)}</td>` +
            `<td><span class="status ${statusClass(b.verification_status)}">${escapeHtml(statusLabel(b.verification_status))}</span></td>` +
            `<td>${evidence} source(s)</td>`;
        $('resultsBody').appendChild(tr);

        if (markers && b.latitude != null && b.longitude != null) {
            L.marker([b.latitude, b.longitude]).bindPopup(escapeHtml(b.name)).addTo(markers);
        }
    });

    document.querySelectorAll('.link-button').forEach(x =>
        x.addEventListener('click', () => loadDetail(x.dataset.id)));

    if (items.length && map) {
        const pts = items.filter(x => x.latitude != null && x.longitude != null);
        if (pts.length) {
            map.fitBounds(pts.map(x => [x.latitude, x.longitude]), { padding: [20, 20], maxZoom: 14 });
        }
    }
}

async function loadLeads() {
    const data = await readApiResponse(await fetch('/api/leads'));
    renderRows(data.results || []);
}

async function loadDetail(id) {
    const box = $('leadDetails');
    box.classList.remove('muted');
    box.textContent = 'Loading business details…';

    try {
        const b = await readApiResponse(await fetch('/api/leads/' + encodeURIComponent(id)));
        const site = safeUrl(b.website);
        const evidence = (b.evidence || []).map(e => {
            const link = safeUrl(e.source_url);
            const when = e.retrieved_at ? new Date(e.retrieved_at).toLocaleString() : '';
            return `<li class="evidence-item"><strong>${escapeHtml(e.source)}</strong>` +
                (e.source_record_id ? ` <span class="muted-text">(${escapeHtml(e.source_record_id)})</span>` : '') +
                (e.snippet ? `<br>${escapeHtml(e.snippet)}` : '') +
                (link ? `<br><a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">View source record</a>` : '') +
                (when ? `<br><span class="muted-text">Retrieved: ${escapeHtml(when)}</span>` : '') +
                `</li>`;
        }).join('');

        box.innerHTML =
            `<h3>${escapeHtml(b.name)} <span class="status ${statusClass(b.verification_status)}">${escapeHtml(statusLabel(b.verification_status))}</span></h3>` +
            `<dl class="detail-grid">` +
            `<dt>Category</dt><dd>${escapeHtml(b.category || '—')}</dd>` +
            `<dt>Location</dt><dd>${escapeHtml(b.location || '—')}</dd>` +
            `<dt>Website</dt><dd>${site ? `<a href="${escapeHtml(site)}" target="_blank" rel="noopener noreferrer">${escapeHtml(b.website)}</a>` : '—'}</dd>` +
            `<dt>Distance</dt><dd>${b.distance_km == null ? '—' : escapeHtml(b.distance_km) + ' km'}</dd>` +
            `<dt>Relevance score</dt><dd>${Number(b.relevance_score || 0).toFixed(1)} / 100</dd>` +
            `</dl>` +
            `<p><strong>Score explanation:</strong> ${escapeHtml(b.relevance_explanation || 'Not available')}</p>` +
            `<h4>Evidence (${(b.evidence || []).length})</h4>` +
            (evidence ? `<ul class="evidence-list">${evidence}</ul>` : '<p class="muted-text">No evidence recorded.</p>');
    } catch (error) {
        box.textContent = error.message;
    }
}

async function loadHistory() {
    const rows = await readApiResponse(await fetch('/api/history'));
    const list = $('historyList');
    if (!rows.length) {
        list.innerHTML = '<li>No searches yet</li>';
        return;
    }
    list.innerHTML = rows.map(h => {
        const when = h.created_at ? new Date(h.created_at).toLocaleString() : '';
        return `<li><strong>${escapeHtml(h.location)}</strong> — ${escapeHtml(h.product_service || '')}` +
            (h.category ? ` · ${escapeHtml(h.category)}` : '') +
            ` · ${escapeHtml(h.radius_km)} km · ${escapeHtml(h.results_count)} result(s)` +
            (when ? ` <span class="muted-text">(${escapeHtml(when)})</span>` : '') + `</li>`;
    }).join('');
}

$('searchForm').addEventListener('submit', async event => {
    event.preventDefault();
    const button = $('searchButton');
    const payload = {
        location: $('location').value.trim(),
        product_service: $('service').value.trim(),
        category: $('category').value || null,
        keywords: $('keywords').value.split(',').map(x => x.trim()).filter(Boolean),
        radius_km: Number($('radius').value) || 5
    };

    button.disabled = true;
    showMessage('Searching…');

    try {
        const response = await fetch('/api/search/businesses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await readApiResponse(response);
        renderRows(data.results || []);
        showMessage(`Found ${data.total} business near ${data.search_location}.`);
        loadHistory().catch(() => {});
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        button.disabled = false;
    }
});

$('refreshButton').addEventListener('click', () => loadLeads().catch(e => showMessage(e.message, true)));

$('exportButton').addEventListener('click', () => {
    const ids = [...document.querySelectorAll('.lead-check:checked')].map(x => x.value);
    if (!ids.length) {
        showMessage('Select at least one lead before exporting.', true);
        return;
    }
    window.location.href = '/api/export/csv?ids=' + encodeURIComponent(ids.join(','));
});

$('importButton').addEventListener('click', async () => {
    const file = $('csvFile').files[0];
    if (!file) {
        $('importMessage').textContent = 'Choose a CSV file first.';
        return;
    }
    const fd = new FormData();
    fd.append('file', file);
    try {
        const d = await readApiResponse(await fetch('/api/import/approved-csv', { method: 'POST', body: fd }));
        $('importMessage').textContent = d.message + ` (${d.imported} record(s))`;
        await loadLeads();
    } catch (error) {
        $('importMessage').textContent = error.message;
    }
});

initMap();
loadLeads().catch(e => showMessage(e.message, true));
loadHistory().catch(() => {});
