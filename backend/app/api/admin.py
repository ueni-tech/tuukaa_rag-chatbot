from fastapi import APIRouter

from ..core.config import settings
from ..models.schemas import TenantInfo, TenantListResponse


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants() -> TenantListResponse:
    items = [
        TenantInfo(name=name, key=key)
        for name, key in settings.embed_api_keys_map.items()
    ]
    return TenantListResponse(tenants=items)
