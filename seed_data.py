import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import *
import datetime

db = SessionLocal()

def seed_data():
    try:
        print("Bắt đầu tạo dữ liệu mẫu...")
        # 1. Chuyên khoa
        print("Tạo Chuyên Khoa...")
        ck_noi = ChuyenKhoa(MaChuyenKhoa="CK01", TenChuyenKhoa="Nội tổng quát", MoTa="Khám nội", TrangThai=True)
        ck_tim = ChuyenKhoa(MaChuyenKhoa="CK02", TenChuyenKhoa="Tim mạch", MoTa="Khám tim mạch", TrangThai=True)
        ck_mat = ChuyenKhoa(MaChuyenKhoa="CK03", TenChuyenKhoa="Nhãn khoa", MoTa="Khám mắt", TrangThai=True)
        db.merge(ck_noi)
        db.merge(ck_tim)
        db.merge(ck_mat)

        # 2. Phòng khám
        print("Tạo Phòng Khám...")
        pk1 = PhongKham(MaPhong="P101", MaChuyenKhoa="CK01", TenPhong="Phòng Nội 1", Tang=1, Khu="A", TrangThai=True)
        pk2 = PhongKham(MaPhong="P102", MaChuyenKhoa="CK02", TenPhong="Phòng Tim mạch 1", Tang=1, Khu="B", TrangThai=True)
        db.merge(pk1)
        db.merge(pk2)

        # 3. Thuốc
        print("Tạo Thuốc...")
        t1 = Thuoc(MaThuoc="TH01", TenThuoc="Paracetamol 500mg", DonViTinh="Viên", GiaThuoc=2000, CachDung="Uống", TrangThai=True)
        t2 = Thuoc(MaThuoc="TH02", TenThuoc="Aspirin", DonViTinh="Viên", GiaThuoc=3000, CachDung="Uống", TrangThai=True)
        db.merge(t1)
        db.merge(t2)

        # 4. Bảng giá
        print("Tạo Bảng Giá...")
        bg1 = BangGiaKham(MaBangGia="BG01", MaChuyenKhoa="CK01", TenDichVu="Khám nội thông thường", GiaKham=150000, TrangThai=True)
        bg2 = BangGiaKham(MaBangGia="BG02", MaChuyenKhoa="CK02", TenDichVu="Khám chuyên sâu tim mạch", GiaKham=300000, TrangThai=True)
        db.merge(bg1)
        db.merge(bg2)

        # 5. Ca khám
        print("Tạo Ca Khám...")
        ca1 = CaKham(MaCaKham="CA01", TenCa="Sáng", GioBatDau=datetime.time(7, 30), GioKetThuc=datetime.time(11, 30), TrangThai=True)
        ca2 = CaKham(MaCaKham="CA02", TenCa="Chiều", GioBatDau=datetime.time(13, 0), GioKetThuc=datetime.time(17, 0), TrangThai=True)
        db.merge(ca1)
        db.merge(ca2)

        db.commit()

        # 6. Bác sĩ (Find existing doctors and assign them to specialties)
        print("Cập nhật Bác sĩ...")
        doctors = db.query(BacSi).all()
        if len(doctors) > 0:
            doctors[0].MaChuyenKhoa = "CK01"
            if len(doctors) > 1:
                doctors[1].MaChuyenKhoa = "CK02"
            db.commit()

            # 7. Lịch phòng khám
            print("Tạo Lịch Phòng Khám & Lịch Làm Việc...")
            today = datetime.date.today()
            lpk1 = LichPhongKham(MaLichPhong="LPK01", MaPhong="P101", MaCaKham="CA01", NgayKham=today, SoLuongToiDa=20, SoLuongDaDat=0, TrangThai="Mo")
            lpk2 = LichPhongKham(MaLichPhong="LPK02", MaPhong="P102", MaCaKham="CA02", NgayKham=today, SoLuongToiDa=15, SoLuongDaDat=0, TrangThai="Mo")
            db.merge(lpk1)
            db.merge(lpk2)
            db.commit()

            llv1 = LichLamViec(MaLichLamViec="LLV01", MaBacSi=doctors[0].MaBacSi, MaLichPhong="LPK01", TrangThai="HoatDong")
            db.merge(llv1)
            if len(doctors) > 1:
                llv2 = LichLamViec(MaLichLamViec="LLV02", MaBacSi=doctors[1].MaBacSi, MaLichPhong="LPK02", TrangThai="HoatDong")
                db.merge(llv2)
            db.commit()

        print("Tạo dữ liệu thành công!")
    except Exception as e:
        db.rollback()
        print("Lỗi:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
