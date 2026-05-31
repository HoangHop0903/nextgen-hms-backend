from sqlalchemy import Column, String, Boolean, Date, Time, Numeric, DateTime, ForeignKey, Integer, NVARCHAR
from sqlalchemy.orm import relationship
from app.core.database import Base

class TaiKhoan(Base):
    __tablename__ = 'TaiKhoan'
    MaTaiKhoan = Column(String(10), primary_key=True)
    TenDangNhap = Column(String(50), unique=True, nullable=False)
    MatKhau = Column(String(255), nullable=False)
    Email = Column(String(100))
    VaiTro = Column(String(30), nullable=False)
    TrangThai = Column(Boolean, nullable=False)

class NguoiNha(Base):
    __tablename__ = 'NguoiNha'
    MaNguoiNha = Column(String(10), primary_key=True)
    HoTen = Column(String(100), nullable=False)
    SDT = Column(String(15), nullable=False)
    CCCD = Column(String(20))
    QuanHe = Column(String(50))
    DiaChi = Column(String(255))

class BenhNhan(Base):
    __tablename__ = 'BenhNhan'
    MaBenhNhan = Column(String(10), primary_key=True)
    MaTaiKhoan = Column(String(10), ForeignKey('TaiKhoan.MaTaiKhoan'))
    MaNguoiNha = Column(String(10), ForeignKey('NguoiNha.MaNguoiNha'))
    HoTen = Column(NVARCHAR(100), nullable=False)
    NgaySinh = Column(Date)
    GioiTinh = Column(String(10))
    CCCD = Column(String(20))
    SDT = Column(String(15))
    DiaChi = Column(NVARCHAR(255))
    SoBHYT = Column(String(30))
    TienSuDiUng = Column(String(255))
    AnhDaiDien = Column(String(255))
    TrangThai = Column(Boolean, nullable=False)
    
    taikhoan = relationship("TaiKhoan")
    nguoinha = relationship("NguoiNha")

class HoSoBenhAn(Base):
    __tablename__ = 'HoSoBenhAn'
    MaHoSo = Column(String(10), primary_key=True)
    MaBenhNhan = Column(String(10), ForeignKey('BenhNhan.MaBenhNhan'))
    NgayLap = Column(Date)
    TienSuBenh = Column(String(255))
    KetQuaGanNhat = Column(String(255))
    GhiChu = Column(String(255))
    
    benhnhan = relationship("BenhNhan")

class NhanVien(Base):
    __tablename__ = 'NhanVien'
    MaNhanVien = Column(String(10), primary_key=True)
    MaTaiKhoan = Column(String(10), ForeignKey('TaiKhoan.MaTaiKhoan'))
    HoTen = Column(String(100))
    NgaySinh = Column(Date)
    GioiTinh = Column(String(10))
    SDT = Column(String(15))
    DiaChi = Column(String(255))
    ChucVu = Column(String(50))
    AnhDaiDien = Column(String(255))
    TrangThai = Column(Boolean, nullable=False)
    
    taikhoan = relationship("TaiKhoan")

class ChuyenKhoa(Base):
    __tablename__ = 'ChuyenKhoa'
    MaChuyenKhoa = Column(String(10), primary_key=True)
    TenChuyenKhoa = Column(String(100), nullable=False)
    MoTa = Column(String(255))
    TrangThai = Column(Boolean, nullable=False)

class PhongKham(Base):
    __tablename__ = 'PhongKham'
    MaPhong = Column(String(10), primary_key=True)
    MaChuyenKhoa = Column(String(10), ForeignKey('ChuyenKhoa.MaChuyenKhoa'))
    TenPhong = Column(String(100))
    Tang = Column(Integer)
    Khu = Column(String(50))
    TrangThai = Column(Boolean, nullable=False)
    
    chuyenkhoa = relationship("ChuyenKhoa")

class BacSi(Base):
    __tablename__ = 'BacSi'
    MaBacSi = Column(String(10), primary_key=True)
    MaTaiKhoan = Column(String(10), ForeignKey('TaiKhoan.MaTaiKhoan'))
    MaChuyenKhoa = Column(String(10), ForeignKey('ChuyenKhoa.MaChuyenKhoa'))
    HoTen = Column(String(100))
    HocVi = Column(String(50))
    SDT = Column(String(15))
    Email = Column(String(100))
    AnhDaiDien = Column(String(255))
    TrangThai = Column(Boolean, nullable=False)
    
    taikhoan = relationship("TaiKhoan")
    chuyenkhoa = relationship("ChuyenKhoa")

class CaKham(Base):
    __tablename__ = 'CaKham'
    MaCaKham = Column(String(10), primary_key=True)
    TenCa = Column(String(50))
    GioBatDau = Column(Time)
    GioKetThuc = Column(Time)
    TrangThai = Column(Boolean, nullable=False)

class LichPhongKham(Base):
    __tablename__ = 'LichPhongKham'
    MaLichPhong = Column(String(10), primary_key=True)
    MaPhong = Column(String(10), ForeignKey('PhongKham.MaPhong'))
    MaCaKham = Column(String(10), ForeignKey('CaKham.MaCaKham'))
    NgayKham = Column(Date)
    SoLuongToiDa = Column(Integer)
    SoLuongDaDat = Column(Integer, default=0)
    TrangThai = Column(String(30))
    
    phong = relationship("PhongKham")
    cakham = relationship("CaKham")

class LichLamViec(Base):
    __tablename__ = 'LichLamViec'
    MaLichLamViec = Column(String(10), primary_key=True)
    MaBacSi = Column(String(10), ForeignKey('BacSi.MaBacSi'))
    MaLichPhong = Column(String(10), ForeignKey('LichPhongKham.MaLichPhong'))
    TrangThai = Column(String(30))
    
    bacsi = relationship("BacSi")
    lichphong = relationship("LichPhongKham")

class BangGiaKham(Base):
    __tablename__ = 'BangGiaKham'
    MaBangGia = Column(String(10), primary_key=True)
    MaChuyenKhoa = Column(String(10), ForeignKey('ChuyenKhoa.MaChuyenKhoa'))
    TenDichVu = Column(String(100))
    GiaKham = Column(Numeric(18, 2))
    TrangThai = Column(Boolean, nullable=False)
    
    chuyenkhoa = relationship("ChuyenKhoa")

class DatLichKham(Base):
    __tablename__ = 'DatLichKham'
    MaDatLich = Column(String(10), primary_key=True)
    MaBenhNhan = Column(String(10), ForeignKey('BenhNhan.MaBenhNhan'))
    MaLichLamViec = Column(String(10), ForeignKey('LichLamViec.MaLichLamViec'))
    MaBangGia = Column(String(10), ForeignKey('BangGiaKham.MaBangGia'))
    NgayDat = Column(DateTime)
    KhungGio = Column(String(10))  # VD: "09:00", "09:30"
    LyDoKham = Column(NVARCHAR(255))
    TrangThai = Column(String(30))
    LoaiDat = Column(String(30))
    
    benhnhan = relationship("BenhNhan")
    lichlamviec = relationship("LichLamViec")
    banggia = relationship("BangGiaKham")

class LichSuDatLich(Base):
    __tablename__ = 'LichSuDatLich'
    MaLichSu = Column(String(10), primary_key=True)
    MaDatLich = Column(String(10), ForeignKey('DatLichKham.MaDatLich'))
    ThoiGianThayDoi = Column(DateTime)
    NoiDung = Column(String(255))
    TrangThai = Column(String(50))
    
    datlich = relationship("DatLichKham")

class PhieuTiepNhan(Base):
    __tablename__ = 'PhieuTiepNhan'
    MaPhieuTiepNhan = Column(String(10), primary_key=True)
    MaDatLich = Column(String(10), ForeignKey('DatLichKham.MaDatLich'))
    MaNhanVien = Column(String(10), ForeignKey('NhanVien.MaNhanVien'))
    NgayTiepNhan = Column(DateTime)
    SoThuTu = Column(Integer)
    TrangThai = Column(String(30))
    
    datlich = relationship("DatLichKham")
    nhanvien = relationship("NhanVien")

class PhieuKham(Base):
    __tablename__ = 'PhieuKham'
    MaPhieuKham = Column(String(10), primary_key=True)
    MaBenhNhan = Column(String(10), ForeignKey('BenhNhan.MaBenhNhan'))
    MaBacSi = Column(String(10), ForeignKey('BacSi.MaBacSi'))
    MaPhong = Column(String(10), ForeignKey('PhongKham.MaPhong'))
    NgayKham = Column(DateTime)
    TrieuChung = Column(NVARCHAR(255))
    ChanDoan = Column(NVARCHAR(255))
    KetLuan = Column(NVARCHAR(255))
    GhiChu = Column(NVARCHAR(255))
    
    benhnhan = relationship("BenhNhan")
    bacsi = relationship("BacSi")
    phong = relationship("PhongKham")

class Thuoc(Base):
    __tablename__ = 'Thuoc'
    MaThuoc = Column(String(10), primary_key=True)
    TenThuoc = Column(String(100))
    DonViTinh = Column(String(30))
    GiaThuoc = Column(Numeric(18, 2))
    CachDung = Column(String(255))
    TrangThai = Column(Boolean, nullable=False)

class DonThuoc(Base):
    __tablename__ = 'DonThuoc'
    MaDonThuoc = Column(String(10), primary_key=True)
    MaPhieuKham = Column(String(10), ForeignKey('PhieuKham.MaPhieuKham'))
    NgayKe = Column(DateTime)
    GhiChu = Column(NVARCHAR(255))
    
    phieukham = relationship("PhieuKham")

class ChiTietDonThuoc(Base):
    __tablename__ = 'ChiTietDonThuoc'
    MaCTDT = Column(String(10), primary_key=True)
    MaDonThuoc = Column(String(10), ForeignKey('DonThuoc.MaDonThuoc'))
    MaThuoc = Column(String(10), ForeignKey('Thuoc.MaThuoc'))
    SoLuong = Column(Integer)
    LieuDung = Column(String(255))
    SoNgayDung = Column(Integer)
    
    donthuoc = relationship("DonThuoc")
    thuoc = relationship("Thuoc")

class YeuCauHoTro(Base):
    __tablename__ = 'YeuCauHoTro'
    MaYeuCau = Column(String(10), primary_key=True)
    MaBenhNhan = Column(String(10), ForeignKey('BenhNhan.MaBenhNhan'))
    NoiDung = Column(NVARCHAR(500))
    NgayGui = Column(DateTime)
    TrangThai = Column(String(30))
    
    benhnhan = relationship("BenhNhan")

class PhanHoiHoTro(Base):
    __tablename__ = 'PhanHoiHoTro'
    MaPhanHoi = Column(String(10), primary_key=True)
    MaYeuCau = Column(String(10), ForeignKey('YeuCauHoTro.MaYeuCau'))
    MaNhanVien = Column(String(10), ForeignKey('NhanVien.MaNhanVien'))
    NoiDung = Column(NVARCHAR(500))
    NgayPhanHoi = Column(DateTime)
    
    yeucau = relationship("YeuCauHoTro")
    nhanvien = relationship("NhanVien")

class HoaDon(Base):
    __tablename__ = 'HoaDon'
    MaHoaDon = Column(String(10), primary_key=True)
    MaBenhNhan = Column(String(10), ForeignKey('BenhNhan.MaBenhNhan'))
    MaDatLich = Column(String(10), ForeignKey('DatLichKham.MaDatLich'))
    TongTien = Column(Numeric(18, 2))
    NgayLap = Column(DateTime)
    TrangThai = Column(NVARCHAR(50))
    PhuongThucThanhToan = Column(NVARCHAR(50))
    
    benhnhan = relationship("BenhNhan")
    datlich = relationship("DatLichKham")
