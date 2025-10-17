-- Creates schemas and raw tables for STCP GTFS data

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.agency (
    agency_id VARCHAR(255) PRIMARY KEY,
    agency_name VARCHAR(255),
    agency_url TEXT,
    agency_timezone VARCHAR(100),
    agency_lang VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.calendar (
    service_id VARCHAR(255) PRIMARY KEY,
    monday INTEGER DEFAULT 0,
    tuesday INTEGER DEFAULT 0,
    wednesday INTEGER DEFAULT 0,
    thursday INTEGER DEFAULT 0,
    friday INTEGER DEFAULT 0,
    saturday INTEGER DEFAULT 0,
    sunday INTEGER DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.calendar_dates (
    service_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    exception_type INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (service_id, date)
);

CREATE TABLE IF NOT EXISTS raw.routes (
    route_id VARCHAR(255) PRIMARY KEY,
    route_short_name VARCHAR(255),
    route_long_name VARCHAR(255),
    route_desc TEXT,
    route_type INTEGER,
    route_url TEXT,
    route_color VARCHAR(10),
    route_text_color VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.shapes (
    shape_id VARCHAR(255) NOT NULL,
    shape_pt_lat NUMERIC(10,8) NOT NULL,
    shape_pt_lon NUMERIC(11,8) NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

CREATE TABLE IF NOT EXISTS raw.stop_times (
    trip_id VARCHAR(255) NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id VARCHAR(255) NOT NULL,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.stops (
    stop_id VARCHAR(255) PRIMARY KEY,
    stop_code VARCHAR(255),
    stop_name VARCHAR(255),
    stop_lat NUMERIC(10,8),
    stop_lon NUMERIC(11,8),
    zone_id VARCHAR(255),
    stop_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.transfers (
    from_stop_id VARCHAR(255) NOT NULL,
    to_stop_id VARCHAR(255) NOT NULL,
    transfer_type INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_stop_id, to_stop_id)
);

CREATE TABLE IF NOT EXISTS raw.trips (
    route_id VARCHAR(255) NOT NULL,
    direction_id INTEGER NOT NULL,
    service_id VARCHAR(255) NOT NULL,
    trip_id VARCHAR(255) PRIMARY KEY,
    trip_headsign VARCHAR(255),
    wheelchair_accessible INTEGER DEFAULT 0,
    block_id VARCHAR(255),
    shape_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
