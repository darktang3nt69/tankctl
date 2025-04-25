from sqlalchemy import text
from app.db.session import engine

def upgrade():
    with engine.connect() as connection:
        # Alter the token column to increase its size
        connection.execute(text("""
            ALTER TABLE tanks 
            ALTER COLUMN token TYPE VARCHAR(512);
        """))
        connection.commit()

def downgrade():
    with engine.connect() as connection:
        # Revert the token column back to its original size
        connection.execute(text("""
            ALTER TABLE tanks 
            ALTER COLUMN token TYPE VARCHAR(64);
        """))
        connection.commit()

if __name__ == "__main__":
    upgrade() 