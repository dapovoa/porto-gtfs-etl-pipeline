-- Service frequency by route and hour
CREATE OR REPLACE VIEW analytics.frequencia_servico AS
SELECT 
    t.route_id,
    r.route_short_name,
    r.route_long_name,
    EXTRACT(HOUR FROM st.departure_time::TIME) as hora,
    COUNT(DISTINCT t.trip_id) as total_viagens,
    COUNT(st.trip_id) as total_passagens
FROM raw.trips t
JOIN raw.routes r ON t.route_id = r.route_id
JOIN raw.stop_times st ON t.trip_id = st.trip_id
-- Safely filter out invalid time formats before casting
WHERE st.departure_time ~ '^\d{2}:\d{2}:\d{2}$' AND SUBSTRING(st.departure_time, 1, 2)::int < 24
GROUP BY t.route_id, r.route_short_name, r.route_long_name, EXTRACT(HOUR FROM st.departure_time::TIME)
ORDER BY t.route_id, hora;

-- Transfer hubs (stops with multiple routes)
CREATE OR REPLACE VIEW analytics.hubs_transferencia AS
SELECT 
    s.stop_id,
    s.stop_name,
    s.stop_lat,
    s.stop_lon,
    COUNT(DISTINCT t.route_id) as total_linhas,
    COUNT(DISTINCT t.trip_id) as total_viagens,
    ARRAY_AGG(DISTINCT r.route_short_name ORDER BY r.route_short_name) as linhas
FROM raw.stops s
JOIN raw.stop_times st ON s.stop_id = st.stop_id
JOIN raw.trips t ON st.trip_id = t.trip_id
JOIN raw.routes r ON t.route_id = r.route_id
GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
HAVING COUNT(DISTINCT t.route_id) >= 3
ORDER BY total_linhas DESC;

-- Route distances (approximated via shapes)
CREATE OR REPLACE VIEW analytics.quilometragem_linhas AS
WITH shape_distances AS (
    SELECT 
        shape_id,
        COUNT(*) as total_pontos,
        ROUND(
            (111.045 * SQRT(
                POWER(MAX(shape_pt_lat) - MIN(shape_pt_lat), 2) + 
                POWER(MAX(shape_pt_lon) - MIN(shape_pt_lon), 2)
            ))::numeric, 2
        ) as distancia_km
    FROM raw.shapes
    GROUP BY shape_id
)
SELECT 
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    COUNT(DISTINCT t.shape_id) as total_shapes,
    AVG(sd.distancia_km) as km_medio,
    SUM(sd.distancia_km) as km_total
FROM raw.routes r
JOIN raw.trips t ON r.route_id = t.route_id
JOIN shape_distances sd ON t.shape_id = sd.shape_id
WHERE t.shape_id != ''
GROUP BY r.route_id, r.route_short_name, r.route_long_name
ORDER BY km_total DESC;

-- Service patterns analysis
CREATE OR REPLACE VIEW analytics.padroes_servico AS
SELECT 
    c.service_id,
    CASE 
        WHEN c.monday = 1 AND c.tuesday = 1 AND c.wednesday = 1 AND c.thursday = 1 AND c.friday = 1 AND c.saturday = 0 AND c.sunday = 0 THEN 'Dias Uteis'
        WHEN c.saturday = 1 AND c.sunday = 0 THEN 'Sabados'
        WHEN c.sunday = 1 THEN 'Domingos'
        ELSE 'Outro'
    END as tipo_servico,
    c.start_date,
    c.end_date,
    COUNT(DISTINCT t.trip_id) as total_viagens,
    COUNT(DISTINCT t.route_id) as total_linhas
FROM raw.calendar c
JOIN raw.trips t ON c.service_id = t.service_id
GROUP BY c.service_id, tipo_servico, c.start_date, c.end_date
ORDER BY total_viagens DESC;

-- Stops for map display
CREATE OR REPLACE VIEW analytics.paragens_mapa AS
SELECT 
    s.stop_id,
    s.stop_name,
    s.stop_lat,
    s.stop_lon,
    CASE 
        WHEN s.stop_lat >= 41.2 AND s.stop_lon <= -8.6 THEN 'Norte'
        WHEN s.stop_lat >= 41.15 AND s.stop_lat < 41.2 AND s.stop_lon <= -8.6 THEN 'Centro'
        WHEN s.stop_lat < 41.15 AND s.stop_lon <= -8.6 THEN 'Sul'
        WHEN s.stop_lon > -8.6 THEN 'Este'
        ELSE 'Outras'
    END as area_geografica
FROM raw.stops s
WHERE s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL;

-- Routes for dashboard
CREATE OR REPLACE VIEW analytics.linhas_dashboard AS
SELECT 
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_desc,
    r.route_color,
    r.route_text_color,
    CASE r.route_type
        WHEN 0 THEN 'Eletrico'
        WHEN 3 THEN 'Autocarro'
        ELSE 'Outro'
    END as tipo_transporte
FROM raw.routes r;

-- Top stops by schedule count
CREATE OR REPLACE VIEW analytics.top_paragens_horarios AS
SELECT 
    s.stop_id,
    s.stop_name,
    s.stop_lat,
    s.stop_lon,
    COUNT(st.trip_id) as total_horarios
FROM raw.stops s
JOIN raw.stop_times st ON s.stop_id = st.stop_id
GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
ORDER BY total_horarios DESC
LIMIT 10;

-- Geographic distribution
CREATE OR REPLACE VIEW analytics.distribuicao_geografica AS
SELECT 
    area_geografica as zona,
    COUNT(*) as total_paragens,
    AVG(stop_lat) as lat_media,
    AVG(stop_lon) as lon_media
FROM analytics.paragens_mapa
GROUP BY area_geografica
ORDER BY total_paragens DESC;

-- KPI Summary
CREATE OR REPLACE VIEW analytics.kpi_summary AS
SELECT 
    (SELECT COUNT(*) FROM raw.stops) as total_paragens,
    (SELECT COUNT(*) FROM raw.routes) as total_linhas,
    (SELECT COUNT(*) FROM raw.stop_times) as total_horarios,
    (SELECT agency_name FROM raw.agency LIMIT 1) as operadora,
    (SELECT MAX(created_at) FROM raw.stops) as data_atualizacao;
