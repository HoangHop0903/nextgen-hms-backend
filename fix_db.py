import sys
sys.path.append('C:\\Users\\AD\\Downloads\\NextGen_HMS\\backend')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("ALTER TABLE BenhNhan ALTER COLUMN HoTen NVARCHAR(100);"))
    db.execute(text("ALTER TABLE BenhNhan ALTER COLUMN DiaChi NVARCHAR(255);"))
    
    # Update the corrupted records
    db.execute(text("UPDATE BenhNhan SET HoTen = N'Nguyễn Văn B' WHERE HoTen LIKE 'Nguy?n Van B'"))
    db.execute(text("UPDATE BenhNhan SET HoTen = N'Đặng Đình Yến Nga' WHERE HoTen LIKE 'Dang Dinh Yen Nga'"))
    
    db.commit()
    print('Altered columns to NVARCHAR and fixed data')
except Exception as e:
    print(e)
finally:
    db.close()
