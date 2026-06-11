from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import TaiKhoan, BacSi, NhanVien
import random

engine = create_engine('postgresql://postgres.pghpekvenlnzflenefuk:Hophoangluu0908588469@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres')
db = sessionmaker(bind=engine)()

bs_tk = [b.MaTaiKhoan for b in db.query(BacSi).all()]
nv_tk = [n.MaTaiKhoan for n in db.query(NhanVien).all()]
tks = db.query(TaiKhoan).all()

count = 0
for tk in tks:
    if tk.VaiTro == 'BACSI' and tk.MaTaiKhoan not in bs_tk:
        new_id = f'BS{random.randint(10000,99999)}'
        db.add(BacSi(MaBacSi=new_id, MaTaiKhoan=tk.MaTaiKhoan, MaChuyenKhoa='CK01', HoTen=f"BS {tk.TenDangNhap}", HocVi='BS', SDT='0123456789', TrangThai=True))
        count += 1
    elif tk.VaiTro == 'NHANVIEN' and tk.MaTaiKhoan not in nv_tk:
        new_id = f'NV{random.randint(10000,99999)}'
        db.add(NhanVien(MaNhanVien=new_id, MaTaiKhoan=tk.MaTaiKhoan, HoTen=f"NV {tk.TenDangNhap}", ChucVu='Nhân viên', SDT='0123456789', TrangThai=True))
        count += 1

db.commit()
print(f"Added {count} personnel")
