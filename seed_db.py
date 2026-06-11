import datetime
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Tải cấu hình DB
from app.core.database import Base
from app.models.models import (
    TaiKhoan, NguoiNha, BenhNhan, NhanVien, ChuyenKhoa, PhongKham, BacSi,
    CaKham, LichPhongKham, BangGiaKham, HoSoBenhAn
)

DATABASE_URL = "postgresql://postgres.pghpekvenlnzflenefuk:Hophoangluu0908588469@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

def hash_password(password: str):
    return pwd_context.hash(password)

print("Đang tạo dữ liệu mẫu...")

try:
    # 1. Tạo Chuyên Khoa
    ck1 = ChuyenKhoa(MaChuyenKhoa="CK01", TenChuyenKhoa="Nội tổng hợp", MoTa="Khám nội", TrangThai=True)
    ck2 = ChuyenKhoa(MaChuyenKhoa="CK02", TenChuyenKhoa="Nhi khoa", MoTa="Khám nhi", TrangThai=True)
    ck3 = ChuyenKhoa(MaChuyenKhoa="CK03", TenChuyenKhoa="Răng Hàm Mặt", MoTa="Khám răng", TrangThai=True)
    for ck in [ck1, ck2, ck3]:
        if not db.query(ChuyenKhoa).filter(ChuyenKhoa.MaChuyenKhoa == ck.MaChuyenKhoa).first():
            db.add(ck)
    db.commit()

    # 2. Tạo Bảng Giá
    bg1 = BangGiaKham(MaBangGia="BG01", MaChuyenKhoa="CK01", TenDichVu="Khám nội thường", GiaKham=150000, TrangThai=True)
    bg2 = BangGiaKham(MaBangGia="BG02", MaChuyenKhoa="CK02", TenDichVu="Khám nhi", GiaKham=200000, TrangThai=True)
    for bg in [bg1, bg2]:
        if not db.query(BangGiaKham).filter(BangGiaKham.MaBangGia == bg.MaBangGia).first():
            db.add(bg)
    db.commit()

    # 3. Tạo Phòng Khám
    pk1 = PhongKham(MaPhong="P101", MaChuyenKhoa="CK01", TenPhong="Phòng Khám Nội 1", Tang=1, Khu="A", TrangThai=True)
    pk2 = PhongKham(MaPhong="P102", MaChuyenKhoa="CK02", TenPhong="Phòng Khám Nhi 1", Tang=1, Khu="A", TrangThai=True)
    for pk in [pk1, pk2]:
        if not db.query(PhongKham).filter(PhongKham.MaPhong == pk.MaPhong).first():
            db.add(pk)
    db.commit()

    # 4. Tạo Ca Khám
    ca1 = CaKham(MaCaKham="CA1", TenCa="Sáng", GioBatDau=datetime.time(7,0), GioKetThuc=datetime.time(11,30), TrangThai=True)
    ca2 = CaKham(MaCaKham="CA2", TenCa="Chiều", GioBatDau=datetime.time(13,30), GioKetThuc=datetime.time(17,0), TrangThai=True)
    for ca in [ca1, ca2]:
        if not db.query(CaKham).filter(CaKham.MaCaKham == ca.MaCaKham).first():
            db.add(ca)
    db.commit()

    # 5. Tạo Bác Sĩ (TaiKhoan + BacSi)
    bs_list = [
        {"ma": "BS01", "ten": "Lê Văn Hùng", "username": "bs_hung", "ck": "CK01", "hocvi": "ThS.BS"},
        {"ma": "BS02", "ten": "Trần Thị Cúc", "username": "bs_cuc", "ck": "CK02", "hocvi": "BSCK1"}
    ]
    for b in bs_list:
        if not db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == b["username"]).first():
            tk = TaiKhoan(MaTaiKhoan=b["ma"], TenDangNhap=b["username"], MatKhau=hash_password("123456"), VaiTro="BAC_SI", TrangThai=True)
            db.add(tk)
            bs = BacSi(MaBacSi=b["ma"], MaTaiKhoan=b["ma"], MaChuyenKhoa=b["ck"], HoTen=b["ten"], HocVi=b["hocvi"], SDT="0911111111", TrangThai=True)
            db.add(bs)
    db.commit()

    # 6. Tạo Nhân Viên (TaiKhoan + NhanVien)
    if not db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == "nv_lan").first():
        tk = TaiKhoan(MaTaiKhoan="NV01", TenDangNhap="nv_lan", MatKhau=hash_password("123456"), VaiTro="NHAN_VIEN", TrangThai=True)
        db.add(tk)
        nv = NhanVien(MaNhanVien="NV01", MaTaiKhoan="NV01", HoTen="Nguyễn Thị Lan", ChucVu="Lễ Tân", SDT="0922222222", TrangThai=True)
        db.add(nv)
    db.commit()

    # 7. Tạo Bệnh Nhân (TaiKhoan + BenhNhan + HoSoBenhAn)
    bn_list = [
        {"ma": "BN001", "ten": "Phạm Văn Cường", "username": "bn_cuong", "sdt": "0981112222", "diung": "Hải sản"},
        {"ma": "BN002", "ten": "Lê Minh Tuấn", "username": "bn_tuan", "sdt": "0983334444", "diung": "Thuốc kháng sinh"},
        {"ma": "BN003", "ten": "Hoàng Thị Mai", "username": "bn_mai", "sdt": "0985556666", "diung": ""}
    ]
    for b in bn_list:
        if not db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == b["username"]).first():
            tk = TaiKhoan(MaTaiKhoan=b["ma"], TenDangNhap=b["username"], MatKhau=hash_password("123456"), VaiTro="BENH_NHAN", TrangThai=True)
            db.add(tk)
            bn = BenhNhan(
                MaBenhNhan=b["ma"], MaTaiKhoan=b["ma"], HoTen=b["ten"], 
                GioiTinh="Nam" if "Thị" not in b["ten"] else "Nữ",
                SDT=b["sdt"], TienSuDiUng=b["diung"], DiaChi="Hà Nội", TrangThai=True,
                NgaySinh=datetime.date(1990 + random.randint(-10, 10), random.randint(1, 12), random.randint(1, 28))
            )
            db.add(bn)
            hs = HoSoBenhAn(
                MaHoSo=f"HS{b['ma']}",
                MaBenhNhan=b["ma"],
                NgayLap=datetime.date.today(),
                TienSuBenh="Cao huyết áp" if random.random() > 0.5 else ""
            )
            db.add(hs)
    db.commit()

    print("Tạo dữ liệu thành công! Tài khoản test: bs_hung / 123456, nv_lan / 123456, bn_cuong / 123456")
except Exception as e:
    print("Lỗi tạo dữ liệu:", e)
finally:
    db.close()
