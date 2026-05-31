from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal

# --- TaiKhoan ---
class TaiKhoanBase(BaseModel):
    MaTaiKhoan: str
    TenDangNhap: str
    Email: Optional[str] = None
    VaiTro: str
    TrangThai: bool

class TaiKhoanCreate(TaiKhoanBase):
    MatKhau: str

class TaiKhoanResponse(TaiKhoanBase):
    class Config:
        from_attributes = True

# --- NguoiNha ---
class NguoiNhaBase(BaseModel):
    MaNguoiNha: str
    HoTen: str
    SDT: str
    CCCD: Optional[str] = None
    QuanHe: Optional[str] = None
    DiaChi: Optional[str] = None

class NguoiNhaResponse(NguoiNhaBase):
    class Config:
        from_attributes = True

# --- BenhNhan ---
class BenhNhanBase(BaseModel):
    MaBenhNhan: str
    MaTaiKhoan: Optional[str] = None
    MaNguoiNha: Optional[str] = None
    HoTen: str
    NgaySinh: Optional[date] = None
    GioiTinh: Optional[str] = None
    CCCD: Optional[str] = None
    SDT: Optional[str] = None
    DiaChi: Optional[str] = None
    SoBHYT: Optional[str] = None
    TienSuDiUng: Optional[str] = None
    TrangThai: bool

class BenhNhanResponse(BenhNhanBase):
    class Config:
        from_attributes = True

# --- ChuyenKhoa ---
class ChuyenKhoaBase(BaseModel):
    MaChuyenKhoa: str
    TenChuyenKhoa: str
    MoTa: Optional[str] = None
    TrangThai: bool

class ChuyenKhoaResponse(ChuyenKhoaBase):
    class Config:
        from_attributes = True

# --- BacSi ---
class BacSiBase(BaseModel):
    MaBacSi: str
    MaTaiKhoan: Optional[str] = None
    MaChuyenKhoa: Optional[str] = None
    HoTen: Optional[str] = None
    HocVi: Optional[str] = None
    SDT: Optional[str] = None
    Email: Optional[str] = None
    TrangThai: bool

class BacSiResponse(BacSiBase):
    class Config:
        from_attributes = True

# --- NhanVien ---
class NhanVienBase(BaseModel):
    MaNhanVien: str
    MaTaiKhoan: Optional[str] = None
    HoTen: Optional[str] = None
    NgaySinh: Optional[date] = None
    GioiTinh: Optional[str] = None
    SDT: Optional[str] = None
    DiaChi: Optional[str] = None
    ChucVu: Optional[str] = None
    TrangThai: bool

class NhanVienResponse(NhanVienBase):
    class Config:
        from_attributes = True

# --- PhongKham ---
class PhongKhamBase(BaseModel):
    MaPhong: str
    MaChuyenKhoa: Optional[str] = None
    TenPhong: Optional[str] = None
    Tang: Optional[int] = None
    Khu: Optional[str] = None
    TrangThai: bool

class PhongKhamResponse(PhongKhamBase):
    class Config:
        from_attributes = True

# --- CaKham ---
class CaKhamBase(BaseModel):
    MaCaKham: str
    TenCa: Optional[str] = None
    GioBatDau: Optional[time] = None
    GioKetThuc: Optional[time] = None
    TrangThai: bool

class CaKhamResponse(CaKhamBase):
    class Config:
        from_attributes = True

# --- LichPhongKham ---
class LichPhongKhamBase(BaseModel):
    MaLichPhong: str
    MaPhong: Optional[str] = None
    MaCaKham: Optional[str] = None
    NgayKham: Optional[date] = None
    SoLuongToiDa: Optional[int] = None
    SoLuongDaDat: Optional[int] = 0
    TrangThai: Optional[str] = None

class LichPhongKhamResponse(LichPhongKhamBase):
    class Config:
        from_attributes = True

# --- LichLamViec ---
class LichLamViecBase(BaseModel):
    MaLichLamViec: str
    MaBacSi: Optional[str] = None
    MaLichPhong: Optional[str] = None
    TrangThai: Optional[str] = None

class LichLamViecResponse(LichLamViecBase):
    class Config:
        from_attributes = True

# --- BangGiaKham ---
class BangGiaKhamBase(BaseModel):
    MaBangGia: str
    MaChuyenKhoa: Optional[str] = None
    TenDichVu: Optional[str] = None
    GiaKham: Optional[Decimal] = None
    TrangThai: bool

class BangGiaKhamResponse(BangGiaKhamBase):
    class Config:
        from_attributes = True

# --- DatLichKham ---
class DatLichKhamBase(BaseModel):
    MaDatLich: str
    MaBenhNhan: Optional[str] = None
    MaLichLamViec: Optional[str] = None
    MaBangGia: Optional[str] = None
    NgayDat: Optional[datetime] = None
    LyDoKham: Optional[str] = None
    TrangThai: Optional[str] = None
    LoaiDat: Optional[str] = None

class DatLichKhamResponse(DatLichKhamBase):
    class Config:
        from_attributes = True

# --- PhieuKham ---
class PhieuKhamBase(BaseModel):
    MaPhieuKham: str
    MaBenhNhan: Optional[str] = None
    MaBacSi: Optional[str] = None
    MaPhong: Optional[str] = None
    NgayKham: Optional[datetime] = None
    TrieuChung: Optional[str] = None
    ChanDoan: Optional[str] = None
    KetLuan: Optional[str] = None
    GhiChu: Optional[str] = None

class PhieuKhamResponse(PhieuKhamBase):
    class Config:
        from_attributes = True

# --- Thuoc ---
class ThuocBase(BaseModel):
    MaThuoc: str
    TenThuoc: Optional[str] = None
    DonViTinh: Optional[str] = None
    GiaThuoc: Optional[Decimal] = None
    CachDung: Optional[str] = None
    TrangThai: bool

class ThuocResponse(ThuocBase):
    class Config:
        from_attributes = True

# --- DonThuoc ---
class DonThuocBase(BaseModel):
    MaDonThuoc: str
    MaPhieuKham: Optional[str] = None
    NgayKe: Optional[datetime] = None
    GhiChu: Optional[str] = None

class DonThuocResponse(DonThuocBase):
    class Config:
        from_attributes = True

# --- Login ---
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    ma_tai_khoan: str
