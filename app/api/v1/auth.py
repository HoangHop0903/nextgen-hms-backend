from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime
import shutil
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend root directory (parent of app/)
_backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_dir / ".env")

from app.core.database import get_db
from app.models.models import TaiKhoan, BenhNhan, BacSi, NhanVien
from app.schemas.schemas import LoginRequest, LoginResponse

router = APIRouter()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    phone: str
    gender: str
    dob: datetime.date

class GoogleLoginRequest(BaseModel):
    token: str

class UpdateProfileRequest(BaseModel):
    mat_khau: str = None
    email: str = None
    ho_ten: str = None
    sdt: str = None
    anh_dai_dien: str = None

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user_account(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token.startswith("dummy_token_for_"):
        ma_tk = token.replace("dummy_token_for_", "")
        acc = db.query(TaiKhoan).filter(TaiKhoan.MaTaiKhoan == ma_tk).first()
        if not acc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        return acc
    raise HTTPException(status_code=401, detail="Xác thực thất bại")

import unicodedata

def normalize_role(role: str) -> str:
    if not role: return ""
    return unicodedata.normalize('NFD', role).encode('ascii', 'ignore').decode('utf-8').lower().replace(' ', '')

@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...)):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join("uploads", filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"http://localhost:8000/uploads/{filename}"}

@router.put("/profile")
def update_profile(req: UpdateProfileRequest, db: Session = Depends(get_db), current_user: TaiKhoan = Depends(get_current_user_account)):
    if req.mat_khau:
        current_user.MatKhau = req.mat_khau
    if req.email:
        # Check if email is used by someone else
        existing = db.query(TaiKhoan).filter(TaiKhoan.Email == req.email, TaiKhoan.MaTaiKhoan != current_user.MaTaiKhoan).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email đã được sử dụng bởi người khác")
        current_user.Email = req.email
        
    # Update linked personal info
    if req.ho_ten or req.sdt or req.anh_dai_dien:
        role_norm = normalize_role(current_user.VaiTro)
        if "benhnhan" in role_norm or "benh" in role_norm:
            bn = db.query(BenhNhan).filter(BenhNhan.MaTaiKhoan == current_user.MaTaiKhoan).first()
            if bn:
                if req.ho_ten: bn.HoTen = req.ho_ten
                if req.sdt: bn.SDT = req.sdt
                if req.anh_dai_dien: bn.AnhDaiDien = req.anh_dai_dien
        elif "bacsi" in role_norm:
            bs = db.query(BacSi).filter(BacSi.MaTaiKhoan == current_user.MaTaiKhoan).first()
            if bs:
                if req.ho_ten: bs.HoTen = req.ho_ten
                if req.sdt: bs.SDT = req.sdt
                if req.anh_dai_dien: bs.AnhDaiDien = req.anh_dai_dien
        elif "nhanvien" in role_norm:
            nv = db.query(NhanVien).filter(NhanVien.MaTaiKhoan == current_user.MaTaiKhoan).first()
            if nv:
                if req.ho_ten: nv.HoTen = req.ho_ten
                if req.sdt: nv.SDT = req.sdt
                if req.anh_dai_dien: nv.AnhDaiDien = req.anh_dai_dien

    db.commit()
    return {"message": "Cập nhật hồ sơ thành công"}

@router.get("/me")
def get_my_info(db: Session = Depends(get_db), current_user: TaiKhoan = Depends(get_current_user_account)):
    info = {
        "MaTaiKhoan": current_user.MaTaiKhoan,
        "TenDangNhap": current_user.TenDangNhap,
        "Email": current_user.Email,
        "VaiTro": current_user.VaiTro,
        "HoTen": ""
    }
    
    role_norm = normalize_role(current_user.VaiTro)
    if "benhnhan" in role_norm or "benh" in role_norm:
        bn = db.query(BenhNhan).filter(BenhNhan.MaTaiKhoan == current_user.MaTaiKhoan).first()
        if bn: info["HoTen"] = bn.HoTen
    elif "bacsi" in role_norm:
        bs = db.query(BacSi).filter(BacSi.MaTaiKhoan == current_user.MaTaiKhoan).first()
        if bs: info["HoTen"] = bs.HoTen
    elif "nhanvien" in role_norm:
        nv = db.query(NhanVien).filter(NhanVien.MaTaiKhoan == current_user.MaTaiKhoan).first()
        if nv: info["HoTen"] = nv.HoTen
    else:
        info["HoTen"] = "Admin"
        
    return info

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == login_data.username).first()
    
    if not user or user.MatKhau != login_data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tên đăng nhập hoặc mật khẩu không đúng")
    
    if not user.TrangThai:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khoá")
    
    return LoginResponse(
        access_token=f"dummy_token_for_{user.MaTaiKhoan}",
        token_type="bearer",
        role=user.VaiTro,
        ma_tai_khoan=user.MaTaiKhoan
    )

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username or email exists
    if db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == req.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
        
    import random
    ma_tk = f"TK{random.randint(1000, 99999)}"
    ma_bn = f"BN{random.randint(1000, 99999)}"
    
    new_user = TaiKhoan(
        MaTaiKhoan=ma_tk,
        TenDangNhap=req.username,
        MatKhau=req.password,
        Email=req.email,
        VaiTro="BENHNHAN",
        TrangThai=True
    )
    
    new_patient = BenhNhan(
        MaBenhNhan=ma_bn,
        MaTaiKhoan=ma_tk,
        HoTen=req.full_name,
        NgaySinh=req.dob,
        GioiTinh=req.gender,
        SDT=req.phone,
        TrangThai=True
    )
    
    db.add(new_user)
    db.add(new_patient)
    db.commit()
    
    return {"message": "Đăng ký thành công", "username": req.username}

@router.post("/google-login")
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503, 
            detail="Chức năng đăng nhập Google chưa được cấu hình. Vui lòng liên hệ quản trị viên."
        )
    
    try:
        # Xác thực token Google thật
        idinfo = id_token.verify_oauth2_token(req.token, requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']
        name = idinfo.get('name', 'Google User')
        picture = idinfo.get('picture', '')

        # Check if user exists by email
        user = db.query(TaiKhoan).filter(TaiKhoan.Email == email).first()
        if not user:
            # Create a new patient account automatically
            import random
            ma_tk = f"TK{random.randint(10000, 99999)}"
            ma_bn = f"BN{random.randint(10000, 99999)}"
            
            user = TaiKhoan(
                MaTaiKhoan=ma_tk,
                TenDangNhap=email.split("@")[0],
                MatKhau="google_oauth",  # Placeholder - user logs in via Google only
                Email=email,
                VaiTro="BENHNHAN",
                TrangThai=True
            )
            
            patient = BenhNhan(
                MaBenhNhan=ma_bn,
                MaTaiKhoan=ma_tk,
                HoTen=name,
                GioiTinh="Khác",
                SDT="",
                AnhDaiDien=picture,
                TrangThai=True
            )
            db.add(user)
            db.add(patient)
            db.commit()

        if not user.TrangThai:
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khoá")

        return LoginResponse(
            access_token=f"dummy_token_for_{user.MaTaiKhoan}",
            token_type="bearer",
            role=user.VaiTro,
            ma_tai_khoan=user.MaTaiKhoan
        )
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token Google không hợp lệ: {str(e)}")

