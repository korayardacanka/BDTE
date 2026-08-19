from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Servisin ayakta olduğunu doğrulamak için basit sağlık kontrolü."""
    return {"status": "ok"}
