from typing import Dict, Any, Optional, List
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from aphrodite_logging import get_logger
from .base_processor import BaseBadgeProcessor
from .types import PosterResult
from .database_service import badge_settings_service
from .renderers import UnifiedBadgeRenderer
from app.core.database import async_session_factory

class V2FlagBadgeProcessor(BaseBadgeProcessor):
    """Pure V2 flag badge processor - no V1 dependencies"""

    def __init__(self):
        super().__init__("flag")
        self.logger = get_logger("aphrodite.badge.flag.v2", service="badge")
        self.renderer = UnifiedBadgeRenderer()

    async def process_single(
        self, 
        poster_path: str, 
        output_path: Optional[str] = None,
        use_demo_data: bool = False,
        db_session: Optional[AsyncSession] = None,
        jellyfin_id: Optional[str] = None,
        flag_name: Optional[str] = "mexico"  # Puedes cambiar el valor por defecto
    ) -> PosterResult:
        """Process a single poster with flag badge using pure V2 system"""
        try:
            self.logger.info(f"🚩 [V2 FLAG] PROCESSOR STARTED for: {poster_path} (flag: {flag_name})")

            # Carga la configuración de badge
            settings = await self._load_v2_settings(db_session)
            if not settings:
                self.logger.error("❌ [V2 FLAG] Failed to load settings from PostgreSQL")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error="Failed to load V2 flag badge settings"
                )

            self.logger.info("✅ [V2 FLAG] Settings loaded from PostgreSQL")

            # Determina la ruta al PNG de la bandera
            badge_dir = settings.get("ImageBadges", {}).get("codec_image_directory", "/app/assets/images/flag")
            badge_path = f"{badge_dir}/flag_{flag_name}.png"

            # Verifica existencia
            if not Path(badge_path).exists():
                self.logger.error(f"[V2 FLAG] Badge PNG not found: {badge_path}")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error=f"Flag badge PNG not found: {badge_path}"
                )

            # Crea el badge visual usando el renderer
            badge = self.renderer.create_image_badge(
                badge_path,
                settings,
                "flag"
            )

            if not badge:
                self.logger.error(f"❌ [V2 FLAG] Badge creation failed")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error="V2 flag badge creation failed"
                )

            final_output_path = output_path or f"/app/api/static/preview/{Path(poster_path).name}"

            success = self.renderer.apply_badge_to_poster(
                poster_path, badge, settings, final_output_path
            )

            if success:
                self.logger.info(f"✅ [V2 FLAG] Badge applied successfully: {final_output_path}")
                return PosterResult(
                    source_path=poster_path,
                    output_path=final_output_path,
                    applied_badges=[f"flag_{flag_name}"],
                    success=True
                )
            else:
                self.logger.error(f"❌ [V2 FLAG] Badge application failed")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error="V2 flag badge application failed"
                )

        except Exception as e:
            self.logger.error(f"🚨 [V2 FLAG] PROCESSOR EXCEPTION: {e}", exc_info=True)
            return PosterResult(
                source_path=poster_path,
                success=False,
                error=f"V2 flag processor error: {str(e)}"
            )

    async def process_bulk(
        self,
        poster_paths: List[str],
        output_directory: Optional[str] = None,
        use_demo_data: bool = False,
        db_session: Optional[AsyncSession] = None,
        flag_name: Optional[str] = "mexico"
    ) -> List[PosterResult]:
        """Process multiple posters with V2 flag badges"""
        results = []

        self.logger.info(f"🚩 [V2 FLAG] BULK PROCESSING {len(poster_paths)} posters")

        for i, poster_path in enumerate(poster_paths):
            self.logger.debug(f"🚩 [V2 FLAG] Processing {i+1}/{len(poster_paths)}: {poster_path}")

            # Calcula el output path para bulk
            output_path = None
            if output_directory:
                poster_name = Path(poster_path).name
                output_path = str(Path(output_directory) / poster_name)

            # Procesa el poster
            result = await self.process_single(
                poster_path,
                output_path,
                use_demo_data,
                db_session,
                None,
                flag_name
            )
            results.append(result)

            if (i + 1) % 10 == 0:
                self.logger.info(f"🚩 [V2 FLAG] Processed {i+1}/{len(poster_paths)} badges")

        successful = sum(1 for r in results if r.success)
        self.logger.info(f"🚩 [V2 FLAG] BULK COMPLETED: {successful}/{len(results)} successful")

        return results

    async def _load_v2_settings(self, db_session: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """Load flag badge settings (puedes personalizar si quieres base de datos o defaults)"""
        try:
            self.logger.debug("🗄️ [V2 FLAG] Loading settings from PostgreSQL")

            # Usa settings de la base (o los defaults)
            if db_session:
                # Si usas PostgreSQL para settings de bandera, agrégalo aquí (ejemplo):
                # settings = await badge_settings_service.get_flag_settings(db_session, force_reload=True)
                # if settings:
                #     return settings
                pass  # Por ahora, solo default

            # Por ahora, solo settings por defecto:
            return self._get_v2_default_settings()

        except Exception as e:
            self.logger.error(f"❌ [V2 FLAG] Error loading settings: {e}", exc_info=True)
            return self._get_v2_default_settings()

    def _get_v2_default_settings(self) -> Dict[str, Any]:
        """Get V2 default flag badge settings"""
        return {
            "General": {
                "general_badge_size": 100,
                "general_text_padding": 12,
                "use_dynamic_sizing": True,
                "general_badge_position": "bottom-left",  # 👈 aquí defines la posición por defecto
                "general_edge_padding": 30
            },
            "ImageBadges": {
                "enable_image_badges": True,
                "fallback_to_text": False,
                "image_padding": 10,
                "codec_image_directory": "images/flag"  # Carpeta para tus PNG de banderas
            }
        }
