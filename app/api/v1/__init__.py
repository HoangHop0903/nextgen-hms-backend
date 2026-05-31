from fastapi import APIRouter
from .auth import router as auth_router
from .patient_portal import router as patient_portal_router
from .doctor_portal import router as doctor_portal_router
from .staff_portal import router as staff_portal_router
from .admin_portal import router as admin_portal_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(patient_portal_router, prefix="/patient", tags=["Patient Portal"])
api_router.include_router(doctor_portal_router, prefix="/doctor", tags=["Doctor Portal"])
api_router.include_router(staff_portal_router, prefix="/staff", tags=["Staff Portal"])
api_router.include_router(admin_portal_router, prefix="/admin", tags=["Admin Portal"])
