from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    window: str = "#0D1015"
    surface: str = "#14181E"
    surface_hover: str = "#1A1F27"
    field: str = "#10141A"
    border: str = "#343B46"
    border_focus: str = "#6B7482"
    text: str = "#F2F0ED"
    text_muted: str = "#9CA3AF"
    text_faint: str = "#747C89"
    accent: str = "#F2554A"
    accent_hover: str = "#D9473E"
    accent_pressed: str = "#C43E36"
    success: str = "#3FA47C"
    danger: str = "#EF6461"


COLORS = Palette()

FONT_FAMILY = "Segoe UI"
MONOSPACE_FONT_FAMILY = "Consolas"

WINDOW_SIZE = "1180x720"
WINDOW_MIN_WIDTH = 920
WINDOW_MIN_HEIGHT = 600
SIDEBAR_WIDTH = 350
PANEL_RADIUS = 14
CONTROL_RADIUS = 9
