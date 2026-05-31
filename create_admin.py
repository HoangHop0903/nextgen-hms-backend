import sys
import os

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.models import TaiKhoan

db = SessionLocal()
try:
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
        print('Created admin account.')
    else:
        print('Admin account already exists.')
except Exception as e:
    print('Error:', e)
finally:
    db.close()
