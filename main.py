from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import api_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and admin account
    try:
        from app.core.database import Base, engine, SessionLocal
        from app.models.models import TaiKhoan
        import app.models.models
        
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        admin = db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == 'admin').first()
        if not admin:
            new_admin = TaiKhoan(
                MaTaiKhoan='TKADMIN',
                TenDangNhap='admin',
                MatKhau='admin',
                Email='admin@nextgen.com',
                VaiTro='ADMIN',
                TrangThai=True
            )
            db.add(new_admin)
            db.commit()
        db.close()
    except Exception as e:
        print("Database initialization error:", e)
        
    yield

app = FastAPI(title="NextGen HMS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to QuanLyKhamBenh API"}
