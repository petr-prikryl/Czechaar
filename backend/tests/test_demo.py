from __future__ import annotations

from sqlalchemy import delete, select

from app.db.session import SessionLocal, initialize_database
from app.models.audio import AudioStream
from app.models.enums import MediaType, ScanState
from app.models.ignored import IgnoredItem
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.models.scan import ScanRun, ScanRunItem
from app.models.setting import ApplicationSetting
from app.models.sync import LibrarySyncRun
from app.services.demo import DEMO_SEED_KEY, DEMO_SEED_VERSION, seed_demo_data


def _clear_demo_data() -> None:
    with SessionLocal() as session:
        demo_integrations = session.scalars(
            select(Integration).where(Integration.name.in_(["Demo Radarr", "Demo Sonarr"]))
        ).all()
        integration_ids = [integration.id for integration in demo_integrations]
        if integration_ids:
            file_ids = session.scalars(
                select(MediaFile.id).where(MediaFile.integration_id.in_(integration_ids))
            ).all()
            item_ids = session.scalars(
                select(MediaItem.id).where(MediaItem.integration_id.in_(integration_ids))
            ).all()
            if file_ids:
                session.execute(delete(AudioStream).where(AudioStream.media_file_id.in_(file_ids)))
                session.execute(delete(ScanRunItem).where(ScanRunItem.media_file_id.in_(file_ids)))
                session.execute(
                    delete(MediaItemFileLink).where(MediaItemFileLink.media_file_id.in_(file_ids))
                )
                session.execute(delete(MediaFile).where(MediaFile.id.in_(file_ids)))
            if item_ids:
                session.execute(delete(IgnoredItem).where(IgnoredItem.object_id.in_(item_ids)))
                session.execute(delete(MediaItem).where(MediaItem.id.in_(item_ids)))
            session.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        session.execute(delete(PathMapping).where(PathMapping.description.like("Demo %")))
        session.execute(delete(AllowedMediaRoot).where(AllowedMediaRoot.description.like("Demo %")))
        session.execute(delete(ScanRun))
        session.execute(delete(LibrarySyncRun))
        session.execute(delete(ApplicationSetting).where(ApplicationSetting.key == DEMO_SEED_KEY))
        session.commit()


def test_demo_data_seed_is_idempotent_and_representative() -> None:
    initialize_database()
    _clear_demo_data()
    try:
        seed_demo_data()
        seed_demo_data()

        with SessionLocal() as session:
            integrations = session.scalars(
                select(Integration).where(Integration.name.in_(["Demo Radarr", "Demo Sonarr"]))
            ).all()
            missing_file_count = session.scalar(
                select(MediaFile).where(MediaFile.scan_state == ScanState.CZECH_AUDIO_MISSING)
            )
            episodes = session.scalars(
                select(MediaItem).where(MediaItem.media_type == MediaType.EPISODE)
            ).all()
            marker = session.get(ApplicationSetting, DEMO_SEED_KEY)

            assert len(integrations) == 2
            assert missing_file_count is not None
            assert len(episodes) >= 4
            assert marker is not None
            assert marker.value == DEMO_SEED_VERSION
    finally:
        _clear_demo_data()
