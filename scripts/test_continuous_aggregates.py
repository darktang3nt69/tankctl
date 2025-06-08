import click
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Database URL from settings
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Create engine and session local for direct interaction
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@click.group()
def agg_test():
    """
    Continuous Aggregate testing commands.
    """
    pass

@agg_test.command("refresh")
@click.option("--aggregate-name", type=str, help="Name of the continuous aggregate to refresh (e.g., hourly_status_aggregates).")
def refresh_aggregate(aggregate_name: str):
    """
    Manually refreshes a specified continuous aggregate and measures its duration.
    """
    db = SessionLocal()
    try:
        if not aggregate_name:
            click.echo("Error: --aggregate-name is required.")
            return

        click.echo(f"Refreshing continuous aggregate: {aggregate_name}...")
        start_time = time.time()
        db.execute(text(f"REFRESH MATERIALIZED VIEW {aggregate_name};"))
        db.commit()
        end_time = time.time()
        duration = end_time - start_time
        click.echo(f"Successfully refreshed {aggregate_name} in {duration:.4f} seconds.")

    except Exception as e:
        click.echo(f"Error refreshing aggregate {aggregate_name}: {e}")
        db.rollback()
    finally:
        db.close()

@agg_test.command("test-all")
def test_all_aggregates():
    """
    Tests the refresh performance of all predefined continuous aggregates.
    """
    aggregates_to_test = [
        "hourly_status_aggregates",
        "daily_status_aggregates",
        "five_min_status_aggregates"
    ]

    for agg_name in aggregates_to_test:
        db = SessionLocal() # Create a new session for each refresh
        try:
            click.echo(f"\nRefreshing continuous aggregate: {agg_name}...")
            start_time = time.time()
            db.execute(text(f"REFRESH MATERIALIZED VIEW {agg_name};"))
            db.commit()
            end_time = time.time()
            duration = end_time - start_time
            click.echo(f"Successfully refreshed {agg_name} in {duration:.4f} seconds.")
        except Exception as e:
            click.echo(f"Error refreshing aggregate {agg_name}: {e}")
            db.rollback()
        finally:
            db.close()


if __name__ == "__main__":
    agg_test() 