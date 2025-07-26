from fastapi import APIRouter

from axon.utils.health import service_status

router = APIRouter()


@router.get("/health", tags=["system"])
async def health():
    """Return the per-process service status."""
    # NOTE: expose service_status for each worker
    return service_status.__dict__
