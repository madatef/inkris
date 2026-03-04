from dotenv import load_dotenv
import aioduckdb

from app.config import settings

load_dotenv()

# Global singleton
_con: aioduckdb.Connection | None = None

async def init_db():
    """Initialize the database connection. Call this from lifespan."""
    global _con
    _con = await aioduckdb.connect(':memory:')
    
    await _con.execute("INSTALL httpfs")
    await _con.execute("LOAD httpfs")
    
    # Configure S3. DuckDB reads env vars by default, but we wanna leave nothing for chance
    await _con.execute(f"""
        SET s3_region='{settings.AWS_REGION}';
        SET s3_access_key_id='{settings.AWS_ACCESS_KEY_ID}';
        SET s3_secret_access_key='{settings.AWS_SECRET_ACCESS_KEY}';
    """)

async def close_db():
    """Close the database connection. Call this from lifespan cleanup."""
    global _con
    if _con:
        await _con.close()
        _con = None

def get_con() -> aioduckdb.Connection:
    """Dependency function."""
    if _con is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _con
