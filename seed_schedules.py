import datetime
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import (
    BacSi, BenhNhan, CaKham, PhongKham, LichPhongKham, LichLamViec, BangGiaKham,
    DatLichKham, PhieuKham, Thuoc, DonThuoc, ChiTietDonThuoc
)

DATABASE_URL = "postgresql://postgres.pghpekvenlnzflenefuk:Hophoangluu0908588469@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("Bắt đầu tạo dữ liệu...")
    
    # 1. Lấy dữ liệu cơ sở
    bs1 = db.query(BacSi).filter(BacSi.MaBacSi == "BS01").first()
    bs2 = db.query(BacSi).filter(BacSi.MaBacSi == "BS02").first()
    p1 = db.query(PhongKham).filter(PhongKham.MaPhong == "P101").first()
    p2 = db.query(PhongKham).filter(PhongKham.MaPhong == "P102").first()
    ca1 = db.query(CaKham).filter(CaKham.MaCaKham == "CA1").first()
    ca2 = db.query(CaKham).filter(CaKham.MaCaKham == "CA2").first()
    bg1 = db.query(BangGiaKham).filter(BangGiaKham.MaChuyenKhoa == "CK01").first()
    bg2 = db.query(BangGiaKham).filter(BangGiaKham.MaChuyenKhoa == "CK02").first()
    
    benh_nhan_list = db.query(BenhNhan).all()

    # 2. Tạo Thuốc (nếu chưa có)
    thuocs = [
        {"ma": "T001", "ten": "Paracetamol 500mg", "dvt": "Viên", "gia": 2000},
        {"ma": "T002", "ten": "Amoxicillin 250mg", "dvt": "Viên", "gia": 5000},
        {"ma": "T003", "ten": "Vitamin C", "dvt": "Viên", "gia": 1000},
        {"ma": "T004", "ten": "Siro Ho Astex", "dvt": "Chai", "gia": 45000}
    ]
    for t in thuocs:
        if not db.query(Thuoc).filter(Thuoc.MaThuoc == t["ma"]).first():
            db.add(Thuoc(MaThuoc=t["ma"], TenThuoc=t["ten"], DonViTinh=t["dvt"], GiaThuoc=t["gia"], CachDung="Uống sau ăn", TrangThai=True))
    db.commit()

    # 3. Tạo Lịch Phòng Khám và Lịch Làm Việc (12/06/2026 - 15/06/2026)
    start_date = datetime.date(2026, 6, 12)
    end_date = datetime.date(2026, 6, 15)
    delta = datetime.timedelta(days=1)
    
    current_date = start_date
    while current_date <= end_date:
        for p, bs in [(p1, bs1), (p2, bs2)]:
            for ca in [ca1, ca2]:
                # Lịch Phòng Khám
                ma_lpk = f"LPK{random.randint(10000, 99999)}"
                lpk = db.query(LichPhongKham).filter(LichPhongKham.MaLichPhong == ma_lpk).first()
                if not lpk:
                    lpk = LichPhongKham(
                        MaLichPhong=ma_lpk, MaPhong=p.MaPhong, MaCaKham=ca.MaCaKham,
                        NgayKham=current_date, SoLuongToiDa=20, SoLuongDaDat=0, TrangThai="Đang mở"
                    )
                    db.add(lpk)
                    db.flush()
                
                # Lịch Làm Việc (gán Bác sĩ vào Lịch Phòng Khám)
                ma_llv = f"LLV{random.randint(10000, 99999)}"
                if not db.query(LichLamViec).filter(LichLamViec.MaLichLamViec == ma_llv).first():
                    llv = LichLamViec(MaLichLamViec=ma_llv, MaBacSi=bs.MaBacSi, MaLichPhong=lpk.MaLichPhong, TrangThai="Chờ khám")
                    db.add(llv)
        current_date += delta
    db.commit()

    # 4. Đặt Lịch Khám cho 3 ngày này (mỗi ngày đặt 1-2 bệnh nhân)
    llvs_p1_date1 = db.query(LichLamViec).join(LichPhongKham).filter(LichLamViec.MaBacSi == "BS01", LichPhongKham.NgayKham == datetime.date(2026, 6, 12)).all()
    llvs_p2_date2 = db.query(LichLamViec).join(LichPhongKham).filter(LichLamViec.MaBacSi == "BS02", LichPhongKham.NgayKham == datetime.date(2026, 6, 13)).all()
    llvs_p1_date3 = db.query(LichLamViec).join(LichPhongKham).filter(LichLamViec.MaBacSi == "BS01", LichPhongKham.NgayKham == datetime.date(2026, 6, 14)).all()
    
    def book_appointment(bn, llv, bg, lydo):
        ma_dl = f"DL{random.randint(10000, 99999)}"
        if not db.query(DatLichKham).filter(DatLichKham.MaDatLich == ma_dl).first():
            dl = DatLichKham(
                MaDatLich=ma_dl, MaBenhNhan=bn.MaBenhNhan, MaLichLamViec=llv.MaLichLamViec,
                MaBangGia=bg.MaBangGia, NgayDat=datetime.datetime.now(), KhungGio="08:00",
                LyDoKham=lydo, TrangThai="DaTiepNhan", LoaiDat="TrucTuyen"
            )
            db.add(dl)

    if llvs_p1_date1 and benh_nhan_list:
        book_appointment(benh_nhan_list[0], llvs_p1_date1[0], bg1, "Đau đầu, chóng mặt kéo dài")
    if llvs_p2_date2 and len(benh_nhan_list) > 1:
        book_appointment(benh_nhan_list[1], llvs_p2_date2[0], bg2, "Sốt cao, ho có đờm")
    if llvs_p1_date3 and len(benh_nhan_list) > 2:
        book_appointment(benh_nhan_list[2], llvs_p1_date3[0], bg1, "Khám tổng quát, đau dạ dày")
    
    db.commit()

    # 5. Tạo Lịch Sử Phiếu Khám Cũ (để Bác sĩ có thể xem ở Popup Chi tiết)
    past_date = datetime.date(2026, 5, 10)
    for idx, bn in enumerate(benh_nhan_list[:2]):
        pk_id = f"PK{random.randint(10000, 99999)}"
        if not db.query(PhieuKham).filter(PhieuKham.MaPhieuKham == pk_id).first():
            pk = PhieuKham(
                MaPhieuKham=pk_id, MaBenhNhan=bn.MaBenhNhan, MaBacSi="BS01" if idx==0 else "BS02",
                NgayKham=datetime.datetime(2026, 5 - idx, 10 + idx, 9, 30),
                TrieuChung="Đau họng, nghẹt mũi" if idx==0 else "Tiêu chảy cấp",
                ChanDoan="Viêm họng cấp" if idx==0 else "Rối loạn tiêu hóa",
                KetLuan="Cấp thuốc về nhà uống", GhiChu="Khám lần đầu"
            )
            db.add(pk)
            
            # Đơn thuốc cũ
            dt_id = f"DT{random.randint(10000, 99999)}"
            dt = DonThuoc(MaDonThuoc=dt_id, MaPhieuKham=pk_id, NgayKe=datetime.datetime(2026, 5 - idx, 10 + idx, 9, 45), GhiChu="Uống sau ăn no")
            db.add(dt)
            
            # Chi tiết thuốc
            db.add(ChiTietDonThuoc(MaCTDT=f"CT1{random.randint(1000, 9999)}", MaDonThuoc=dt_id, MaThuoc="T001", SoLuong=10, LieuDung="Ngày 2 viên", SoNgayDung=5))
            db.add(ChiTietDonThuoc(MaCTDT=f"CT2{random.randint(1000, 9999)}", MaDonThuoc=dt_id, MaThuoc="T002", SoLuong=15, LieuDung="Ngày 3 viên", SoNgayDung=5))

    db.commit()
    print("Done")
except Exception as e:
    print("Error:", e)
finally:
    db.close()
