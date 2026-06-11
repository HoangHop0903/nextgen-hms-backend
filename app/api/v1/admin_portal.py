from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import datetime
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.models.models import TaiKhoan, BenhNhan, BacSi, NhanVien, ChuyenKhoa, Thuoc, DatLichKham, PhongKham, CaKham, LichPhongKham, LichLamViec, BangGiaKham, HoaDon

router = APIRouter()

# Note: We skip auth dependency here to keep it simple, but in prod we would check if role == 'ADMIN'

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    current_year = datetime.datetime.now().year
    
    total_patients = db.query(BenhNhan).count()
    total_doctors = db.query(BacSi).count()
    total_staffs = db.query(NhanVien).count()
    total_bookings = db.query(DatLichKham).count()
    pending_bookings = db.query(DatLichKham).filter(DatLichKham.TrangThai == 'ChoDuyet').count()

    # 1. Monthly Data
    monthly_visits = db.query(
        extract('month', DatLichKham.NgayDat).label('month'),
        func.count(DatLichKham.MaDatLich).label('visits')
    ).filter(extract('year', DatLichKham.NgayDat) == current_year).group_by(extract('month', DatLichKham.NgayDat)).all()

    monthly_revenue = db.query(
        extract('month', HoaDon.NgayLap).label('month'),
        func.sum(HoaDon.TongTien).label('revenue')
    ).filter(extract('year', HoaDon.NgayLap) == current_year, HoaDon.TrangThai == 'Đã thanh toán').group_by(extract('month', HoaDon.NgayLap)).all()

    monthly_data = []
    current_month = datetime.datetime.now().month
    for m in range(1, 13):
        visits = next((v.visits for v in monthly_visits if v.month == m), 0)
        rev = next((float(r.revenue) for r in monthly_revenue if r.month == m), 0)
        if visits > 0 or rev > 0 or m <= current_month:
            monthly_data.append({
                "name": f"T{m}",
                "LượtKhám": visits,
                "DoanhThu": rev
            })

    # 2. Pie Chart (Specialties)
    specialties_data = db.query(
        ChuyenKhoa.TenChuyenKhoa,
        func.count(DatLichKham.MaDatLich).label('count')
    ).join(BangGiaKham, DatLichKham.MaBangGia == BangGiaKham.MaBangGia)\
     .join(ChuyenKhoa, BangGiaKham.MaChuyenKhoa == ChuyenKhoa.MaChuyenKhoa)\
     .group_by(ChuyenKhoa.TenChuyenKhoa).all()

    pie_data = [{"name": s.TenChuyenKhoa, "value": s.count} for s in specialties_data]

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_staffs": total_staffs,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "monthly_data": monthly_data,
        "pie_data": pie_data
    }

@router.get("/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accs = db.query(TaiKhoan).all()
    return [{"MaTaiKhoan": a.MaTaiKhoan, "TenDangNhap": a.TenDangNhap, "Email": a.Email, "VaiTro": a.VaiTro, "TrangThai": a.TrangThai} for a in accs]

class CreateAccountReq(BaseModel):
    TenDangNhap: str
    MatKhau: str
    Email: str
    VaiTro: str

@router.post("/accounts")
def create_account(req: CreateAccountReq, db: Session = Depends(get_db)):
    if db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == req.TenDangNhap).first():
        raise HTTPException(status_code=400, detail="Username already exists")
        
    import random
    new_id = f"TK{random.randint(10000, 99999)}"
    new_acc = TaiKhoan(
        MaTaiKhoan=new_id,
        TenDangNhap=req.TenDangNhap,
        MatKhau=req.MatKhau,
        Email=req.Email,
        VaiTro=req.VaiTro,
        TrangThai=True
    )
    db.add(new_acc)
    db.commit()
    return {"message": "Account created", "MaTaiKhoan": new_id}

class UpdateStatusReq(BaseModel):
    status: bool

class UpdateAccountReq(BaseModel):
    mat_khau: Optional[str] = None
    email: Optional[str] = None
    vai_tro: Optional[str] = None

@router.put("/accounts/{ma_tk}")
def update_account_info(ma_tk: str, req: UpdateAccountReq, db: Session = Depends(get_db)):
    acc = db.query(TaiKhoan).filter(TaiKhoan.MaTaiKhoan == ma_tk).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    
    if req.mat_khau:
        acc.MatKhau = req.mat_khau
    if req.email:
        # Check if email used
        existing = db.query(TaiKhoan).filter(TaiKhoan.Email == req.email, TaiKhoan.MaTaiKhoan != ma_tk).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        acc.Email = req.email
    if req.vai_tro:
        acc.VaiTro = req.vai_tro
        
    db.commit()
    return {"message": "Updated info"}

@router.put("/accounts/{ma_tk}/status")
def update_account_status(ma_tk: str, req: UpdateStatusReq, db: Session = Depends(get_db)):
    acc = db.query(TaiKhoan).filter(TaiKhoan.MaTaiKhoan == ma_tk).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    acc.TrangThai = req.status
    db.commit()
    return {"message": "Updated"}

# --- QUẢN LÝ CHUYÊN KHOA ---
@router.get("/specialties")
def get_specialties(db: Session = Depends(get_db)):
    return db.query(ChuyenKhoa).all()

class ChuyenKhoaReq(BaseModel):
    TenChuyenKhoa: str
    MoTa: Optional[str] = None

@router.post("/specialties")
def create_specialty(req: ChuyenKhoaReq, db: Session = Depends(get_db)):
    import random
    new_id = f"CK{random.randint(100,999)}"
    ck = ChuyenKhoa(MaChuyenKhoa=new_id, TenChuyenKhoa=req.TenChuyenKhoa, MoTa=req.MoTa, TrangThai=True)
    db.add(ck)
    db.commit()
    return {"message": "Created", "MaChuyenKhoa": new_id}

@router.put("/specialties/{ma_ck}/status")
def update_specialty_status(ma_ck: str, req: UpdateStatusReq, db: Session = Depends(get_db)):
    ck = db.query(ChuyenKhoa).filter(ChuyenKhoa.MaChuyenKhoa == ma_ck).first()
    if ck:
        ck.TrangThai = req.status
        db.commit()
    return {"message": "Updated"}

# --- QUẢN LÝ PHÒNG KHÁM ---
@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    return db.query(PhongKham).all()

class PhongKhamReq(BaseModel):
    MaChuyenKhoa: str
    TenPhong: str
    Tang: int
    Khu: str

@router.post("/rooms")
def create_room(req: PhongKhamReq, db: Session = Depends(get_db)):
    import random
    new_id = f"P{random.randint(100,999)}"
    p = PhongKham(MaPhong=new_id, MaChuyenKhoa=req.MaChuyenKhoa, TenPhong=req.TenPhong, Tang=req.Tang, Khu=req.Khu, TrangThai=True)
    db.add(p)
    db.commit()
    return {"message": "Created", "MaPhong": new_id}

@router.put("/rooms/{ma_p}/status")
def update_room_status(ma_p: str, req: UpdateStatusReq, db: Session = Depends(get_db)):
    p = db.query(PhongKham).filter(PhongKham.MaPhong == ma_p).first()
    if p:
        p.TrangThai = req.status
        db.commit()
    return {"message": "Updated"}

# --- QUẢN LÝ THUỐC ---
@router.get("/medicines")
def get_medicines_admin(db: Session = Depends(get_db)):
    return db.query(Thuoc).all()

class ThuocReq(BaseModel):
    TenThuoc: str
    DonViTinh: str
    GiaThuoc: float
    CachDung: str

@router.post("/medicines")
def create_medicine(req: ThuocReq, db: Session = Depends(get_db)):
    import random
    new_id = f"T{random.randint(1000,9999)}"
    t = Thuoc(MaThuoc=new_id, TenThuoc=req.TenThuoc, DonViTinh=req.DonViTinh, GiaThuoc=req.GiaThuoc, CachDung=req.CachDung, TrangThai=True)
    db.add(t)
    db.commit()
    return {"message": "Created"}

@router.put("/medicines/{ma_t}/status")
def update_medicine_status(ma_t: str, req: UpdateStatusReq, db: Session = Depends(get_db)):
    t = db.query(Thuoc).filter(Thuoc.MaThuoc == ma_t).first()
    if t:
        t.TrangThai = req.status
        db.commit()
    return {"message": "Updated"}

# --- QUẢN LÝ CA KHÁM ---
@router.get("/shifts")
def get_shifts(db: Session = Depends(get_db)):
    return db.query(CaKham).all()

# --- PHÂN CÔNG LỊCH LÀM VIỆC ---
class ScheduleReq(BaseModel):
    MaBacSi: str
    MaPhong: str
    MaCaKham: str
    NgayKham: str # YYYY-MM-DD
    SoLuongToiDa: int

@router.post("/schedule")
def create_doctor_schedule(req: ScheduleReq, db: Session = Depends(get_db)):
    import random
    import datetime
    
    # 1. Tạo Lịch Phòng Khám trước
    ma_lpk = f"LPK{random.randint(10000,99999)}"
    lpk = LichPhongKham(
        MaLichPhong=ma_lpk,
        MaPhong=req.MaPhong,
        MaCaKham=req.MaCaKham,
        NgayKham=datetime.datetime.strptime(req.NgayKham, "%Y-%m-%d").date(),
        SoLuongToiDa=req.SoLuongToiDa,
        SoLuongDaDat=0,
        TrangThai="HoatDong"
    )
    db.add(lpk)
    
    # 2. Phân công Bác sĩ vào Lịch Phòng Khám
    ma_llv = f"LLV{random.randint(10000,99999)}"
    llv = LichLamViec(
        MaLichLamViec=ma_llv,
        MaBacSi=req.MaBacSi,
        MaLichPhong=ma_lpk,
        TrangThai="HoatDong"
    )
    db.add(llv)
    db.commit()
    return {"message": "Đã phân công lịch làm việc thành công"}

# --- QUẢN LÝ BẢNG GIÁ KHÁM ---
@router.get("/prices")
def get_prices(db: Session = Depends(get_db)):
    return db.query(BangGiaKham).all()

class BangGiaReq(BaseModel):
    MaChuyenKhoa: str
    TenDichVu: str
    GiaKham: float

@router.post("/prices")
def create_price(req: BangGiaReq, db: Session = Depends(get_db)):
    import random
    new_id = f"BG{random.randint(100,999)}"
    bg = BangGiaKham(MaBangGia=new_id, MaChuyenKhoa=req.MaChuyenKhoa, TenDichVu=req.TenDichVu, GiaKham=req.GiaKham, TrangThai=True)
    db.add(bg)
    db.commit()
    return {"message": "Created", "MaBangGia": new_id}

@router.put("/prices/{ma_bg}/status")
def update_price_status(ma_bg: str, req: UpdateStatusReq, db: Session = Depends(get_db)):
    bg = db.query(BangGiaKham).filter(BangGiaKham.MaBangGia == ma_bg).first()
    if bg:
        bg.TrangThai = req.status
        db.commit()
    return {"message": "Updated"}



# --- FULL CRUD IMPLEMENTATION ADDED ---
from sqlalchemy.exc import IntegrityError

# 1. SPECIALTIES: PUT & DELETE
class ChuyenKhoaUpdateReq(BaseModel):
    TenChuyenKhoa: Optional[str] = None
    MoTa: Optional[str] = None

@router.put('/specialties/{ma_ck}')
def update_specialty(ma_ck: str, req: ChuyenKhoaUpdateReq, db: Session = Depends(get_db)):
    ck = db.query(ChuyenKhoa).filter(ChuyenKhoa.MaChuyenKhoa == ma_ck).first()
    if not ck: raise HTTPException(404, 'Not found')
    if req.TenChuyenKhoa: ck.TenChuyenKhoa = req.TenChuyenKhoa
    if req.MoTa: ck.MoTa = req.MoTa
    db.commit()
    return {'message': 'Updated'}

@router.delete('/specialties/{ma_ck}')
def delete_specialty(ma_ck: str, db: Session = Depends(get_db)):
    ck = db.query(ChuyenKhoa).filter(ChuyenKhoa.MaChuyenKhoa == ma_ck).first()
    if not ck: raise HTTPException(404, 'Not found')
    try:
        db.delete(ck)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá chuyên khoa vì đang có bác sĩ hoặc phòng khám thuộc chuyên khoa này. Hãy đổi trạng thái sang Tạm ngưng.')

# 2. ROOMS: PUT & DELETE
class PhongKhamUpdateReq(BaseModel):
    TenPhong: Optional[str] = None
    Tang: Optional[int] = None
    Khu: Optional[str] = None

@router.put('/rooms/{ma_p}')
def update_room(ma_p: str, req: PhongKhamUpdateReq, db: Session = Depends(get_db)):
    p = db.query(PhongKham).filter(PhongKham.MaPhong == ma_p).first()
    if not p: raise HTTPException(404, 'Not found')
    if req.TenPhong: p.TenPhong = req.TenPhong
    if req.Tang: p.Tang = req.Tang
    if req.Khu: p.Khu = req.Khu
    db.commit()
    return {'message': 'Updated'}

@router.delete('/rooms/{ma_p}')
def delete_room(ma_p: str, db: Session = Depends(get_db)):
    p = db.query(PhongKham).filter(PhongKham.MaPhong == ma_p).first()
    if not p: raise HTTPException(404, 'Not found')
    try:
        db.delete(p)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá phòng khám vì đã có lịch phân công hoặc lịch sử. Hãy đổi trạng thái.')

# 3. MEDICINES: PUT & DELETE
class ThuocUpdateReq(BaseModel):
    TenThuoc: Optional[str] = None
    DonViTinh: Optional[str] = None
    GiaThuoc: Optional[float] = None
    CachDung: Optional[str] = None

@router.put('/medicines/{ma_t}')
def update_medicine(ma_t: str, req: ThuocUpdateReq, db: Session = Depends(get_db)):
    t = db.query(Thuoc).filter(Thuoc.MaThuoc == ma_t).first()
    if not t: raise HTTPException(404, 'Not found')
    if req.TenThuoc: t.TenThuoc = req.TenThuoc
    if req.DonViTinh: t.DonViTinh = req.DonViTinh
    if req.GiaThuoc: t.GiaThuoc = req.GiaThuoc
    if req.CachDung: t.CachDung = req.CachDung
    db.commit()
    return {'message': 'Updated'}

@router.delete('/medicines/{ma_t}')
def delete_medicine(ma_t: str, db: Session = Depends(get_db)):
    t = db.query(Thuoc).filter(Thuoc.MaThuoc == ma_t).first()
    if not t: raise HTTPException(404, 'Not found')
    try:
        db.delete(t)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá thuốc vì đã được kê trong đơn thuốc. Hãy đổi trạng thái.')

# 4. PRICES: PUT & DELETE
class BangGiaUpdateReq(BaseModel):
    TenDichVu: Optional[str] = None
    GiaKham: Optional[float] = None

@router.put('/prices/{ma_bg}')
def update_price(ma_bg: str, req: BangGiaUpdateReq, db: Session = Depends(get_db)):
    bg = db.query(BangGiaKham).filter(BangGiaKham.MaBangGia == ma_bg).first()
    if not bg: raise HTTPException(404, 'Not found')
    if req.TenDichVu: bg.TenDichVu = req.TenDichVu
    if req.GiaKham: bg.GiaKham = req.GiaKham
    db.commit()
    return {'message': 'Updated'}

@router.delete('/prices/{ma_bg}')
def delete_price(ma_bg: str, db: Session = Depends(get_db)):
    bg = db.query(BangGiaKham).filter(BangGiaKham.MaBangGia == ma_bg).first()
    if not bg: raise HTTPException(404, 'Not found')
    try:
        db.delete(bg)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá dịch vụ/bảng giá vì đã có dữ liệu đặt khám. Hãy đổi trạng thái.')

# 5. SHIFTS: CRUD
class CaKhamReq(BaseModel):
    TenCa: str
    GioBatDau: str
    GioKetThuc: str

@router.post('/shifts')
def create_shift(req: CaKhamReq, db: Session = Depends(get_db)):
    import random
    new_id = f'C{random.randint(100,999)}'
    ck = CaKham(MaCaKham=new_id, TenCa=req.TenCa, GioBatDau=req.GioBatDau, GioKetThuc=req.GioKetThuc, TrangThai=True)
    db.add(ck)
    db.commit()
    return {'message': 'Created'}

@router.put('/shifts/{ma_ck}')
def update_shift(ma_ck: str, req: CaKhamReq, db: Session = Depends(get_db)):
    ck = db.query(CaKham).filter(CaKham.MaCaKham == ma_ck).first()
    if not ck: raise HTTPException(404, 'Not found')
    ck.TenCa = req.TenCa
    ck.GioBatDau = req.GioBatDau
    ck.GioKetThuc = req.GioKetThuc
    db.commit()
    return {'message': 'Updated'}

@router.delete('/shifts/{ma_ck}')
def delete_shift(ma_ck: str, db: Session = Depends(get_db)):
    ck = db.query(CaKham).filter(CaKham.MaCaKham == ma_ck).first()
    if not ck: raise HTTPException(404, 'Not found')
    try:
        db.delete(ck)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá ca khám vì đã có lịch phòng khám sử dụng. Hãy đổi trạng thái.')

# 6. PERSONNEL (DOCTORS & STAFFS): FULL CRUD
@router.get('/doctors')
def get_doctors_admin(db: Session = Depends(get_db)):
    return db.query(BacSi).all()

class BacSiReq(BaseModel):
    MaTaiKhoan: str
    MaChuyenKhoa: str
    HoTen: str
    HocVi: str
    SDT: str

@router.post('/doctors')
def create_doctor(req: BacSiReq, db: Session = Depends(get_db)):
    if db.query(BacSi).filter(BacSi.MaTaiKhoan == req.MaTaiKhoan).first() or db.query(NhanVien).filter(NhanVien.MaTaiKhoan == req.MaTaiKhoan).first():
        raise HTTPException(status_code=400, detail="Tài khoản này đã được gán cho một nhân sự khác!")
    import random
    new_id = f'BS{random.randint(1000,9999)}'
    bs = BacSi(MaBacSi=new_id, MaTaiKhoan=req.MaTaiKhoan, MaChuyenKhoa=req.MaChuyenKhoa, HoTen=req.HoTen, HocVi=req.HocVi, SDT=req.SDT, TrangThai=True)
    db.add(bs)
    db.commit()
    return {'message': 'Created'}

@router.put('/doctors/{ma_bs}')
def update_doctor(ma_bs: str, req: BacSiReq, db: Session = Depends(get_db)):
    bs = db.query(BacSi).filter(BacSi.MaBacSi == ma_bs).first()
    if not bs: raise HTTPException(404, 'Not found')
    if req.MaTaiKhoan != bs.MaTaiKhoan and (db.query(BacSi).filter(BacSi.MaTaiKhoan == req.MaTaiKhoan).first() or db.query(NhanVien).filter(NhanVien.MaTaiKhoan == req.MaTaiKhoan).first()):
        raise HTTPException(status_code=400, detail="Tài khoản này đã được gán cho một nhân sự khác!")
    bs.MaTaiKhoan = req.MaTaiKhoan
    bs.MaChuyenKhoa = req.MaChuyenKhoa
    bs.HoTen = req.HoTen
    bs.HocVi = req.HocVi
    bs.SDT = req.SDT
    db.commit()
    return {'message': 'Updated'}

@router.delete('/doctors/{ma_bs}')
def delete_doctor(ma_bs: str, db: Session = Depends(get_db)):
    bs = db.query(BacSi).filter(BacSi.MaBacSi == ma_bs).first()
    if not bs: raise HTTPException(404, 'Not found')
    try:
        db.delete(bs)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá bác sĩ này vì đã có lịch khám/hồ sơ bệnh án. Vui lòng tắt trạng thái hoạt động.')

@router.get('/staffs')
def get_staffs_admin(db: Session = Depends(get_db)):
    return db.query(NhanVien).all()

class NhanVienReq(BaseModel):
    MaTaiKhoan: str
    HoTen: str
    ChucVu: str
    SDT: str

@router.post('/staffs')
def create_staff(req: NhanVienReq, db: Session = Depends(get_db)):
    if db.query(BacSi).filter(BacSi.MaTaiKhoan == req.MaTaiKhoan).first() or db.query(NhanVien).filter(NhanVien.MaTaiKhoan == req.MaTaiKhoan).first():
        raise HTTPException(status_code=400, detail="Tài khoản này đã được gán cho một nhân sự khác!")
    import random
    new_id = f'NV{random.randint(1000,9999)}'
    nv = NhanVien(MaNhanVien=new_id, MaTaiKhoan=req.MaTaiKhoan, HoTen=req.HoTen, ChucVu=req.ChucVu, SDT=req.SDT, TrangThai=True)
    db.add(nv)
    db.commit()
    return {'message': 'Created'}

@router.put('/staffs/{ma_nv}')
def update_staff(ma_nv: str, req: NhanVienReq, db: Session = Depends(get_db)):
    nv = db.query(NhanVien).filter(NhanVien.MaNhanVien == ma_nv).first()
    if not nv: raise HTTPException(404, 'Not found')
    if req.MaTaiKhoan != nv.MaTaiKhoan and (db.query(BacSi).filter(BacSi.MaTaiKhoan == req.MaTaiKhoan).first() or db.query(NhanVien).filter(NhanVien.MaTaiKhoan == req.MaTaiKhoan).first()):
        raise HTTPException(status_code=400, detail="Tài khoản này đã được gán cho một nhân sự khác!")
    nv.MaTaiKhoan = req.MaTaiKhoan
    nv.HoTen = req.HoTen
    nv.ChucVu = req.ChucVu
    nv.SDT = req.SDT
    db.commit()
    return {'message': 'Updated'}

@router.delete('/staffs/{ma_nv}')
def delete_staff(ma_nv: str, db: Session = Depends(get_db)):
    nv = db.query(NhanVien).filter(NhanVien.MaNhanVien == ma_nv).first()
    if not nv: raise HTTPException(404, 'Not found')
    try:
        db.delete(nv)
        db.commit()
        return {'message': 'Deleted'}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'Không thể xoá nhân viên này vì liên kết khoá ngoại.')

# 7. PATIENTS & BOOKINGS: FULL CRUD
@router.get('/patients')
def get_patients_admin(db: Session = Depends(get_db)):
    return db.query(BenhNhan).all()

@router.delete('/patients/{ma_bn}')
def delete_patient(ma_bn: str, db: Session = Depends(get_db)):
    try:
        pat = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == ma_bn).first()
        if not pat:
            raise HTTPException(status_code=404, detail="Không tìm thấy bệnh nhân")
        db.delete(pat)
        db.commit()
        return {"msg": "Đã xóa bệnh nhân"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Không thể xóa bệnh nhân vì đang có dữ liệu liên kết (Lịch khám/Hồ sơ).")

class PatientUpdate(BaseModel):
    HoTen: str
    NgaySinh: date
    GioiTinh: str
    DienThoai: str

@router.put('/patients/{ma_bn}')
def update_patient(ma_bn: str, pat: PatientUpdate, db: Session = Depends(get_db)):
    db_pat = db.query(BenhNhan).filter(BenhNhan.MaBenhNhan == ma_bn).first()
    if not db_pat:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh nhân")
    db_pat.HoTen = pat.HoTen
    db_pat.NgaySinh = pat.NgaySinh
    db_pat.GioiTinh = pat.GioiTinh
    db_pat.DienThoai = pat.DienThoai
    db.commit()
    return {"msg": "Sửa bệnh nhân thành công"}

@router.get('/bookings')
def get_bookings_admin(db: Session = Depends(get_db)):
    bookings = db.query(DatLichKham).order_by(DatLichKham.NgayDat.desc()).all()
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
                
        result.append({
            "MaDatLich": b.MaDatLich,
            "MaBenhNhan": b.MaBenhNhan,
            "TenBenhNhan": bn.HoTen if bn else "Không rõ",
            "BacSi": bs_name,
            "NgayKham": ngay_kham,
            "CaKham": ca_kham_ten,
            "KhungGio": b.KhungGio,
            "LyDoKham": b.LyDoKham,
            "TrangThai": b.TrangThai,
            "NgayDat": b.NgayDat
        })
    return result

@router.delete('/bookings/{ma_dl}')
def delete_booking(ma_dl: str, db: Session = Depends(get_db)):
    try:
        book = db.query(DatLichKham).filter(DatLichKham.MaDatLich == ma_dl).first()
        if not book:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch khám")
        db.delete(book)
        db.commit()
        return {"msg": "Đã xóa lịch khám"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Không thể xóa lịch khám này do có dữ liệu liên kết.")

class BookingUpdate(BaseModel):
    TrangThai: str

@router.put('/bookings/{ma_dl}')
def update_booking(ma_dl: str, book: BookingUpdate, db: Session = Depends(get_db)):
    db_book = db.query(DatLichKham).filter(DatLichKham.MaDatLich == ma_dl).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch khám")
    db_book.TrangThai = book.TrangThai
    db.commit()
    return {"msg": "Cập nhật trạng thái thành công"}
