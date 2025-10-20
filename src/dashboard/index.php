<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STCP Operations Dashboard</title>
    <link rel="icon" type="image/x-icon" href="icons/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="icons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="512x512" href="icons/icon-512x512.png">
    <link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192x192.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <div class="header-left">
                <div class="brand">
                    <img src="icons/icon-192x192.png" alt="STCP Logo" class="brand-logo-img">
                    <div class="brand-text">
                        <h1>Porto GTFS Dashboard</h1>
                        <div class="brand-subtitle">Transport Data Analytics</div>
                    </div>
                </div>
            </div>
            <div class="header-right">
                <button class="header-action-btn" id="theme-toggle" aria-label="Toggle theme">
                    <i class="fas fa-moon"></i>
                </button>
            </div>
        </header>
        <main class="dashboard-main">
            <section class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-label">Total Stops</div>
                    </div>
                    <div class="kpi-value" id="total-paragens">-</div>
                    <div class="kpi-footer">
                        <div class="kpi-change positive" id="stops-change">
                            <i class="fas fa-arrow-up"></i>
                            <span>+2.5%</span>
                        </div>
                        <div class="kpi-meta">vs last week</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-label">Active Routes</div>
                    </div>
                    <div class="kpi-value" id="total-linhas">-</div>
                    <div class="kpi-footer">
                        <div class="kpi-change positive" id="routes-change">
                            <i class="fas fa-arrow-up"></i>
                            <span>+1</span>
                        </div>
                        <div class="kpi-meta">vs last month</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-label">Daily Schedules</div>
                    </div>
                    <div class="kpi-value" id="total-horarios">-</div>
                    <div class="kpi-footer">
                        <div class="kpi-change positive" id="schedules-change">
                            <i class="fas fa-arrow-up"></i>
                            <span>+12%</span>
                        </div>
                        <div class="kpi-meta">vs last week</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-label">Coverage Area</div>
                    </div>
                    <div class="kpi-value" id="cobertura">-</div>
                    <div class="kpi-footer">
                        <div class="kpi-change neutral" id="coverage-change">
                            <i class="fas fa-check"></i>
                            <span>5 zones</span>
                        </div>
                        <div class="kpi-meta">metro area</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-label">Last Updated</div>
                    </div>
                    <div class="kpi-value kpi-value-small" id="last-update">--</div>
                    <div class="kpi-footer">
                        <div class="kpi-change neutral" id="update-time">
                            <i class="fas fa-clock"></i>
                            <span>--</span>
                        </div>
                        <div class="kpi-meta" id="update-ago">--</div>
                    </div>
                </div>
            </section>
            <section class="content-grid">
                <div class="widget widget-map">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Operations Map</h2>
                            <span class="widget-badge" id="map-stops-count">-</span>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Refresh">
                                <i class="fas fa-sync-alt"></i>
                            </button>
                            <button class="widget-action-btn" aria-label="Fullscreen">
                                <i class="fas fa-expand"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content" style="padding: 0;">
                        <div id="map"></div>
                    </div>
                </div>
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Zone Distribution</h2>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content chart-container">
                        <canvas id="zone-chart"></canvas>
                    </div>
                </div>
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Main Routes</h2>
                            <span class="widget-badge" id="routes-count">-</span>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Filter">
                                <i class="fas fa-filter"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content">
                        <div class="list-container" id="routes-list"></div>
                    </div>
                </div>
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Distance by Route</h2>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content chart-container">
                        <canvas id="distance-chart"></canvas>
                    </div>
                </div> 
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Top Stops</h2>
                            <span class="widget-badge">Busiest</span>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Filter">
                                <i class="fas fa-filter"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content">
                        <div class="list-container" id="top-stops"></div>
                    </div>
                </div>
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Service Frequency</h2>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content chart-container">
                        <canvas id="frequency-chart"></canvas>
                    </div>
                </div>
                <div class="widget">
                    <div class="widget-header">
                        <div class="widget-title-section">
                            <h2 class="widget-title">Transfer Hubs</h2>
                            <span class="widget-badge">3+ routes</span>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-action-btn" aria-label="Filter">
                                <i class="fas fa-filter"></i>
                            </button>
                        </div>
                    </div>
                    <div class="widget-content">
                        <div class="list-container" id="hubs-list"></div>
                    </div>
                </div>
            </section>
        </main>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="js/dashboard.js"></script>
</body>
</html>