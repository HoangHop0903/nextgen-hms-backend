import sys
import os
from sqlalchemy import create_engine
from app.models.models import Base
from app.core.database import SessionLocal

# Update this connection string if needed
DATABASE_URL = "postgresql://postgres:[Hophoangluu0908588469]@db.pghpekvenlnzflenefuk.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL, echo=True)

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
