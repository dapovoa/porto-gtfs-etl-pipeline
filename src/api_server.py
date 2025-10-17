#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

from config import DATABASE_URL

app = FastAPI(
    title="STCP Dashboard API",
    description="API for the STCP Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

engine = create_engine(DATABASE_URL)

def get_db_connection():
    try:
        return engine.connect()
    except SQLAlchemyError as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@api_router.get("/kpi", summary="Get Key Performance Indicators")
async def get_kpi_data():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT total_paragens, total_linhas, total_horarios, operadora, data_atualizacao FROM analytics.kpi_summary LIMIT 1"))
            row = result.fetchone()
            if row:
                return {
                    "total_paragens": row[0], "total_linhas": row[1], "total_horarios": row[2],
                    "operadora": row[3], "data_atualizacao": row[4].isoformat() if row[4] else None, "cobertura": "100%"
                }
            return {"total_paragens": 0, "total_linhas": 0, "total_horarios": 0, "operadora": "N/A", "cobertura": "0%"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPI data: {e}")

@api_router.get("/paragens", summary="Get all stops for map display")
async def get_paragens():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT stop_id, stop_name, stop_lat, stop_lon, area_geografica FROM analytics.paragens_mapa WHERE stop_lat IS NOT NULL AND stop_lon IS NOT NULL ORDER BY stop_name"))
            return [
                {
                    "stop_id": row[0], "stop_name": row[1], "stop_lat": float(row[2]),
                    "stop_lon": float(row[3]), "area_geografica": row[4]
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stops data: {e}")

@api_router.get("/linhas", summary="Get all routes")
async def get_linhas():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT route_id, route_short_name, route_long_name, route_desc, route_color, route_text_color, tipo_transporte FROM analytics.linhas_dashboard ORDER BY route_short_name"))
            return [
                {
                    "route_id": row[0], "route_short_name": row[1], "route_long_name": row[2],
                    "route_desc": row[3], "route_color": row[4], "route_text_color": row[5],
                    "tipo_transporte": row[6]
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching routes data: {e}")

@api_router.get("/top-stops", summary="Get top 10 busiest stops")
async def get_top_stops():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT stop_id, stop_name, stop_lat, stop_lon, total_horarios FROM analytics.top_paragens_horarios ORDER BY total_horarios DESC LIMIT 10"))
            return [
                {
                    "stop_id": row[0], "stop_name": row[1], "stop_lat": float(row[2]) if row[2] else None,
                    "stop_lon": float(row[3]) if row[3] else None, "total_horarios": row[4]
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top stops data: {e}")

@api_router.get("/hubs-transferencia", summary="Get main transfer hubs")
async def get_hubs_transferencia():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT stop_id, stop_name, stop_lat, stop_lon, total_linhas, total_viagens, linhas FROM analytics.hubs_transferencia ORDER BY total_linhas DESC"))
            return [
                {
                    "stop_id": row[0], "stop_name": row[1], "stop_lat": float(row[2]) if row[2] else None,
                    "stop_lon": float(row[3]) if row[3] else None, "total_linhas": row[4],
                    "total_viagens": row[5], "linhas": row[6]
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transfer hubs data: {e}")

@api_router.get("/quilometragem-linhas", summary="Get route distances")
async def get_quilometragem_linhas():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT route_id, route_short_name, route_long_name, total_shapes, km_medio, km_total FROM analytics.quilometragem_linhas ORDER BY km_total DESC"))
            return [
                {
                    "route_id": row[0], "route_short_name": row[1], "route_long_name": row[2],
                    "total_shapes": row[3], "km_medio": float(row[4]) if row[4] else 0,
                    "km_total": float(row[5]) if row[5] else 0
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route distance data: {e}")

@api_router.get("/frequencia-servico", summary="Get service frequency")
async def get_frequencia_servico():
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT route_id, route_short_name, route_long_name, hora, total_viagens, total_passagens FROM analytics.frequencia_servico ORDER BY route_short_name, hora"))
            return [
                {
                    "route_id": row[0], "route_short_name": row[1], "route_long_name": row[2],
                    "hora": row[3], "total_viagens": row[4], "total_passagens": row[5]
                } for row in result
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching service frequency data: {e}")

app.include_router(api_router)

dashboard_dir = Path(__file__).parent / "dashboard"

# Mount static files directories
app.mount("/css", StaticFiles(directory=str(dashboard_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(dashboard_dir / "js")), name="js")
app.mount("/icons", StaticFiles(directory=str(dashboard_dir / "icons")), name="icons")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(dashboard_dir / 'index.html')

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
