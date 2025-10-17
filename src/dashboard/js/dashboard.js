class STCPDashboard {
    constructor() {
        this.map = null;
        this.charts = {};
        this.apiBase = '/api';
        this.refreshInterval = 300000;
        this.accentColor = '#4a90e2';
        this.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        this.monoFontFamily = "'Inter', sans-serif";
        this.init();
    }

    async init() {
        this.setupChartDefaults();
        this.initMap();
        await this.loadData();
        this.startAutoRefresh();
        this.handleResize();
    }

    setupChartDefaults() {
        Chart.defaults.color = '#64748b';
        Chart.defaults.borderColor = '#e2e8f0';
        Chart.defaults.font.family = this.fontFamily;
        Chart.defaults.font.size = this.getResponsiveFontSize();
    }

    getResponsiveFontSize() {
        const vw = window.innerWidth;
        if (vw >= 3840) return 14;
        if (vw >= 2560) return 12;
        if (vw >= 1920) return 11;
        return 10;
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
        if (this.charts) {
            Object.values(this.charts).forEach(chart => {
                if (chart && chart.options) {
                    if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                        chart.options.plugins.legend.labels.font.size = this.getResponsiveFontSize();
                    }
                    if (chart.options.scales) {
                        if (chart.options.scales.x && chart.options.scales.x.ticks) {
                            chart.options.scales.x.ticks.font.size = this.getResponsiveFontSize() - 1;
                        }
                        if (chart.options.scales.y && chart.options.scales.y.ticks) {
                            chart.options.scales.y.ticks.font.size = this.getResponsiveFontSize() - 1;
                        }
                    }
                    try {
                        chart.update();
                    } catch (e) {
                        console.warn('Error updating chart:', e);
                    }
                }
            });
        }
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
        document.getElementById('total-paragens').textContent = data.total_paragens?.toLocaleString() || '--';
        document.getElementById('total-linhas').textContent = data.total_linhas?.toLocaleString() || '--';
        document.getElementById('total-horarios').textContent = data.total_horarios?.toLocaleString() || '--';
        document.getElementById('cobertura').textContent = data.cobertura || '--';
    }

    updateMap(paragens) {
        this.map.eachLayer(layer => {
            if (layer instanceof L.CircleMarker) this.map.removeLayer(layer);
        });

        const radius = window.innerWidth >= 2560 ? 10 : 8;
        
        paragens.forEach(paragem => {
            if (paragem.stop_lat && paragem.stop_lon) {
                L.circleMarker([paragem.stop_lat, paragem.stop_lon], {
                    radius: radius,
                    fillColor: this.accentColor,
                    color: '#ffffff',
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(this.map).bindPopup(`
                    <div style="font-family: ${this.fontFamily}; color: #1e293b;">
                        <h4 style="margin: 0 0 8px 0; color: ${this.accentColor}; font-family: ${this.fontFamily}; font-weight: 600;">${paragem.stop_name}</h4>
                        <p style="margin: 0; color: #64748b; font-size: 0.875rem;">
                            <strong>ID:</strong> ${paragem.stop_id}<br>
                            <strong>ZONE:</strong> ${paragem.area_geografica || 'N/A'}
                        </p>
                    </div>
                `);
            }
        });
    }

    updateRoutes(linhas) {
        const container = document.getElementById('routes-list');
        container.innerHTML = '';
        const maxItems = window.innerHeight > 1080 ? 12 : 8;
        
        linhas.slice(0, maxItems).forEach(linha => {
            const item = document.createElement('div');
            item.className = 'route-item';
            const color = '4a90e2';
            item.innerHTML = `
                <div class="route-badge" style="background-color: #${color};">${linha.route_short_name}</div>
                <div class="route-info">
                    <div class="route-name">${linha.route_long_name || linha.route_short_name}</div>
                    <div class="route-desc">${linha.route_desc || 'BUS ROUTE'}</div>
                </div>`;
            container.appendChild(item);
        });
    }

    updateTopStops(stops) {
        const container = document.getElementById('top-stops');
        container.innerHTML = '';
        const maxItems = window.innerHeight > 1080 ? 10 : 6;
        
        stops.slice(0, maxItems).forEach((stop, index) => {
            const item = document.createElement('div');
            item.className = 'stop-item';
            item.innerHTML = `
                <div class="stop-rank">${index + 1}</div>
                <div class="stop-info">
                    <div class="stop-name">${stop.stop_name}</div>
                    <div class="stop-count">${stop.total_horarios?.toLocaleString() || 0} SCHEDULES</div>
                </div>`;
            container.appendChild(item);
        });
    }

    updateHubs(hubs) {
        const container = document.getElementById('hubs-list');
        container.innerHTML = '';
        const maxItems = window.innerHeight > 1080 ? 10 : 6;
        
        hubs.slice(0, maxItems).forEach((hub, index) => {
            const item = document.createElement('div');
            item.className = 'hub-item';
            item.innerHTML = `
                <div class="hub-rank">${index + 1}</div>
                <div class="hub-info">
                    <div class="hub-name">${hub.stop_name}</div>
                    <div class="hub-details">${hub.total_linhas} ROUTES • ${hub.total_viagens} TRIPS</div>
                    <div class="hub-lines">${hub.linhas ? hub.linhas.join(', ') : ''}</div>
                </div>`;
            container.appendChild(item);
        });
    }

    createOrUpdateChart(chartId, type, data, options) {
        const ctx = document.getElementById(chartId).getContext('2d');
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
        }
        
        const fontSize = this.getResponsiveFontSize();
        
        if (!options.plugins) options.plugins = {};
        if (!options.plugins.legend) options.plugins.legend = {};
        if (!options.plugins.legend.labels) options.plugins.legend.labels = {};
        options.plugins.legend.labels.font = { size: fontSize };
        
        if (options.scales) {
            if (options.scales.x) {
                if (!options.scales.x.ticks) options.scales.x.ticks = {};
                options.scales.x.ticks.font = { size: fontSize - 1 };
            }
            if (options.scales.y) {
                if (!options.scales.y.ticks) options.scales.y.ticks = {};
                options.scales.y.ticks.font = { size: fontSize - 1 };
            }
        }
        
        this.charts[chartId] = new Chart(ctx, { type, data, options });
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
                backgroundColor: ['#4a90e2', '#357abd', '#5ba0e6', '#7db0ea', '#9fc0ee', '#c1d0f2'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        }, {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { 
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        padding: 10, 
                        usePointStyle: true, 
                        color: '#64748b'
                    } 
                } 
            }
        });
    }

    updateDistanceChart(data) {
        const maxItems = window.innerWidth > 2560 ? 15 : 10;
        const topItems = data.slice(0, maxItems);
        
        this.createOrUpdateChart('distance-chart', 'bar', {
            labels: topItems.map(item => item.route_short_name),
            datasets: [{
                label: 'Distance (km)',
                data: topItems.map(item => item.km_total),
                backgroundColor: this.accentColor,
            }]
        }, {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
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
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: window.innerWidth > 2560 ? 4 : 3
            }]
        }, {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
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
        switch (status) {
            case 'loading':
                lastUpdate.textContent = '--';
                break;
            case 'success':
                const now = new Date();
                lastUpdate.textContent = now.toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
                break;
            case 'error':
                lastUpdate.textContent = 'ERROR';
                break;
        }
    }

    startAutoRefresh() {
        setInterval(() => this.loadData(), this.refreshInterval);
    }
}

document.addEventListener('DOMContentLoaded', () => new STCPDashboard());
