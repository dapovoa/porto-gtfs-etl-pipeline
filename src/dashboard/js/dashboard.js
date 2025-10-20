class STCPDashboard {
    constructor() {
        this.map = null;
        this.charts = {};
        this.apiBase = '/api';
        this.refreshInterval = 300000;
        this.accentColor = '#2563eb';
        this.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        this.markerClusterGroup = null;
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    async init() {
        this.initTheme();
        this.setupChartDefaults();
        this.initMap();
        await this.loadData();
        this.startAutoRefresh();
        this.handleResize();
        this.setupThemeToggle();
    }

    initTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateAccentColor();
    }

    updateAccentColor() {
        this.accentColor = this.theme === 'dark' ? '#3b82f6' : '#2563eb';
    }

    setupThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        const icon = toggle.querySelector('i');

        icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

        toggle.addEventListener('click', () => {
            this.theme = this.theme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', this.theme);
            document.documentElement.setAttribute('data-theme', this.theme);
            icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            this.updateAccentColor();
            this.updateChartsTheme();
        });
    }

    updateChartsTheme() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.data && chart.data.datasets) {
                chart.data.datasets.forEach(dataset => {
                    if (Array.isArray(dataset.backgroundColor)) {

                        dataset.backgroundColor = this.getChartColors();
                    } else {
                        dataset.backgroundColor = this.accentColor;
                        dataset.borderColor = this.accentColor;
                    }
                });
                chart.update();
            }
        });
    }

    getChartColors() {
        return [
            '#2563eb', 
            '#059669', 
            '#0891b2', 
            '#d97706', 
            '#dc2626', 
            '#64748b'  
        ];
    }

    setupChartDefaults() {
        Chart.defaults.color = '#64748b';
        Chart.defaults.borderColor = '#e2e8f0';
        Chart.defaults.font.family = this.fontFamily;
        Chart.defaults.font.size = this.getResponsiveFontSize();
    }

    getResponsiveFontSize() {
        const vw = window.innerWidth;
        if (vw >= 3840) return 12;
        if (vw >= 2560) return 11;
        if (vw >= 1920) return 10;
        return 9;
    }

    initMap() {
        setTimeout(() => {
            if (document.getElementById('map')) {
                this.map = L.map('map', {
                    zoomControl: true,
                    attributionControl: false
                }).setView([41.1579, -8.6291], 13);

                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                    attribution: '',
                    subdomains: 'abcd',
                    maxZoom: 20
                }).addTo(this.map);

                L.control.zoom({
                    position: 'topright'
                }).addTo(this.map);

                setTimeout(() => {
                    this.map.invalidateSize();
                }, 500);

                setTimeout(() => {
                    this.map.invalidateSize();
                }, 1000);
            }
        }, 300);
    }

    handleResize() {
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (this.map) {
                    this.map.invalidateSize();
                }
                this.updateChartsSize();
            }, 250);
        });
    }

    updateChartsSize() {
        Chart.defaults.font.size = this.getResponsiveFontSize();
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.options) {
                try {
                    chart.update();
                } catch (e) {
                    console.warn('Error updating chart:', e);
                }
            }
        });
    }

    async loadData() {
        try {
            this.updateStatus('loading');
            const endpoints = [
                'kpi', 'paragens', 'linhas', 'top-stops',
                'hubs-transferencia', 'quilometragem-linhas', 'frequencia-servico'
            ];
            const requests = endpoints.map(ep => fetch(`${this.apiBase}/${ep}`).then(res => {
                if (!res.ok) throw new Error(`Failed to fetch ${ep}`);
                return res.json();
            }));

            const [kpi, paragens, linhas, topStops, hubs, distance, frequency] = await Promise.all(requests);

            this.updateKPIs(kpi);
            this.updateMap(paragens);
            this.updateRoutes(linhas);
            this.updateTopStops(topStops);
            this.updateHubs(hubs);
            this.updateZoneChart(paragens);
            this.updateDistanceChart(distance);
            this.updateFrequencyChart(frequency);

            document.getElementById('map-stops-count').textContent = paragens.length.toLocaleString();
            document.getElementById('routes-count').textContent = linhas.length.toLocaleString();

            if (this.map) {
                setTimeout(() => {
                    this.map.invalidateSize();
                }, 300);
            }

            this.updateStatus('success');
        } catch (error) {
            console.error('Error loading data:', error);
            this.updateStatus('error');
        }
    }

    updateKPIs(data) {
        const totalParagens = document.getElementById('total-paragens');
        const totalLinhas = document.getElementById('total-linhas');
        const totalHorarios = document.getElementById('total-horarios');
        const cobertura = document.getElementById('cobertura');

        totalParagens.textContent = data.total_paragens?.toLocaleString() || '--';
        totalLinhas.textContent = data.total_linhas?.toLocaleString() || '--';

        const schedules = data.total_horarios || 0;
        if (schedules >= 1000) {
            totalHorarios.textContent = Math.floor(schedules / 1000) + 'K';
        } else {
            totalHorarios.textContent = schedules.toLocaleString();
        }

        cobertura.textContent = data.cobertura || 'Porto';

        [totalParagens, totalLinhas, totalHorarios, cobertura].forEach(el => {
            el.classList.remove('skeleton');
        });
    }

    updateMap(paragens) {
        if (this.markerClusterGroup) {
            this.map.removeLayer(this.markerClusterGroup);
        }

        this.markerClusterGroup = L.markerClusterGroup({
            chunkedLoading: true,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            maxClusterRadius: 50
        });

        const radius = window.innerWidth >= 2560 ? 8 : 6;

        const zoneColors = {
            'Centro': '#2563eb',
            'Norte': '#059669',
            'Sul': '#d97706',
            'Este': '#8b5cf6',
            'Oeste': '#dc2626',
            'default': '#64748b'
        };

        paragens.forEach(paragem => {
            if (paragem.stop_lat && paragem.stop_lon) {
                const zone = paragem.area_geografica || 'default';
                const color = zoneColors[zone] || zoneColors['default'];

                const marker = L.circleMarker([paragem.stop_lat, paragem.stop_lon], {
                    radius: radius,
                    fillColor: color,
                    color: '#ffffff',
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup(`
                    <div style="font-family: ${this.fontFamily};">
                        <h4 style="margin: 0 0 8px 0; color: ${color}; font-family: ${this.fontFamily}; font-weight: 600; font-size: 0.875rem;">${paragem.stop_name}</h4>
                        <p style="margin: 0; font-size: 0.75rem; color: #475569;">
                            <strong>ID:</strong> ${paragem.stop_id}<br>
                            <strong>ZONE:</strong> ${paragem.area_geografica || 'N/A'}
                        </p>
                    </div>
                `);

                this.markerClusterGroup.addLayer(marker);
            }
        });

        this.map.addLayer(this.markerClusterGroup);
    }

    updateRoutes(linhas) {
        const container = document.getElementById('routes-list');
        container.innerHTML = '';

        const colors = ['#2563eb', '#059669', '#0891b2', '#d97706', '#dc2626'];

        linhas.forEach((linha, index) => {
            const item = document.createElement('div');
            item.className = 'list-item';
            const color = colors[index % colors.length];

            item.innerHTML = `
                <div class="item-row">
                    <div class="item-badge" style="background-color: ${color};">${linha.route_short_name}</div>
                    <div class="item-content">
                        <div class="item-title">${linha.route_long_name || linha.route_short_name}</div>
                        <div class="item-meta-row">
                            <div class="item-meta">
                                <i class="fas fa-map-marker-alt"></i>
                                <span>${linha.total_stops || 0} stops</span>
                            </div>
                            <div class="item-meta">
                                <i class="fas fa-route"></i>
                                <span>${(linha.distance || 0).toFixed(1)} km</span>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${Math.min(100, (index + 1) * 30)}%"></div>
                        </div>
                    </div>
                </div>`;
            container.appendChild(item);
        });
    }

    updateTopStops(stops) {
        const container = document.getElementById('top-stops');
        container.innerHTML = '';

        const maxSchedules = Math.max(...stops.map(s => s.total_horarios || 0));
        const colors = ['#2563eb', '#059669', '#0891b2'];

        stops.forEach((stop, index) => {
            const item = document.createElement('div');
            item.className = 'list-item';
            const schedules = stop.total_horarios || 0;
            const percentage = maxSchedules > 0 ? (schedules / maxSchedules) * 100 : 0;

            item.innerHTML = `
                <div class="item-row">
                    <div class="item-rank">${index + 1}</div>
                    <div class="item-content">
                        <div class="item-title">${stop.stop_name}</div>
                        <div class="item-meta-row">
                            <div class="item-meta">
                                <i class="fas fa-calendar-alt"></i>
                                <span>${schedules.toLocaleString()} schedules</span>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                </div>`;
            container.appendChild(item);
        });
    }

    updateHubs(hubs) {
        const container = document.getElementById('hubs-list');
        container.innerHTML = '';

        const maxRoutes = Math.max(...hubs.map(h => h.total_linhas || 0));
        const colors = ['#2563eb', '#059669', '#0891b2'];

        hubs.forEach((hub, index) => {
            const item = document.createElement('div');
            item.className = 'list-item';
            const routes = hub.total_linhas || 0;
            const percentage = maxRoutes > 0 ? (routes / maxRoutes) * 100 : 0;

            item.innerHTML = `
                <div class="item-row">
                    <div class="item-rank">${index + 1}</div>
                    <div class="item-content">
                        <div class="item-title">${hub.stop_name}</div>
                        <div class="item-meta-row">
                            <div class="item-meta">
                                <i class="fas fa-route"></i>
                                <span>${routes} routes</span>
                            </div>
                            <div class="item-meta">
                                <i class="fas fa-bus"></i>
                                <span>${hub.total_viagens || 0} trips</span>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                </div>`;
            container.appendChild(item);
        });
    }

    createOrUpdateChart(chartId, type, data, options) {
        const ctx = document.getElementById(chartId);
        if (!ctx) return;

        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
        }

        const fontSize = this.getResponsiveFontSize();

        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: type === 'doughnut',
                    position: 'bottom',
                    labels: {
                        padding: 8,
                        usePointStyle: true,
                        font: { size: fontSize }
                    }
                }
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };

        this.charts[chartId] = new Chart(ctx, { type, data, options: mergedOptions });
    }

    updateZoneChart(paragens) {
        const zones = paragens.reduce((acc, paragem) => {
            const zone = paragem.area_geografica || 'Other';
            acc[zone] = (acc[zone] || 0) + 1;
            return acc;
        }, {});

        this.createOrUpdateChart('zone-chart', 'doughnut', {
            labels: Object.keys(zones),
            datasets: [{
                data: Object.values(zones),
                backgroundColor: this.getChartColors(),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        }, {});
    }

    updateDistanceChart(data) {
        const maxItems = 8;
        const topItems = data.slice(0, maxItems);

        this.createOrUpdateChart('distance-chart', 'bar', {
            labels: topItems.map(item => item.route_short_name),
            datasets: [{
                label: 'Distance (km)',
                data: topItems.map(item => item.km_total),
                backgroundColor: this.accentColor,
                borderRadius: 4,
                barPercentage: 0.7
            }]
        }, {
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: (value) => value + ' km'
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        });
    }

    updateFrequencyChart(data) {
        const hourlyData = data.reduce((acc, item) => {
            acc[item.hora] = (acc[item.hora] || 0) + item.total_viagens;
            return acc;
        }, {});

        const hours = Object.keys(hourlyData).sort((a, b) => parseInt(a) - parseInt(b));
        const frequencies = hours.map(hour => hourlyData[hour]);

        this.createOrUpdateChart('frequency-chart', 'line', {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Trips per Hour',
                data: frequencies,
                borderColor: this.accentColor,
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3
            }]
        }, {
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' }
                },
                x: {
                    grid: { color: '#f1f5f9' }
                }
            }
        });
    }

    updateStatus(status) {
        const lastUpdate = document.getElementById('last-update');
        const updateTime = document.getElementById('update-time');
        const updateAgo = document.getElementById('update-ago');

        switch (status) {
            case 'loading':
                lastUpdate.textContent = '--';
                if (updateTime) {
                    updateTime.querySelector('span').textContent = '--';
                }
                if (updateAgo) {
                    updateAgo.textContent = '--';
                }
                break;
            case 'success':
                const now = new Date();

                const dateStr = now.toLocaleDateString('pt-PT', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });

                const timeStr = now.toLocaleTimeString('pt-PT', {
                    hour: '2-digit',
                    minute: '2-digit'
                });

                lastUpdate.textContent = dateStr;

                if (updateTime) {
                    updateTime.querySelector('span').textContent = timeStr;
                }

                if (updateAgo) {
                    updateAgo.textContent = 'just now';
                }
                break;
            case 'error':
                lastUpdate.textContent = '--';
                if (updateTime) {
                    updateTime.querySelector('span').textContent = '--';
                }
                if (updateAgo) {
                    updateAgo.textContent = 'error';
                }
                break;
        }
    }

    startAutoRefresh() {
        setInterval(() => this.loadData(), this.refreshInterval);
    }
}

document.addEventListener('DOMContentLoaded', () => new STCPDashboard());