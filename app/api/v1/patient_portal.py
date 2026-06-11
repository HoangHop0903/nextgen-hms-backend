from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional
import datetime
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db
from app.models.models import (
    TaiKhoan, BenhNhan, BacSi, ChuyenKhoa, LichLamViec, LichPhongKham, CaKham, 
    DatLichKham, BangGiaKham, HoSoBenhAn, PhieuKham, DonThuoc, ChiTietDonThuoc, Thuoc, HoaDon
)
from app.utils.vnpay import vnpay

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token.startswith("dummy_token_for_"):
        ma_tk = token.replace("dummy_token_for_", "")
        benh_nhan = db.query(BenhNhan).filter(BenhNhan.MaTaiKhoan == ma_tk).first()
        if not benh_nhan:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ bệnh nhân cho tài khoản này")
        return benh_nhan
    raise HTTPException(status_code=401, detail="Xác thực thất bại")

@router.get("/me")
def get_my_info(patient: BenhNhan = Depends(get_current_patient)):
    return {
        "MaBenhNhan": patient.MaBenhNhan,
        "HoTen": patient.HoTen,
        "NgaySinh": patient.NgaySinh,
        "GioiTinh": patient.GioiTinh,
        "SDT": patient.SDT,
        "AnhDaiDien": patient.AnhDaiDien
    }

@router.get("/services")
def get_services(db: Session = Depends(get_db)):
    prices = db.query(BangGiaKham).filter(BangGiaKham.TrangThai == True).all()
    result = []
    for p in prices:
        ck = db.query(ChuyenKhoa).filter(ChuyenKhoa.MaChuyenKhoa == p.MaChuyenKhoa).first()
        result.append({
            "MaBangGia": p.MaBangGia,
            "TenDichVu": p.TenDichVu,
            "GiaKham": p.GiaKham,
            "TenChuyenKhoa": ck.TenChuyenKhoa if ck else "Dịch vụ chung"
        })
    return result

@router.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    # Optimize query using join instead of looping and querying for each doctor (Fix N+1 query issue)
    doctors = db.query(BacSi, ChuyenKhoa.TenChuyenKhoa).outerjoin(
        ChuyenKhoa, BacSi.MaChuyenKhoa == ChuyenKhoa.MaChuyenKhoa
    ).filter(BacSi.TrangThai == True).all()
    
    result = []
    for bs, ten_chuyen_khoa in doctors:
        result.append({
            "MaBacSi": bs.MaBacSi,
            "HoTen": bs.HoTen,
            "HocVi": bs.HocVi,
            "TenChuyenKhoa": ten_chuyen_khoa if ten_chuyen_khoa else "Chưa phân khoa",
            "AnhDaiDien": bs.AnhDaiDien
        })
    return result

def _generate_time_slots(start_time, end_time, interval_minutes=30):
    """Sinh danh sách khung giờ từ giờ bắt đầu đến giờ kết thúc."""
    slots = []
    current = datetime.datetime.combine(datetime.date.today(), start_time)
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    delta = datetime.timedelta(minutes=interval_minutes)
    while current + delta <= end:
        slots.append(current.strftime("%H:%M"))
        current += delta
    return slots

@router.get("/doctors/{ma_bac_si}/schedule")
def get_doctor_schedule(ma_bac_si: str, db: Session = Depends(get_db)):
    ma_bac_si = ma_bac_si.strip()
    
    lich_lam_viec_all = db.query(LichLamViec).all()
    lich_lam_viec = [l for l in lich_lam_viec_all if l.MaBacSi and l.TrangThai and l.MaBacSi.strip() == ma_bac_si and l.TrangThai.strip() in ["HoatDong", "Đã xác nhận"]]
    
    schedules = []
    for llv in lich_lam_viec:
        lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first()
        if lpk and lpk.NgayKham and lpk.NgayKham >= datetime.date.today():
            ca = db.query(CaKham).filter(CaKham.MaCaKham == lpk.MaCaKham).first()
            if not ca or not ca.GioBatDau or not ca.GioKetThuc:
                continue
            
            # Sinh khung giờ 30 phút
            time_slots = _generate_time_slots(ca.GioBatDau, ca.GioKetThuc)
            
            # Lấy các khung giờ đã bị đặt (trạng thái không phải DaHuy)
            booked = db.query(DatLichKham.KhungGio).filter(
                DatLichKham.MaLichLamViec == llv.MaLichLamViec,
                DatLichKham.KhungGio.isnot(None),
                DatLichKham.TrangThai != "Đã hủy"
            ).all()
            booked_slots = {b.KhungGio.strip() for b in booked if b.KhungGio}
            
            # Nếu là ngày hôm nay, lọc bỏ khung giờ đã qua
            now_str = ""
            if lpk.NgayKham == datetime.date.today():
                now_str = datetime.datetime.now().strftime("%H:%M")
            
            slot_list = []
            for slot in time_slots:
                if now_str and slot <= now_str:
                    continue  # Bỏ qua khung giờ đã qua
                slot_list.append({
                    "time": slot,
                    "booked": slot in booked_slots
                })
            
            if slot_list:  # Chỉ thêm nếu còn slot
                schedules.append({
                    "MaLichLamViec": llv.MaLichLamViec,
                    "NgayKham": lpk.NgayKham,
                    "TenCa": ca.TenCa if ca else "",
                    "GioBatDau": str(ca.GioBatDau),
                    "GioKetThuc": str(ca.GioKetThuc),
                    "slots": slot_list
                })
    
    # Sắp xếp theo ngày
    schedules.sort(key=lambda x: str(x["NgayKham"]))
    return schedules

from pydantic import BaseModel
class BookRequest(BaseModel):
    MaLichLamViec: str
    KhungGio: str  # VD: "09:00"
    LyDoKham: str

@router.post("/book")
def book_appointment(req: BookRequest, patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == req.MaLichLamViec).first()
    if not llv:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch làm việc")
    
    # Kiểm tra khung giờ đã bị đặt chưa (chống trùng)
    existing = db.query(DatLichKham).filter(
        DatLichKham.MaLichLamViec == req.MaLichLamViec,
        DatLichKham.KhungGio == req.KhungGio,
        DatLichKham.TrangThai != "Đã hủy"
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Khung giờ này đã có người đặt. Vui lòng chọn khung giờ khác.")
    
    bs = db.query(BacSi).filter(BacSi.MaBacSi == llv.MaBacSi).first()
    bang_gia = db.query(BangGiaKham).filter(BangGiaKham.MaChuyenKhoa == bs.MaChuyenKhoa).first()
    
    import random
    new_id = f"DL{random.randint(10000, 99999)}"
    
    new_booking = DatLichKham(
        MaDatLich=new_id,
        MaBenhNhan=patient.MaBenhNhan,
        MaLichLamViec=req.MaLichLamViec,
        MaBangGia=bang_gia.MaBangGia if bang_gia else None,
        NgayDat=datetime.datetime.now(),
        KhungGio=req.KhungGio,
        LyDoKham=req.LyDoKham,
        TrangThai="Chờ xác nhận",
        LoaiDat="Online"
    )
    db.add(new_booking)
    
    lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first()
    if lpk:
        lpk.SoLuongDaDat = (lpk.SoLuongDaDat or 0) + 1
        
    db.commit()
    return {"message": "Đặt lịch thành công", "MaDatLich": new_id, "KhungGio": req.KhungGio}

class GuestBookingRequest(BaseModel):
    # Patient Info
    HoTen: str
    NgaySinh: datetime.date
    GioiTinh: str
    SDT: str
    CCCD: Optional[str] = None
    DiaChi: Optional[str] = None
    # Booking Info
    MaLichLamViec: str
    KhungGio: str  # VD: "09:00"
    LyDoKham: str
    PhuongThucThanhToan: Optional[str] = "Tiền mặt"

@router.post("/guest-booking")
def guest_booking(req: GuestBookingRequest, db: Session = Depends(get_db)):
    llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == req.MaLichLamViec).first()
    if not llv:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch làm việc")
    
    # Kiểm tra khung giờ đã bị đặt chưa (chống trùng)
    existing = db.query(DatLichKham).filter(
        DatLichKham.MaLichLamViec == req.MaLichLamViec,
        DatLichKham.KhungGio == req.KhungGio,
        DatLichKham.TrangThai != "Đã hủy"
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Khung giờ này đã có người đặt. Vui lòng chọn khung giờ khác.")
    
    bs = db.query(BacSi).filter(BacSi.MaBacSi == llv.MaBacSi).first()
    bang_gia = db.query(BangGiaKham).filter(BangGiaKham.MaChuyenKhoa == bs.MaChuyenKhoa).first()
    
    if not bang_gia or not bang_gia.GiaKham:
        raise HTTPException(status_code=400, detail="Bác sĩ này chưa có bảng giá khám bệnh, không thể thanh toán")

    import random
    
    existing_acc = db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == req.SDT).first()
    ma_tk = None
    ma_bn = None
    is_new_account = False
    
    if existing_acc:
        existing_bn = db.query(BenhNhan).filter(BenhNhan.MaTaiKhoan == existing_acc.MaTaiKhoan).first()
        if existing_bn:
            ma_bn = existing_bn.MaBenhNhan
            ma_tk = existing_acc.MaTaiKhoan
    
    if not ma_bn:
        is_new_account = True
        ma_tk = f"TK{random.randint(1000, 99999)}"
        ma_bn = f"BN{random.randint(1000, 99999)}"
        
        new_acc = TaiKhoan(
            MaTaiKhoan=ma_tk,
            TenDangNhap=req.SDT,
            MatKhau="123456",
            VaiTro="BENHNHAN",
            TrangThai=True
        )
        db.add(new_acc)
        
        new_patient = BenhNhan(
            MaBenhNhan=ma_bn,
            MaTaiKhoan=ma_tk,
            HoTen=req.HoTen,
            NgaySinh=req.NgaySinh,
            GioiTinh=req.GioiTinh,
            SDT=req.SDT,
            CCCD=req.CCCD,
            DiaChi=req.DiaChi,
            TrangThai=True
        )
        db.add(new_patient)
    
    new_dl_id = f"DL{random.randint(10000, 99999)}"
    new_booking = DatLichKham(
        MaDatLich=new_dl_id,
        MaBenhNhan=ma_bn,
        MaLichLamViec=req.MaLichLamViec,
        MaBangGia=bang_gia.MaBangGia,
        NgayDat=datetime.datetime.now(),
        KhungGio=req.KhungGio,
        LyDoKham=req.LyDoKham,
        TrangThai="Chờ xác nhận",
        LoaiDat="Online"
    )
    db.add(new_booking)
    
    # Increment booking count
    lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == llv.MaLichPhong).first()
    if lpk:
        lpk.SoLuongDaDat = (lpk.SoLuongDaDat or 0) + 1
        
    # 4. Create HoaDon
    hd_id = f"HD{random.randint(10000, 99999)}"
    new_hd = HoaDon(
        MaHoaDon=hd_id,
        MaBenhNhan=ma_bn,
        MaDatLich=new_dl_id,
        TongTien=bang_gia.GiaKham,
        NgayLap=datetime.datetime.now(),
        TrangThai="Chưa thanh toán",
        PhuongThucThanhToan=req.PhuongThucThanhToan
    )
    db.add(new_hd)
    
    vnpay_payment_url = ""
    
    if req.PhuongThucThanhToan == "VNPay":
        # 5. Create VNPay URL
        vnp = vnpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = VNPAY_TMN_CODE
        vnp.requestData['vnp_Amount'] = str(int(float(new_hd.TongTien) * 100))
        vnp.requestData['vnp_CurrCode'] = 'VND'
        vnp.requestData['vnp_TxnRef'] = hd_id
        vnp.requestData['vnp_OrderInfo'] = f"Thanh toan hoa don {hd_id}"
        vnp.requestData['vnp_OrderType'] = 'billpayment'
        vnp.requestData['vnp_Locale'] = 'vn'
        vnp.requestData['vnp_CreateDate'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        vnp.requestData['vnp_IpAddr'] = "127.0.0.1"
        vnp.requestData['vnp_ReturnUrl'] = "http://localhost:3000/patient?guest_vnpay_return=true"

        vnpay_payment_url = vnp.get_payment_url(VNPAY_URL, VNPAY_HASH_SECRET)
    
    db.commit()
    
    return {
        "message": "Tạo đơn đặt lịch thành công",
        "payment_url": vnpay_payment_url,
        "username": req.SDT,
        "password": "123456",
        "is_new_account": is_new_account
    }

@router.get("/bookings")
def get_my_bookings(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    bookings = db.query(DatLichKham).filter(DatLichKham.MaBenhNhan == patient.MaBenhNhan).order_by(desc(DatLichKham.NgayDat)).all()
    res = []
    for b in bookings:
        llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == b.MaLichLamViec).first()
        bs = db.query(BacSi).filter(BacSi.MaBacSi == llv.MaBacSi).first() if llv else None
        res.append({
            "MaDatLich": b.MaDatLich,
            "NgayDat": b.NgayDat.isoformat() if b.NgayDat else None,
            "LyDoKham": b.LyDoKham,
            "TrangThai": b.TrangThai,
            "TenBacSi": bs.HoTen if bs else "Không xác định"
        })
    return res

@router.get("/medical-records")
def get_medical_records(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    # Hồ sơ tổng quát
    hoso = db.query(HoSoBenhAn).filter(HoSoBenhAn.MaBenhNhan == patient.MaBenhNhan).first()
    
    # Danh sách phiếu khám
    phieu_khams = db.query(PhieuKham).filter(PhieuKham.MaBenhNhan == patient.MaBenhNhan).order_by(desc(PhieuKham.NgayKham)).all()
    
    pk_list = []
    for pk in phieu_khams:
        bs = db.query(BacSi).filter(BacSi.MaBacSi == pk.MaBacSi).first()
        pk_list.append({
            "MaPhieuKham": pk.MaPhieuKham,
            "NgayKham": pk.NgayKham,
            "TrieuChung": pk.TrieuChung,
            "ChanDoan": pk.ChanDoan,
            "KetLuan": pk.KetLuan,
            "TenBacSi": bs.HoTen if bs else "Không rõ"
        })
        
    return {
        "HoSo": {
            "TienSuBenh": hoso.TienSuBenh if hoso else "",
            "KetQuaGanNhat": hoso.KetQuaGanNhat if hoso else "",
            "GhiChu": hoso.GhiChu if hoso else ""
        },
        "PhieuKham": pk_list
    }

@router.get("/prescriptions")
def get_prescriptions(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    # Lấy các phiếu khám của bệnh nhân
    phieu_khams = db.query(PhieuKham).filter(PhieuKham.MaBenhNhan == patient.MaBenhNhan).all()
    ma_pk_list = [pk.MaPhieuKham for pk in phieu_khams]
    
    don_thuocs = db.query(DonThuoc).filter(DonThuoc.MaPhieuKham.in_(ma_pk_list)).order_by(desc(DonThuoc.NgayKe)).all()
    
    result = []
    for dt in don_thuocs:
        ctdt_list = db.query(ChiTietDonThuoc).filter(ChiTietDonThuoc.MaDonThuoc == dt.MaDonThuoc).all()
        thuoc_details = []
        for ct in ctdt_list:
            th = db.query(Thuoc).filter(Thuoc.MaThuoc == ct.MaThuoc).first()
            if th:
                thuoc_details.append({
                    "TenThuoc": th.TenThuoc,
                    "DonViTinh": th.DonViTinh,
                    "SoLuong": ct.SoLuong,
                    "LieuDung": ct.LieuDung,
                    "SoNgayDung": ct.SoNgayDung
                })
        
        # Tìm phiếu khám tương ứng để lấy thông tin bác sĩ
        pk = next((p for p in phieu_khams if p.MaPhieuKham == dt.MaPhieuKham), None)
        bs_name = "Không rõ"
        if pk:
            bs = db.query(BacSi).filter(BacSi.MaBacSi == pk.MaBacSi).first()
            if bs: bs_name = bs.HoTen
            
        result.append({
            "MaDonThuoc": dt.MaDonThuoc,
            "NgayKe": dt.NgayKe,
            "GhiChu": dt.GhiChu,
            "TenBacSi": bs_name,
            "ChiTiet": thuoc_details
        })
        
    return result

# --- QUẢN LÝ NGƯỜI NHÀ ---
class NguoiNhaReq(BaseModel):
    HoTen: str
    SDT: str
    CCCD: Optional[str] = None
    QuanHe: Optional[str] = None
    DiaChi: Optional[str] = None

@router.post("/family")
def update_family(req: NguoiNhaReq, patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    from app.models.models import NguoiNha
    if patient.MaNguoiNha:
        nn = db.query(NguoiNha).filter(NguoiNha.MaNguoiNha == patient.MaNguoiNha).first()
        if nn:
            nn.HoTen = req.HoTen
            nn.SDT = req.SDT
            nn.CCCD = req.CCCD
            nn.QuanHe = req.QuanHe
            nn.DiaChi = req.DiaChi
    else:
        import random
        new_id = f"NN{random.randint(10000, 99999)}"
        nn = NguoiNha(
            MaNguoiNha=new_id,
            HoTen=req.HoTen,
            SDT=req.SDT,
            CCCD=req.CCCD,
            QuanHe=req.QuanHe,
            DiaChi=req.DiaChi
        )
        db.add(nn)
        patient.MaNguoiNha = new_id
    db.commit()
    return {"message": "Cập nhật thông tin người nhà thành công"}

@router.get("/family")
def get_family(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    from app.models.models import NguoiNha
    if not patient.MaNguoiNha:
        return None
    nn = db.query(NguoiNha).filter(NguoiNha.MaNguoiNha == patient.MaNguoiNha).first()
    if not nn: return None
    return {
        "HoTen": nn.HoTen,
        "SDT": nn.SDT,
        "CCCD": nn.CCCD,
        "QuanHe": nn.QuanHe,
        "DiaChi": nn.DiaChi
    }

# --- YÊU CẦU HỖ TRỢ ---
class SupportReq(BaseModel):
    NoiDung: str

@router.post("/support")
def create_support_request(req: SupportReq, patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    from app.models.models import YeuCauHoTro
    import random
    new_id = f"YC{random.randint(1000, 9999)}"
    yc = YeuCauHoTro(
        MaYeuCau=new_id,
        MaBenhNhan=patient.MaBenhNhan,
        NoiDung=req.NoiDung,
        NgayGui=datetime.datetime.now(),
        TrangThai="ChoXuLy"
    )
    db.add(yc)
    db.commit()
    return {"message": "Đã gửi yêu cầu hỗ trợ", "MaYeuCau": new_id}

@router.get("/support")
def get_support_requests(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    from app.models.models import YeuCauHoTro, PhanHoiHoTro
    reqs = db.query(YeuCauHoTro).filter(YeuCauHoTro.MaBenhNhan == patient.MaBenhNhan).order_by(desc(YeuCauHoTro.NgayGui)).all()
    result = []
    for r in reqs:
        ph = db.query(PhanHoiHoTro).filter(PhanHoiHoTro.MaYeuCau == r.MaYeuCau).first()
        result.append({
            "MaYeuCau": r.MaYeuCau,
            "NoiDung": r.NoiDung,
            "NgayGui": r.NgayGui,
            "TrangThai": r.TrangThai,
            "PhanHoi": ph.NoiDung if ph else None,
            "NgayPhanHoi": ph.NgayPhanHoi if ph else None
        })
    return result

# --- THANH TOÁN (BILLING & VNPAY) ---

import os
VNPAY_TMN_CODE = os.environ.get("VNPAY_TMN_CODE", "CGXZLS0Z")
VNPAY_HASH_SECRET = os.environ.get("VNPAY_HASH_SECRET", "XNBCJFAKAZQSGTARRLGCHVZWCIOIGSHN")
VNPAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_RETURN_URL = "http://localhost:3000/patient?vnpay_return=true"

@router.get("/invoices")
def get_invoices(patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    hds = db.query(HoaDon).filter(HoaDon.MaBenhNhan == patient.MaBenhNhan).order_by(desc(HoaDon.NgayLap)).all()
    result = []
    for hd in hds:
        dl = db.query(DatLichKham).filter(DatLichKham.MaDatLich == hd.MaDatLich).first()
        bs_name = "Không rõ"
        if dl:
            llv = db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == dl.MaLichLamViec).first()
            if llv:
                bs = db.query(BacSi).filter(BacSi.MaBacSi == llv.MaBacSi).first()
                if bs: bs_name = bs.HoTen
                
        result.append({
            "MaHoaDon": hd.MaHoaDon,
            "NgayLap": hd.NgayLap,
            "TongTien": float(hd.TongTien) if hd.TongTien else 0,
            "TrangThai": hd.TrangThai,
            "PhuongThucThanhToan": hd.PhuongThucThanhToan,
            "TenBacSi": bs_name
        })
    return result

class PaymentReq(BaseModel):
    MaHoaDon: str

@router.post("/payment/create_url")
def create_payment_url(req: PaymentReq, patient: BenhNhan = Depends(get_current_patient), db: Session = Depends(get_db)):
    hd = db.query(HoaDon).filter(HoaDon.MaHoaDon == req.MaHoaDon, HoaDon.MaBenhNhan == patient.MaBenhNhan).first()
    if not hd:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoá đơn")
    if hd.TrangThai == "Đã thanh toán":
        raise HTTPException(status_code=400, detail="Hoá đơn đã được thanh toán")
        
    vnp = vnpay()
    vnp.requestData['vnp_Version'] = '2.1.0'
    vnp.requestData['vnp_Command'] = 'pay'
    vnp.requestData['vnp_TmnCode'] = VNPAY_TMN_CODE
    vnp.requestData['vnp_Amount'] = str(int(float(hd.TongTien) * 100))
    vnp.requestData['vnp_CurrCode'] = 'VND'
    vnp.requestData['vnp_TxnRef'] = hd.MaHoaDon.strip()
    vnp.requestData['vnp_OrderInfo'] = f"Thanh toan hoa don {hd.MaHoaDon}"
    vnp.requestData['vnp_OrderType'] = 'billpayment'
    vnp.requestData['vnp_Locale'] = 'vn'
    vnp.requestData['vnp_CreateDate'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    vnp.requestData['vnp_IpAddr'] = "127.0.0.1"
    vnp.requestData['vnp_ReturnUrl'] = VNPAY_RETURN_URL

    vnpay_payment_url = vnp.get_payment_url(VNPAY_URL, VNPAY_HASH_SECRET)
    return {"payment_url": vnpay_payment_url}

from fastapi import Request
from fastapi.responses import RedirectResponse

@router.get("/payment/vnpay_return")
def vnpay_return(request: Request, db: Session = Depends(get_db)):
    inputData = request.query_params
    vnp = vnpay()
    vnp.responseData = dict(inputData)
    
    order_id = inputData.get('vnp_TxnRef')
    response_code = inputData.get('vnp_ResponseCode')
    
    if vnp.validate_response(VNPAY_HASH_SECRET):
        if response_code == "00":
            # Success
            hd = db.query(HoaDon).filter(HoaDon.MaHoaDon == order_id).first()
            if hd:
                hd.TrangThai = "Đã thanh toán"
                hd.PhuongThucThanhToan = "VNPay"
                db.commit()
            return RedirectResponse(url=f"http://localhost:3000/patient?tab=billing&status=success")
        else:
            return RedirectResponse(url=f"http://localhost:3000/patient?tab=billing&status=failed")
    else:
        return RedirectResponse(url=f"http://localhost:3000/patient?tab=billing&status=invalid_signature")
