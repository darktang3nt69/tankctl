from sqlalchemy.orm import Session
from sqlalchemy import desc, distinct, func, and_
from app.models.status_log import StatusLog
from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy.sql import text, table, column

def get_latest_status_data(db: Session):
    """
    Retrieves the most recent status log entry for each unique tank_id.
    """
    # This is a common pattern in TimescaleDB/PostgreSQL
    # to get the latest record per group.
    latest_statuses = db.query(StatusLog).distinct(StatusLog.tank_id).order_by(StatusLog.tank_id, desc(StatusLog.timestamp)).all()
    return latest_statuses

def get_historical_status_data(db: Session, tank_id: UUID):
    """
    Retrieves all status log entries for a specific tank_id, ordered by timestamp.
    """
    # Query the status_logs table for the given tank_id
    historical_data = db.query(StatusLog).filter(StatusLog.tank_id == tank_id).order_by(StatusLog.timestamp).all()
    return historical_data

def get_time_windowed_status_data(db: Session, tank_id: UUID, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, resolution: Optional[str] = None):
    """
    Retrieves status log data for a specific tank within a time window, with optional aggregation and gap filling.
    Utilizes TimescaleDB's continuous aggregates for efficient querying of pre-aggregated data
    when a supported resolution is provided (e.g., '1 hour', '1 day', '5 minutes').
    For other resolutions or when no resolution is specified, it queries the raw hypertable
    and can apply `time_bucket_gapfill` for on-the-fly aggregation and gap filling.
    See TimescaleDB documentation for `time_bucket_gapfill`: https://docs.timescale.com/api/latest/hyperfunctions/time_bucket_gapfill/
    See TimescaleDB documentation for continuous aggregates: https://docs.timescale.com/api/latest/continuous-aggregates/

    Business Logic:
    - Determines the appropriate data source (continuous aggregate or raw hypertable) based on `resolution`.
    - For supported resolutions, it queries the respective continuous aggregate table
      (`hourly_status_aggregates`, `daily_status_aggregates`, `five_min_status_aggregates`).
      These tables contain pre-computed `avg_temperature`, `min_temperature`, `max_temperature`,
      `avg_ph`, `min_ph`, and `max_ph` for the given time bucket.
    - For unsupported resolutions or raw data requests, it queries the `status_logs` hypertable.
    - If a `resolution` is provided but not supported by a continuous aggregate, it uses
      TimescaleDB's `time_bucket_gapfill` function on the raw data to create time-based
      buckets and fill missing data points. This ensures a continuous series for charting.
    - Filters data by `tank_id` and optional `start_time` and `end_time`.
    - Orders results by time/timestamp.
    """
    query = None

    # Define table objects for continuous aggregates
    hourly_agg_table = table('hourly_status_aggregates')
    daily_agg_table = table('daily_status_aggregates')
    five_min_agg_table = table('five_min_status_aggregates') # Define 5-minute aggregate table object

    # Check for supported continuous aggregate resolutions
    if resolution == '1 hour':
        # Query the hourly continuous aggregate
        query = db.query(
            column('time'),
            column('tank_id'),
            column('avg_temperature'),
            column('min_temperature'),
            column('max_temperature'),
            column('avg_ph'),
            column('min_ph'),
            column('max_ph')
        ).select_from(hourly_agg_table).filter(column('tank_id') == tank_id)
        
        if start_time:
            query = query.filter(column('time') >= start_time)
        if end_time:
             query = query.filter(column('time') <= end_time)

        query = query.order_by(column('time'))

    elif resolution == '1 day':
        # Query the daily continuous aggregate
         query = db.query(
            column('time'),
            column('tank_id'),
            column('avg_temperature'),
            column('min_temperature'),
            column('max_temperature'),
            column('avg_ph'),
            column('min_ph'),
            column('max_ph')
        ).select_from(daily_agg_table).filter(column('tank_id') == tank_id)
        
         if start_time:
            query = query.filter(column('time') >= start_time)
         if end_time:
             query = query.filter(column('time') <= end_time)
             
         query = query.order_by(column('time'))

    elif resolution == '5 minutes': # Add support for 5-minute resolution
         # Query the 5-minute continuous aggregate
         query = db.query(
            column('time'),
            column('tank_id'),
            column('avg_temperature'),
            column('min_temperature'),
            column('max_temperature'),
            column('avg_ph'),
            column('min_ph'),
            column('max_ph')
        ).select_from(five_min_agg_table).filter(column('tank_id') == tank_id)
        
         if start_time:
            query = query.filter(column('time') >= start_time)
         if end_time:
             query = query.filter(column('time') <= end_time)
             
         query = query.order_by(column('time'))

    else:
        # No supported resolution or no resolution provided, query raw hypertable with time_bucket_gapfill if resolution given
        query = db.query(StatusLog).filter(StatusLog.tank_id == tank_id)

        if start_time:
            query = query.filter(StatusLog.timestamp >= start_time)
        if end_time:
            query = query.filter(StatusLog.timestamp <= end_time)

        if resolution:
            # Use time_bucket_gapfill for aggregation and gap filling on raw data for unsupported resolutions
            bucket_interval = text(f"INTERVAL '{resolution}'")
            query = db.query(
                func.time_bucket_gapfill(bucket_interval, StatusLog.timestamp).label('time'),
                StatusLog.tank_id,
                func.avg(StatusLog.temperature).label('avg_temperature'),
                func.min(StatusLog.temperature).label('min_temperature'),
                func.max(StatusLog.temperature).label('max_temperature'),
                func.avg(StatusLog.ph).label('avg_ph'),
                func.min(StatusLog.ph).label('min_ph'),
                func.max(StatusLog.ph).label('max_ph'),
            ).filter(StatusLog.tank_id == tank_id)
            
            if start_time:
                # Need to use text() for comparison with time_bucket_gapfill output if using raw text interval
                 query = query.filter(text('time') >= text(f'\' {start_time.isoformat()}\''))
            if end_time:
                query = query.filter(text('time') <= text(f'\' {end_time.isoformat()}\''))
                
            query = query.group_by('time', StatusLog.tank_id).order_by('time')
        else:
            # No resolution, just filter by time range and order raw data
            query = query.order_by(StatusLog.timestamp)

    return query.all() 