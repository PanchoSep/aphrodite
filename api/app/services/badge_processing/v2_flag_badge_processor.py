from typing import Optional, Dict, Any
from pathlib import Path
from aphrodite_logging import get_logger
from .base_processor import BaseBadgeProcessor
from .types import PosterResult
from .renderers import UnifiedBadgeRenderer

class V2FlagBadgeProcessor(BaseBadgeProcessor):
    """Processor V2 para añadir una bandera manual como badge en el póster"""

    def __init__(self):
        super().__init__("flag")
        self.logger = get_logger("aphrodite.badge.flag.v2", service="badge")
        self.renderer = UnifiedBadgeRenderer()

    async def process_single(
        self,
        poster_path: str,
        output_path: Optional[str] = None,
        flag_name: str = "mexico",    # Puedes hacerlo dinámico según la selección del usuario
    ) -> PosterResult:
        try:
            self.logger.info(f"[V2 FLAG] PROCESSOR STARTED for: {poster_path} (flag: {flag_name})")
            
            # Define el path al asset de la bandera
            badge_path = f"images/flag/flag_{flag_name}.png"  # Ajusta el path según tu estructura real

            # Opcional: Verifica que el archivo exista
            if not Path(badge_path).exists():
                self.logger.error(f"[V2 FLAG] Badge PNG not found: {badge_path}")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error=f"Flag badge PNG not found: {badge_path}"
                )

            # Crea el badge visual usando el renderer
            badge_settings = {
                "General": {
                    "general_badge_position": "bottom-left",  # Posición abajo a la izquierda
                    "general_edge_padding": 30                # Margen desde el borde
                }
                # Puedes agregar más settings si necesitas
            }

            badge = self.renderer.create_image_badge(
                badge_path,
                badge_settings,
                "flag"
            )

            if not badge:
                self.logger.error(f"[V2 FLAG] Badge creation failed")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error="V2 flag badge creation failed"
                )

            final_output_path = output_path or f"/app/api/static/preview/{Path(poster_path).name}"

            success = self.renderer.apply_badge_to_poster(
                poster_path, badge, badge_settings, final_output_path
            )

            if success:
                self.logger.info(f"[V2 FLAG] Badge applied successfully: {final_output_path}")
                return PosterResult(
                    source_path=poster_path,
                    output_path=final_output_path,
                    applied_badges=[f"flag_{flag_name}"],
                    success=True
                )
            else:
                self.logger.error(f"[V2 FLAG] Badge application failed")
                return PosterResult(
                    source_path=poster_path,
                    success=False,
                    error="V2 flag badge application failed"
                )

        except Exception as e:
            self.logger.error(f"[V2 FLAG] Exception: {e}")
            return PosterResult(
                source_path=poster_path,
                success=False,
                error=str(e)
            )
