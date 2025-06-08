import click
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.status_log import StatusLog
from datetime import datetime, timedelta
import uuid

@click.group()
def db_perf():
    """
    Database performance analysis commands.
    """
    pass

@db_perf.command("analyze-query")
@click.option("--query-type", type=click.Choice([
    "get_latest_status_data",
    "get_historical_status_data",
    "get_time_windowed_status_data_hourly",
    "get_time_windowed_status_data_daily",
    "get_time_windowed_status_data_5min",
    "get_time_windowed_status_data_raw"
]), required=True, help="Type of query to analyze.")
@click.option("--tank-id", type=str, help="Tank ID for historical and time-windowed queries.")
@click.option("--start-time", type=str, help="Start time for queries (YYYY-MM-DDTHH:MM:SS).")
@click.option("--end-time", type=str, help="End time for queries (YYYY-MM-DDTHH:MM:SS).")
def analyze_query(
    query_type: str,
    tank_id: str | None,
    start_time: str | None,
    end_time: str | None,
):
    """
    Analyzes the performance of a specific database query using EXPLAIN ANALYZE.
    """
    db = SessionLocal()
    try:
        query_to_execute = ""
        params = {}

        if query_type == "get_latest_status_data":
            query_to_execute = "SELECT DISTINCT ON (tank_id) * FROM status_logs ORDER BY tank_id, timestamp DESC"
        elif query_type == "get_historical_status_data":
            if not tank_id:
                click.echo("Error: --tank-id is required for get_historical_status_data.")
                return
            query_to_execute = "SELECT * FROM status_logs WHERE tank_id = :tank_id ORDER BY timestamp ASC"
            params = {"tank_id": tank_id}
        elif query_type.startswith("get_time_windowed_status_data"):
            if not tank_id:
                click.echo("Error: --tank-id is required for time-windowed queries.")
                return
            
            base_query = ""
            if query_type == "get_time_windowed_status_data_hourly":
                base_query = "SELECT time, tank_id, avg_temperature, min_temperature, max_temperature, avg_ph, min_ph, max_ph FROM hourly_status_aggregates WHERE tank_id = :tank_id"
            elif query_type == "get_time_windowed_status_data_daily":
                base_query = "SELECT time, tank_id, avg_temperature, min_temperature, max_temperature, avg_ph, min_ph, max_ph FROM daily_status_aggregates WHERE tank_id = :tank_id"
            elif query_type == "get_time_windowed_status_data_5min":
                base_query = "SELECT time, tank_id, avg_temperature, min_temperature, max_temperature, avg_ph, min_ph, max_ph FROM five_min_status_aggregates WHERE tank_id = :tank_id"
            elif query_type == "get_time_windowed_status_data_raw":
                # This mimics time_bucket_gapfill query, might need exact mapping for full test
                base_query = """
                SELECT time_bucket_gapfill(INTERVAL '1 hour', timestamp) AS time,
                       tank_id,
                       avg(temperature) AS avg_temperature,
                       min(temperature) AS min_temperature,
                       max(temperature) AS max_temperature,
                       avg(ph) AS avg_ph,
                       min(ph) AS min_ph,
                       max(ph) AS max_ph
                FROM status_logs
                WHERE tank_id = :tank_id
                """

            query_to_execute = base_query
            params = {"tank_id": tank_id}

            if start_time:
                st_dt = datetime.fromisoformat(start_time)
                query_to_execute += " AND time >= :start_time" if "aggregates" in query_type else " AND timestamp >= :start_time"
                params["start_time"] = st_dt
            if end_time:
                et_dt = datetime.fromisoformat(end_time)
                query_to_execute += " AND time <= :end_time" if "aggregates" in query_type else " AND timestamp <= :end_time"
                params["end_time"] = et_dt
            
            if query_type == "get_time_windowed_status_data_raw":
                 query_to_execute += " GROUP BY time, tank_id ORDER BY time"
            else:
                 query_to_execute += " ORDER BY time"

        else:
            click.echo("Invalid query type.")
            return
        
        click.echo(f"Analyzing query: {query_type}")
        click.echo(f"SQL: {query_to_execute}")
        click.echo(f"Params: {params}")

        result = db.execute(text(f"EXPLAIN ANALYZE {query_to_execute}"), params).fetchall()
        for row in result:
            click.echo(row[0])

    except Exception as e:
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    db_perf() 