from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import datetime
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db
from app.models.models import (
    NhanVien, DatLichKham, BenhNhan, BacSi, LichLamViec, LichPhongKham, PhieuTiepNhan, CaKham, YeuCauHoTro, PhanHoiHoTro
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_staff(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token.startswith("dummy_token_for_"):
        ma_tk = token.replace("dummy_token_for_", "")
        nv = db.query(NhanVien).filter(NhanVien.MaTaiKhoan == ma_tk).first()
        if not nv:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ nhân viên")
        return nv
    raise HTTPException(status_code=401, detail="Xác thực thất bại")

@router.get("/me")
def get_my_info(staff: NhanVien = Depends(get_current_staff)):
    return {
        "MaNhanVien": staff.MaNhanVien,
        "HoTen": staff.HoTen,
        "ChucVu": staff.ChucVu,
        "SDT": staff.SDT,
        "AnhDaiDien": staff.AnhDaiDien
    }

@router.get("/bookings")
def get_all_bookings(db: Session = Depends(get_db), staff: NhanVien = Depends(get_current_staff)):
    bookings = db.query(DatLichKham).order_by(desc(DatLichKham.NgayDat)).all()
    result = []
    for b in bookings:
        bn = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == b.MaBenhNhan).first()
        llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == b.MaLichLamViec).first()
        bs_name = "Không rõ"
        ngay_kham = None
        ca_kham_ten = ""
        
        if llv:
            bs = db.query(BacSi).filter(BacSi.MaBacSi == llv.MaBacSi).first()
            if bs: bs_name = bs.HoTen
            
            lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first()
            if lpk:
                ngay_kham = lpk.NgayKham
                ca = db.query(CaKham).filter(CaKham.MaCaKham == lpk.MaCaKham).first()
                if ca: ca_kham_ten = ca.TenCa
        
        # Chỉ hiển thị các lịch khám từ hôm nay trở đi để nhân viên quản lý
        if ngay_kham and ngay_kham >= datetime.date.today() - datetime.timedelta(days=7):
            result.append({
                "MaDatLich": b.MaDatLich,
                "TenBenhNhan": bn.HoTen if bn else "Không rõ",
                "SDT": bn.SDT if bn else "Không rõ",
                "BacSi": bs_name,
                "NgayKham": ngay_kham,
                "CaKham": ca_kham_ten,
                "KhungGio": b.KhungGio,
                "LyDoKham": b.LyDoKham,
                "TrangThai": b.TrangThai,
                "NgayDat": b.NgayDat
            })
    return result

class UpdateStatusRequest(BaseModel):
    status: str

@router.put("/bookings/{ma_dat_lich}/status")
def update_booking_status(ma_dat_lich: str, req: UpdateStatusRequest, db: Session = Depends(get_db), staff: NhanVien = Depends(get_current_staff)):
    booking = db.query(DatLichKham).filter(DatLichKham.MaDatLich == ma_dat_lich).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã đặt lịch")
        
    booking.TrangThai = req.status
    db.commit()
    return {"message": f"Đã chuyển trạng thái thành {req.status}"}

class ReceptionRequest(BaseModel):
    MaDatLich: str

@router.post("/reception")
def create_reception(req: ReceptionRequest, staff: NhanVien = Depends(get_current_staff), db: Session = Depends(get_db)):
    booking = db.query(DatLichKham).filter(DatLichKham.MaDatLich == req.MaDatLich).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch")
        
    if booking.TrangThai != "Đã xác nhận":
        raise HTTPException(status_code=400, detail="Chỉ có thể tiếp nhận lịch đã xác nhận")
        
    import random
    new_ptn_id = f"PTN{random.randint(1000,9999)}"
    
    new_reception = PhieuTiepNhan(
        MaPhieuTiepNhan=new_ptn_id,
        MaDatLich=req.MaDatLich,
        MaNhanVien=staff.MaNhanVien,
        NgayTiepNhan=datetime.datetime.now(),
        SoThuTu=random.randint(1, 100),
        TrangThai="DaTiepNhan"
    )
    
    db.add(new_reception)
    db.commit()
    
    return {"message": "Tiếp nhận thành công", "SoThuTu": new_reception.SoThuTu}

# --- QUẢN LÝ YÊU CẦU HỖ TRỢ ---
@router.get("/support-requests")
def get_support_requests(db: Session = Depends(get_db), staff: NhanVien = Depends(get_current_staff)):
    reqs = db.query(YeuCauHoTro).order_by(desc(YeuCauHoTro.NgayGui)).all()
    result = []
    for r in reqs:
        bn = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == r.MaBenhNhan).first()
        # Find if there is a response
        ph = db.query(PhanHoiHoTro).filter(PhanHoiHoTro.MaYeuCau == r.MaYeuCau).first()
        result.append({
            "MaYeuCau": r.MaYeuCau,
            "TenBenhNhan": bn.HoTen if bn else "Không rõ",
            "SDT": bn.SDT if bn else "Không rõ",
            "NoiDung": r.NoiDung,
            "NgayGui": r.NgayGui,
            "TrangThai": r.TrangThai,
            "PhanHoi": ph.NoiDung if ph else None
        })
    return result

class ReplySupportReq(BaseModel):
    NoiDung: str

@router.post("/support-requests/{ma_yeu_cau}/reply")
def reply_support_request(ma_yeu_cau: str, req: ReplySupportReq, db: Session = Depends(get_db), staff: NhanVien = Depends(get_current_staff)):
    yc = db.query(YeuCauHoTro).filter(YeuCauHoTro.MaYeuCau == ma_yeu_cau).first()
    if not yc:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
        
    import random
    new_id = f"PH{random.randint(1000,9999)}"
    ph = PhanHoiHoTro(
        MaPhanHoi=new_id,
        MaYeuCau=ma_yeu_cau,
        MaNhanVien=staff.MaNhanVien,
        NoiDung=req.NoiDung,
        NgayPhanHoi=datetime.datetime.now()
    )
    db.add(ph)
    yc.TrangThai = "DaPhanHoi"
    db.commit()
    return {"message": "Đã phản hồi thành công"}
