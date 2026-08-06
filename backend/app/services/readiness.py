from app.db.session import check_database
from app.schemas.health import ReadinessResponse


def get_readiness() -> ReadinessResponse:
    database_ready = check_database()
    return ReadinessResponse(
        status="ready" if database_ready else "not_ready",
        database=database_ready,
        migrations_applied=True,
        initialized=True,
    )
