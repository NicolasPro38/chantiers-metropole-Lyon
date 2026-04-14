/* === CARTE DES CHANTIERS – MÉTROPOLE DE LYON === */

// Initialisation de la carte
const map = L.map('map', {
    center: [45.75, 4.85],
    zoom: 12,
    zoomControl: true
});

// Fond de carte OpenMapTiles (comme mobilites.grandlyon.com)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap © Data Grand Lyon',
    maxZoom: 19
}).addTo(map);

// Couche GeoJSON des chantiers
let chantiersLayer = null;
let statsCharts = {};

// Couleurs par état
function getCouleurEtat(etat) {
    switch(etat) {
        case 'Ouvert':  return { fill: '#E87722', stroke: '#c45e0a' };
        case 'Validé':  return { fill: '#C8102E', stroke: '#a00d24' };
        case 'Terminé': return { fill: '#888888', stroke: '#555555' };
        default:        return { fill: '#C8102E', stroke: '#a00d24' };
    }
}

function styleChantier(feature) {
    const c = getCouleurEtat(feature.properties.etat);
    return {
        fillColor: c.fill,
        color: c.stroke,
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.45
    };
}

function onEachFeature(feature, layer) {
    const p = feature.properties;
    layer.on({
        mouseover: function(e) {
            e.target.setStyle({ fillOpacity: 0.75, weight: 2.5 });
        },
        mouseout: function(e) {
            if (chantiersLayer) chantiersLayer.resetStyle(e.target);
        },
        click: function(e) {
            afficherDetail(p);
            map.fitBounds(e.target.getBounds(), { maxZoom: 16, padding: [40, 40] });
        }
    });
}

function afficherDetail(p) {
    const panel = document.getElementById('detail-panel');
    const content = document.getElementById('detail-content');

    const badgeClass = p.etat === 'Ouvert' ? 'badge-ouvert' :
                       p.etat === 'Validé' ? 'badge-valide' : 'badge-termine';

    const formatDate = (d) => d ? new Date(d).toLocaleDateString('fr-FR') : '–';

    content.innerHTML = `
        <h3>🚧 ${p.nature_chantier || 'Chantier'}</h3>
        <div class="detail-row">
            <span class="detail-key">État</span>
            <span class="detail-val"><span class="badge ${badgeClass}">${p.etat}</span></span>
        </div>
        <div class="detail-row">
            <span class="detail-key">N° dossier</span>
            <span class="detail-val">${p.numero || '–'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Intervenant</span>
            <span class="detail-val">${p.intervenant || '–'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Nature travaux</span>
            <span class="detail-val">${p.nature_travaux || '–'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Adresse</span>
            <span class="detail-val">${p.adresse || '–'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Commune</span>
            <span class="detail-val">${p.commune || '–'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Début</span>
            <span class="detail-val">${formatDate(p.date_debut)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-key">Fin prévue</span>
            <span class="detail-val">${formatDate(p.date_fin)}</span>
        </div>
        ${p.mesures_police ? `
        <div class="detail-row">
            <span class="detail-key">Mesures police</span>
            <span class="detail-val">${p.mesures_police}</span>
        </div>` : ''}
        ${p.contact_url ? `
        <div class="detail-row">
            <span class="detail-key">Contact</span>
            <span class="detail-val"><a href="${p.contact_url}" target="_blank">Plus d'infos</a></span>
        </div>` : ''}
    `;
    panel.classList.remove('hidden');
}

document.getElementById('detail-close').addEventListener('click', () => {
    document.getElementById('detail-panel').classList.add('hidden');
});

// Chargement des chantiers
function chargerChantiers(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = '/api/chantiers' + (qs ? '?' + qs : '');

    if (chantiersLayer) map.removeLayer(chantiersLayer);

    fetch(url)
        .then(r => r.json())
        .then(data => {
            document.getElementById('counter-total').textContent = data.total.toLocaleString('fr-FR');

            chantiersLayer = L.geoJSON(data, {
                style: styleChantier,
                onEachFeature: onEachFeature
            }).addTo(map);

            if (data.features.length > 0) {
                map.fitBounds(chantiersLayer.getBounds(), { padding: [20, 20] });
            }
        });
}

// Chargement des communes dans le select
function chargerCommunes() {
    fetch('/api/communes')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('filter-commune');
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.commune;
                opt.textContent = `${c.commune} (${c.nb})`;
                sel.appendChild(opt);
            });
        });
}

// Chargement des stats et graphiques
function chargerStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            // Stat cards
            const ouverts = data.par_etat.find(e => e.label === 'Ouvert');
            const valides = data.par_etat.find(e => e.label === 'Validé');
            document.getElementById('stat-ouverts').textContent = ouverts ? ouverts.nb : 0;
            document.getElementById('stat-valides').textContent = valides ? valides.nb : 0;

            // Remplir le select nature
            const selNature = document.getElementById('filter-nature');
            data.par_nature.forEach(n => {
                if (!n.label) return;
                const opt = document.createElement('option');
                opt.value = n.label;
                opt.textContent = `${n.label} (${n.nb})`;
                selNature.appendChild(opt);
            });

            // Graphique communes
            const ctxC = document.getElementById('chart-communes').getContext('2d');
            if (statsCharts.communes) statsCharts.communes.destroy();
            statsCharts.communes = new Chart(ctxC, {
                type: 'bar',
                data: {
                    labels: data.par_commune.map(d => d.label),
                    datasets: [{
                        data: data.par_commune.map(d => d.nb),
                        backgroundColor: '#C8102E',
                        borderRadius: 3
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { font: { size: 10 } } },
                        y: { ticks: { font: { size: 10 } } }
                    }
                }
            });

            // Graphique nature
            const ctxN = document.getElementById('chart-nature').getContext('2d');
            if (statsCharts.nature) statsCharts.nature.destroy();
            const colors = data.par_nature.map((_, i) =>
                i === 0 ? '#C8102E' : i === 1 ? '#E87722' : `hsl(${i * 25}, 60%, 50%)`
            );
            statsCharts.nature = new Chart(ctxN, {
                type: 'doughnut',
                data: {
                    labels: data.par_nature.map(d => d.label || 'Non défini'),
                    datasets: [{ data: data.par_nature.map(d => d.nb), backgroundColor: colors }]
                },
                options: {
                    plugins: {
                        legend: { position: 'bottom', labels: { font: { size: 10 }, boxWidth: 12 } }
                    }
                }
            });
        });
}

// Filtres
document.getElementById('btn-filter').addEventListener('click', () => {
    const params = {};
    const commune = document.getElementById('filter-commune').value;
    const etat = document.getElementById('filter-etat').value;
    const nature = document.getElementById('filter-nature').value;
    if (commune) params.commune = commune;
    if (etat) params.etat = etat;
    if (nature) params.nature_chantier = nature;
    chargerChantiers(params);
});

document.getElementById('btn-reset').addEventListener('click', () => {
    document.getElementById('filter-commune').value = '';
    document.getElementById('filter-etat').value = '';
    document.getElementById('filter-nature').value = '';
    chargerChantiers();
});

// Init
chargerCommunes();
chargerStats();
chargerChantiers();

// === LÉGENDE ===
const legend = L.control({ position: 'bottomleft' });
legend.onAdd = function() {
    const div = L.DomUtil.create('div', '');
    div.style.cssText = 'background:white; padding:10px 14px; border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.2); font-size:12px; line-height:1.8; min-width:130px;';
    div.innerHTML = `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:#C8102E; margin-bottom:6px; letter-spacing:0.3px;">État du chantier</div>
        <div style="display:flex; align-items:center; gap:8px;"><span style="width:14px;height:14px;background:#E87722;border-radius:3px;display:inline-block;opacity:0.8;"></span> Ouvert</div>
        <div style="display:flex; align-items:center; gap:8px;"><span style="width:14px;height:14px;background:#C8102E;border-radius:3px;display:inline-block;opacity:0.8;"></span> Validé</div>
        <div style="display:flex; align-items:center; gap:8px;"><span style="width:14px;height:14px;background:#888888;border-radius:3px;display:inline-block;opacity:0.8;"></span> Terminé</div>
    `;
    return div;
};
legend.addTo(map);

// Fix style légende
document.addEventListener('DOMContentLoaded', function() {
    const legendEl = document.querySelector('.legend');
    if (legendEl) {
        legendEl.style.cssText = 'background:white; padding:10px 14px; border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.2); font-size:13px; line-height:1.8;';
    }
});

// === RECHERCHE ADRESSE (Photon Grand Lyon) ===
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const searchResults = document.getElementById('search-results');
let searchMarker = null;

function rechercherAdresse(query) {
    if (!query || query.length < 3) return;
    const url = `https://download.data.grandlyon.com/geocoding/photon-bal/api?q=${encodeURIComponent(query)}&limit=6`;
    fetch(url)
        .then(r => r.json())
        .then(data => {
            searchResults.innerHTML = '';
            searchResults.classList.remove('hidden');
            if (!data.features || data.features.length === 0) {
                searchResults.innerHTML = '<li style="color:#999">Aucun résultat</li>';
                return;
            }
            data.features.forEach(f => {
                const p = f.properties;
                const parts = [p.name];
                if (p.street && p.street !== p.name) parts.push(p.street);
                if (p.city && p.city !== p.name) parts.push(p.city);
                const label = parts.join(', ');
                const li = document.createElement('li');
                li.textContent = label;
                li.addEventListener('click', () => {
                    const [lng, lat] = f.geometry.coordinates;
                    map.setView([lat, lng], 16);
                    if (searchMarker) map.removeLayer(searchMarker);
                    searchMarker = L.circleMarker([lat, lng], {
                        radius: 8,
                        fillColor: '#C8102E',
                        color: '#fff',
                        weight: 2,
                        fillOpacity: 0.9
                    }).addTo(map).bindPopup(label).openPopup();
                    searchResults.classList.add('hidden');
                    searchInput.value = label;
                });
                searchResults.appendChild(li);
            });
        });
}

searchBtn.addEventListener('click', () => rechercherAdresse(searchInput.value));
searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') rechercherAdresse(searchInput.value);
});
searchInput.addEventListener('input', () => {
    if (searchInput.value.length >= 3) rechercherAdresse(searchInput.value);
    else searchResults.classList.add('hidden');
});
document.addEventListener('click', e => {
    if (!e.target.closest('.search-bar')) searchResults.classList.add('hidden');
});