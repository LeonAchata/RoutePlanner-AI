'use strict';

// The UI is normally served by the API itself. When the file is opened
// directly (file://) fall back to a local server, and allow ?api=... to point
// at any other backend.
const API_BASE = (() => {
    const override = new URLSearchParams(window.location.search).get('api');
    if (override && override.trim()) return override.trim().replace(/\/$/, '');
    if (window.location.protocol.startsWith('http')) return '';
    return 'http://localhost:8000';
})();

const REQUEST_TIMEOUT_MS = 90_000;
const MAX_QUERY_LENGTH = 1000;

const EXAMPLES = [
    {
        label: 'Errands in Lima',
        text: "I'm in Lima Centro and need to go to Miraflores, San Isidro and Barranco.",
    },
    {
        label: 'Delivery run',
        text: 'Leaving from Av. Arequipa 1200, Lince. Deliveries at Av. Larco 789 Miraflores, Jr. Sucre 456 Magdalena del Mar and Calle Los Olivos 123 Barranco.',
    },
    {
        label: 'Round trip',
        text: 'Desde el Callao voy a San Miguel, Pueblo Libre y Jesus Maria, y luego vuelvo a casa.',
    },
    {
        label: 'Sales visits',
        text: 'Starting at Jockey Plaza, visit clients in La Molina, San Borja and Surquillo.',
    },
];

const $ = (id) => document.getElementById(id);

const ui = {
    form: $('routeForm'),
    input: $('routeInput'),
    charCount: $('charCount'),
    submitBtn: $('submitBtn'),
    examples: $('examplesList'),
    errorBox: $('errorBox'),
    errorMessage: $('errorMessage'),
    errorClose: $('errorClose'),
    results: $('results'),
    tripType: $('tripType'),
    totalDistance: $('totalDistance'),
    totalTime: $('totalTime'),
    stopCount: $('stopCount'),
    itinerary: $('itinerary'),
    gmapsLink: $('gmapsLink'),
    gmapsNote: $('gmapsNote'),
    copyLink: $('copyLink'),
    loading: $('loading'),
    mapEmpty: $('mapEmpty'),
};

let inFlight = null;

/* ---------- Map ---------- */

const map = (() => {
    if (typeof L === 'undefined') return null;

    const instance = L.map('map', { zoomControl: true }).setView([-12.08, -77.04], 12);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        className: 'base-tiles',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(instance);

    return { instance, layer: L.layerGroup().addTo(instance), markers: [] };
})();

function drawRoute(data) {
    if (!map) return;
    map.layer.clearLayers();
    map.markers = [];

    const routeColor = getComputedStyle(document.documentElement).getPropertyValue('--route').trim() || '#1f6feb';
    const path = data.route_polyline
        ? decodePolyline(data.route_polyline)
        : data.stops.map((s) => [s.lat, s.lng]);

    L.polyline(path, {
        color: routeColor,
        weight: 5,
        opacity: 0.85,
        // Straight dashed lines make it clear we only know the stop order,
        // not the actual streets.
        dashArray: data.route_polyline ? null : '6 8',
    }).addTo(map.layer);

    // On a round trip the last stop is the origin again; one marker is enough.
    const stops = data.return_to_origin ? data.stops.slice(0, -1) : data.stops;
    stops.forEach((stop, i) => {
        const marker = L.marker([stop.lat, stop.lng], {
            icon: L.divIcon({
                className: '',
                html: `<div class="map-pin${i === 0 ? ' is-origin' : ''}">${i === 0 ? 'A' : i}</div>`,
                iconSize: [28, 28],
                iconAnchor: [14, 14],
            }),
            title: stop.name,
            zIndexOffset: i === 0 ? 1000 : 0,
        });
        marker.bindPopup(popupContent(stop));
        marker.addTo(map.layer);
        map.markers.push(marker);
    });

    map.instance.fitBounds(L.latLngBounds(path), { padding: [48, 48], maxZoom: 16 });
    ui.mapEmpty.classList.add('hidden');
}

function popupContent(stop) {
    const root = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = stop.name;
    root.appendChild(name);
    if (stop.address && stop.address !== stop.name) {
        const addr = document.createElement('div');
        addr.textContent = stop.address;
        root.appendChild(addr);
    }
    return root;
}

// Google's encoded polyline format:
// https://developers.google.com/maps/documentation/utilities/polylinealgorithm
function decodePolyline(encoded) {
    const points = [];
    let index = 0;
    let lat = 0;
    let lng = 0;

    const next = () => {
        let result = 0;
        let shift = 0;
        let byte;
        do {
            byte = encoded.charCodeAt(index++) - 63;
            result |= (byte & 0x1f) << shift;
            shift += 5;
        } while (byte >= 0x20);
        return result & 1 ? ~(result >> 1) : result >> 1;
    };

    while (index < encoded.length) {
        lat += next();
        lng += next();
        points.push([lat / 1e5, lng / 1e5]);
    }
    return points;
}

/* ---------- Form ---------- */

function renderExamples() {
    for (const example of EXAMPLES) {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'chip';
        chip.textContent = example.label;
        chip.title = example.text;
        chip.addEventListener('click', () => {
            ui.input.value = example.text;
            updateCharCount();
            ui.input.focus();
        });
        ui.examples.appendChild(chip);
    }
}

function updateCharCount() {
    ui.charCount.textContent = `${ui.input.value.length} / ${MAX_QUERY_LENGTH}`;
}

function selectedMode() {
    return ui.form.querySelector('input[name="travelMode"]:checked').value;
}

async function handleSubmit(event) {
    event.preventDefault();
    const query = ui.input.value.trim();

    if (query.length < 3) {
        showError('Describe where you start and which places you want to visit.');
        ui.input.focus();
        return;
    }

    if (inFlight) inFlight.abort();
    const controller = new AbortController();
    inFlight = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), REQUEST_TIMEOUT_MS);

    hideError();
    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, travel_mode: selectedMode() }),
            signal: controller.signal,
        });

        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(errorText(response.status, data));

        renderResults(data);
    } catch (error) {
        if (controller.signal.aborted && controller.signal.reason !== 'timeout') return;
        if (controller.signal.reason === 'timeout') {
            showError('The server took too long to answer. Try again with fewer stops.');
        } else if (error instanceof TypeError) {
            showError('Could not reach the server. Make sure the API is running.');
        } else {
            showError(error.message);
        }
    } finally {
        clearTimeout(timeout);
        if (inFlight === controller) {
            inFlight = null;
            setLoading(false);
        }
    }
}

function errorText(status, data) {
    const detail = data && data.detail;
    if (typeof detail === 'string') return detail;
    // FastAPI validation errors come back as a list.
    if (Array.isArray(detail) && detail.length) return detail[0].msg || 'Invalid request.';
    if (status >= 500) return 'The server ran into a problem. Try again in a moment.';
    return 'The request could not be processed.';
}

function setLoading(isLoading) {
    ui.submitBtn.disabled = isLoading;
    ui.submitBtn.querySelector('.btn-label').textContent = isLoading ? 'Planning...' : 'Plan route';
    ui.loading.classList.toggle('hidden', !isLoading);
    ui.form.setAttribute('aria-busy', String(isLoading));
}

function showError(message) {
    ui.errorMessage.textContent = message;
    ui.errorBox.classList.remove('hidden');
}

function hideError() {
    ui.errorBox.classList.add('hidden');
}

/* ---------- Results ---------- */

function renderResults(data) {
    const destinations = data.stops.length - (data.return_to_origin ? 2 : 1);

    ui.tripType.textContent = data.return_to_origin ? 'Round trip' : 'One way';
    ui.totalDistance.textContent = formatDistance(data.total_distance_km);
    ui.totalTime.textContent = formatMinutes(data.estimated_time_min);
    ui.stopCount.textContent = String(destinations);

    ui.itinerary.replaceChildren(
        ...data.stops.map((stop, i) => {
            const isOrigin = i === 0 || (data.return_to_origin && i === data.stops.length - 1);
            return stopItem(stop, i, isOrigin, data.steps[i]);
        }),
    );

    if (data.google_maps_url) {
        ui.gmapsLink.href = data.google_maps_url;
        ui.gmapsLink.removeAttribute('aria-disabled');
        ui.copyLink.disabled = false;
        ui.gmapsNote.classList.add('hidden');
    } else {
        ui.gmapsLink.removeAttribute('href');
        ui.gmapsLink.setAttribute('aria-disabled', 'true');
        ui.copyLink.disabled = true;
        ui.gmapsNote.classList.remove('hidden');
    }

    ui.results.classList.remove('hidden');
    drawRoute(data);

    if (window.matchMedia('(max-width: 860px)').matches) {
        ui.results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function stopItem(stop, index, isOrigin, legAfter) {
    const li = document.createElement('li');
    li.className = 'stop';

    const marker = document.createElement('button');
    marker.type = 'button';
    marker.className = `stop-marker${isOrigin ? ' is-origin' : ''}`;
    marker.textContent = isOrigin ? 'A' : String(index);
    marker.setAttribute('aria-label', `Show ${stop.name} on the map`);
    marker.addEventListener('click', () => focusStop(stop, isOrigin ? 0 : index));

    const body = document.createElement('div');
    const name = document.createElement('div');
    name.className = 'stop-name';
    name.textContent = stop.name;
    body.appendChild(name);

    if (stop.address && stop.address.toLowerCase() !== stop.name.toLowerCase()) {
        const address = document.createElement('div');
        address.className = 'stop-address';
        address.textContent = stop.address;
        body.appendChild(address);
    }

    li.append(marker, body);

    if (legAfter) {
        const leg = document.createElement('div');
        leg.className = 'leg';
        leg.textContent = `${legAfter.distance}  ·  ${legAfter.time}`;
        li.appendChild(leg);
    }
    return li;
}

function focusStop(stop, markerIndex) {
    if (!map) return;
    map.instance.flyTo([stop.lat, stop.lng], Math.max(map.instance.getZoom(), 15), { duration: 0.6 });
    const marker = map.markers[markerIndex];
    if (marker) marker.openPopup();
}

async function copyGoogleMapsLink() {
    const url = ui.gmapsLink.href;
    if (!url) return;
    const label = ui.copyLink.textContent;
    try {
        await navigator.clipboard.writeText(url);
        ui.copyLink.textContent = 'Copied';
    } catch {
        ui.copyLink.textContent = 'Copy failed';
    }
    setTimeout(() => {
        ui.copyLink.textContent = label;
    }, 1600);
}

function formatMinutes(minutes) {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins === 0 ? `${hours} h` : `${hours} h ${mins} min`;
}

function formatDistance(km) {
    return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

/* ---------- Wiring ---------- */

ui.form.addEventListener('submit', handleSubmit);
ui.input.addEventListener('input', updateCharCount);
ui.input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        ui.form.requestSubmit();
    }
});
ui.errorClose.addEventListener('click', hideError);
ui.copyLink.addEventListener('click', copyGoogleMapsLink);

document.querySelector('.topnav a[href="docs"]').href = `${API_BASE}/docs`;

renderExamples();
updateCharCount();
