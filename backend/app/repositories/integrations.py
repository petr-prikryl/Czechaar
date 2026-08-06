from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration import Integration


class IntegrationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Integration]:
        statement = select(Integration).order_by(Integration.source_type, Integration.name)
        return list(self.session.scalars(statement))

    def get(self, integration_id: int) -> Integration | None:
        return self.session.get(Integration, integration_id)

    def add(self, integration: Integration) -> Integration:
        self.session.add(integration)
        self.session.commit()
        self.session.refresh(integration)
        return integration

    def commit(self, integration: Integration) -> Integration:
        self.session.add(integration)
        self.session.commit()
        self.session.refresh(integration)
        return integration

    def delete(self, integration: Integration) -> None:
        self.session.delete(integration)
        self.session.commit()
