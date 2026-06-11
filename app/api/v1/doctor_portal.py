from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import datetime
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db
from app.models.models import (
    BacSi, DatLichKham, BenhNhan, LichLamViec, LichPhongKham, CaKham,
    Thuoc, PhieuKham, DonThuoc, ChiTietDonThuoc, PhongKham, BangGiaKham, HoaDon
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_doctor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token.startswith("dummy_token_for_"):
        ma_tk = token.replace("dummy_token_for_", "")
        bs = db.query(BacSi).filter(BacSi.MaTaiKhoan == ma_tk).first()
        if not bs:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ bác sĩ")
        return bs
    raise HTTPException(status_code=401, detail="Xác thực thất bại")

@router.get("/me")
def get_my_info(doctor: BacSi = Depends(get_current_doctor)):
    return {
        "MaBacSi": doctor.MaBacSi,
        "HoTen": doctor.HoTen,
        "HocVi": doctor.HocVi,
        "SDT": doctor.SDT,
        "AnhDaiDien": doctor.AnhDaiDien
    }

@router.get("/schedule")
def get_schedule(doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    # Lấy lịch khám của bác sĩ này
    llv_list = db.query(LichLamViec).filter(LichLamViec.MaBacSi == doctor.MaBacSi).all()
    ma_llv_list = [llv.MaLichLamViec for llv in llv_list]
    
    # Lấy bệnh nhân đã tiếp nhận (hoặc đã duyệt) thuộc lịch này
    bookings = db.query(DatLichKham).filter(
        DatLichKham.MaLichLamViec.in_(ma_llv_list),
        DatLichKham.TrangThai.in_(["Đã xác nhận", "Hoàn thành"])
    ).order_by(DatLichKham.NgayDat).all()
    
    result = []
    for b in bookings:
        bn = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == b.MaBenhNhan).first()
        llv = next((l for l in llv_list if l.MaLichLamViec == b.MaLichLamViec), None)
        lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first() if llv else None
        
        # Chỉ lấy lịch hôm nay (hoặc gần đây) để dễ test, ở đây sẽ không lọc chặt để có data hiển thị
        if lpk:
            ca = db.query(CaKham).filter(CaKham.MaCaKham == lpk.MaCaKham).first()
            result.append({
                "MaDatLich": b.MaDatLich,
                "MaBenhNhan": b.MaBenhNhan,
                "TenBenhNhan": bn.HoTen if bn else "Không rõ",
                "GioiTinh": bn.GioiTinh if bn else "",
                "NgayKham": lpk.NgayKham,
                "CaKham": ca.TenCa if ca else "",
                "KhungGio": b.KhungGio,
                "LyDoKham": b.LyDoKham,
                "TrangThai": b.TrangThai
            })
    return result

@router.get("/medicines")
def get_medicines(doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    thuocs = db.query(Thuoc).filter(Thuoc.TrangThai == True).all()
    return [{"MaThuoc": t.MaThuoc, "TenThuoc": t.TenThuoc, "DonViTinh": t.DonViTinh} for t in thuocs]

class CreateMedicineReq(BaseModel):
    TenThuoc: str
    DonViTinh: str
    GiaThuoc: float = 0
    CachDung: str = ""

@router.post("/medicines")
def create_medicine(req: CreateMedicineReq, doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    import random
    new_id = f"TH{random.randint(1000,9999)}"
    new_t = Thuoc(
        MaThuoc=new_id,
        TenThuoc=req.TenThuoc,
        DonViTinh=req.DonViTinh,
        GiaThuoc=req.GiaThuoc,
        CachDung=req.CachDung,
        TrangThai=True
    )
    db.add(new_t)
    db.commit()
    return {"message": "Thêm thuốc thành công", "Thuoc": {"MaThuoc": new_id, "TenThuoc": req.TenThuoc, "DonViTinh": req.DonViTinh}}

class ConsultationRequest(BaseModel):
    MaDatLich: str
    TrieuChung: str
    ChanDoan: str
    KetLuan: str

@router.post("/consultation")
def create_consultation(req: ConsultationRequest, doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    booking = db.query(DatLichKham).filter(DatLichKham.MaDatLich == req.MaDatLich).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Lịch khám không tồn tại")
        
    llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == booking.MaLichLamViec).first()
    lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first() if llv else None
    
    import random
    new_pk_id = f"PK{random.randint(10000,99999)}"
    
    new_pk = PhieuKham(
        MaPhieuKham=new_pk_id,
        MaBenhNhan=booking.MaBenhNhan,
        MaBacSi=doctor.MaBacSi,
        MaPhong=lpk.MaPhong if lpk else None,
        NgayKham=datetime.datetime.now(),
        TrieuChung=req.TrieuChung,
        ChanDoan=req.ChanDoan,
        KetLuan=req.KetLuan,
        GhiChu="Được tạo từ Doctor Portal"
    )
    
    # Đổi trạng thái lịch thành HoanThanh
    booking.TrangThai = "HoanThanh"
    db.add(new_pk)
    db.commit()
    
    return {"message": "Lưu phiếu khám thành công", "MaPhieuKham": new_pk_id}

class PrescriptionDetailReq(BaseModel):
    MaThuoc: str
    SoLuong: int
    LieuDung: str
    SoNgayDung: int

class PrescriptionRequest(BaseModel):
    MaPhieuKham: str
    GhiChu: Optional[str] = None
    ChiTiet: List[PrescriptionDetailReq]

@router.post("/prescription")
def create_prescription(req: PrescriptionRequest, doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    pk = db.query(PhieuKham).filter(PhieuKham.MaPhieuKham == req.MaPhieuKham).first()
    if not pk or pk.MaBacSi != doctor.MaBacSi:
        raise HTTPException(status_code=403, detail="Phiếu khám không hợp lệ hoặc không thuộc về bác sĩ này")
        
    import random
    new_dt_id = f"DT{random.randint(1000,9999)}"
    
    new_dt = DonThuoc(
        MaDonThuoc=new_dt_id,
        MaPhieuKham=req.MaPhieuKham,
        NgayKe=datetime.datetime.now(),
        GhiChu=req.GhiChu
    )
    db.add(new_dt)
    
    
    tong_tien_thuoc = 0
    for idx, ct in enumerate(req.ChiTiet):
        ctdt = ChiTietDonThuoc(
            MaCTDT=f"{new_dt_id}_{idx}",
            MaDonThuoc=new_dt_id,
            MaThuoc=ct.MaThuoc,
            SoLuong=ct.SoLuong,
            LieuDung=ct.LieuDung,
            SoNgayDung=ct.SoNgayDung
        )
        db.add(ctdt)
        # Tính tiền thuốc
        th = db.query(Thuoc).filter(Thuoc.MaThuoc == ct.MaThuoc).first()
        if th and th.GiaThuoc:
            tong_tien_thuoc += float(th.GiaThuoc) * ct.SoLuong
            
    # Tạo Hoá Đơn
    from sqlalchemy import desc
    llvs = db.query(LichLamViec).filter(LichLamViec.MaBacSi == doctor.MaBacSi).all()
    llv_ids = [l.MaLichLamViec for l in llvs]
    booking = db.query(DatLichKham).filter(
        DatLichKham.MaBenhNhan == pk.MaBenhNhan,
        DatLichKham.MaLichLamViec.in_(llv_ids)
    ).order_by(desc(DatLichKham.NgayDat)).first()
    
    tien_kham = 0
    if booking and booking.MaBangGia:
        bg = db.query(BangGiaKham).filter(BangGiaKham.MaBangGia == booking.MaBangGia).first()
        if bg and bg.GiaKham:
            tien_kham = float(bg.GiaKham)
            
    hd_id = f"HD{random.randint(10000,99999)}"
    new_hd = HoaDon(
        MaHoaDon=hd_id,
        MaBenhNhan=pk.MaBenhNhan,
        MaDatLich=booking.MaDatLich if booking else None,
        TongTien=tien_kham + tong_tien_thuoc,
        NgayLap=datetime.datetime.now(),
        TrangThai="Chưa thanh toán",
        PhuongThucThanhToan=""
    )
    db.add(new_hd)
        
    db.commit()
    return {"message": "Kê đơn thuốc thành công", "MaDonThuoc": new_dt_id}

@router.get("/patient/{ma_benh_nhan}")
def get_patient_details(ma_benh_nhan: str, doctor: BacSi = Depends(get_current_doctor), db: Session = Depends(get_db)):
    bn = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == ma_benh_nhan).first()
    if not bn:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh nhân")
        
    from app.models.models import HoSoBenhAn
    hsba = db.query(HoSoBenhAn).filter(HoSoBenhAn.MaBenhNhan == ma_benh_nhan).first()
    
    # Lấy lịch sử phiếu khám
    phieu_khams = db.query(PhieuKham).filter(PhieuKham.MaBenhNhan == ma_benh_nhan).order_by(desc(PhieuKham.NgayKham)).all()
    history = []
    for pk in phieu_khams:
        bs_kham = db.query(BacSi).filter(BacSi.MaBacSi == pk.MaBacSi).first()
        don_thuoc = db.query(DonThuoc).filter(DonThuoc.MaPhieuKham == pk.MaPhieuKham).first()
        thuoc_list = []
        if don_thuoc:
            chi_tiet = db.query(ChiTietDonThuoc).filter(ChiTietDonThuoc.MaDonThuoc == don_thuoc.MaDonThuoc).all()
            for ct in chi_tiet:
                t = db.query(Thuoc).filter(Thuoc.MaThuoc == ct.MaThuoc).first()
                if t:
                    thuoc_list.append({
                        "TenThuoc": t.TenThuoc,
                        "SoLuong": ct.SoLuong,
                        "LieuDung": ct.LieuDung,
                        "SoNgayDung": ct.SoNgayDung
                    })
        
        history.append({
            "MaPhieuKham": pk.MaPhieuKham,
            "NgayKham": pk.NgayKham,
            "BacSiKham": bs_kham.HoTen if bs_kham else "Không rõ",
            "TrieuChung": pk.TrieuChung,
            "ChanDoan": pk.ChanDoan,
            "KetLuan": pk.KetLuan,
            "DonThuoc": thuoc_list
        })
        
    return {
        "BenhNhan": {
            "MaBenhNhan": bn.MaBenhNhan,
            "HoTen": bn.HoTen,
            "NgaySinh": bn.NgaySinh.isoformat() if bn.NgaySinh else None,
            "GioiTinh": bn.GioiTinh,
            "SDT": bn.SDT,
            "DiaChi": bn.DiaChi,
            "SoBHYT": bn.SoBHYT,
            "TienSuDiUng": bn.TienSuDiUng,
            "AnhDaiDien": bn.AnhDaiDien
        },
        "HoSoBenhAn": {
            "TienSuBenh": hsba.TienSuBenh if hsba else "",
            "KetQuaGanNhat": hsba.KetQuaGanNhat if hsba else "",
            "GhiChu": hsba.GhiChu if hsba else ""
        },
        "LichSuKham": history
    }

