from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow
from GtkHelper.GenerativeUI.EntryRow import EntryRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow
from src.backend.PluginManager.ActionCore import ActionCore

from .timezone_catalog import timezone_choices


DEFAULT_CITY = "London"
DEFAULT_TIMEZONE = "Europe/London"


def clock_text(now: datetime, use_24_hour: bool, show_date: bool) -> tuple[str, str]:
    """Return display-ready time and date strings for an aware datetime."""
    if use_24_hour:
        time_text = now.strftime("%H:%M")
    else:
        # %-I is not portable, so remove the leading zero ourselves.
        time_text = now.strftime("%I:%M %p").lstrip("0")

    date_text = now.strftime("%a %d %b") if show_date else ""
    return time_text, date_text


def use_24_hour_format(settings: dict) -> bool:
    """Read the explicit format, falling back to the legacy switch setting."""
    time_format = settings.get("time_format")
    if time_format in ("24h", "12h"):
        return time_format == "24h"
    return settings.get("use_24_hour", True)


def fit_font_size(text, preferred, minimum, available_width, measure_width):
    """Choose the largest font size whose measured text fits the key width."""
    if not text:
        return preferred

    for font_size in range(preferred, minimum - 1, -1):
        if measure_width(text, font_size) <= available_width:
            return font_size
    return minimum


class WorldClockAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self.allow_event_configuration = False
        self._last_rendered_minute = None

    def on_ready(self):
        self._render(force=True)

    def on_update(self):
        self._render(force=True)

    def on_tick(self):
        self._render()

    def _render(self, force=False):
        settings = self.get_settings()
        city = settings.get("city", DEFAULT_CITY).strip() or DEFAULT_CITY
        timezone_name = (
            settings.get("timezone", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
        )

        try:
            now = datetime.now(ZoneInfo(timezone_name))
        except (ZoneInfoNotFoundError, ValueError):
            self._last_rendered_minute = None
            self.set_top_label(city, font_size=12, update=False)
            self.set_center_label("Invalid", font_size=16, update=False)
            self.set_bottom_label("timezone", font_size=10)
            self.show_error()
            return

        minute_key = (timezone_name, now.year, now.month, now.day, now.hour, now.minute)
        if not force and minute_key == self._last_rendered_minute:
            return

        self._last_rendered_minute = minute_key
        self.hide_error()
        time_text, date_text = clock_text(
            now,
            use_24_hour=use_24_hour_format(settings),
            show_date=settings.get("show_date", True),
        )

        city_size = self._fitted_font_size(city, preferred=12, minimum=7)
        time_size = self._fitted_font_size(time_text, preferred=20, minimum=10)
        date_size = self._fitted_font_size(date_text, preferred=9, minimum=6)

        self.set_top_label(city, font_size=city_size, update=False)
        self.set_center_label(time_text, font_size=time_size, update=False)
        self.set_bottom_label(date_text, font_size=date_size)

    def _fitted_font_size(self, text, preferred, minimum):
        controller_input = self.get_input()
        key_width = controller_input.get_image_size()[0]
        # Leave room for the outline and a small margin on both sides.
        available_width = max(12, key_width - max(10, round(key_width * 0.14)))

        try:
            from src.backend.DeckManagement.Subclasses.KeyLabel import KeyLabel

            def measure_width(value, font_size):
                try:
                    label = KeyLabel(
                        controller_input=controller_input,
                        text=value,
                        font_size=font_size,
                    )
                    left, _, right, _ = label.get_font().getbbox(value)
                    return right - left
                except Exception:
                    return len(value) * font_size * 0.6
        except Exception:
            # Safe fallback for unusual font setups. Most sans-serif labels are
            # close to 0.6 em per character.
            measure_width = lambda value, font_size: len(value) * font_size * 0.6

        return fit_font_size(
            text,
            preferred=preferred,
            minimum=minimum,
            available_width=available_width,
            measure_width=measure_width,
        )

    def get_config_rows(self):
        # The sidebar can ask for rows again when revisiting an action. Generative
        # UI objects register themselves with ActionCore, so only create them once.
        if self.generative_ui_objects:
            return []

        self.city_row = EntryRow(
            action_core=self,
            var_name="city",
            default_value=DEFAULT_CITY,
            title="actions.world_clock.city",
            on_change=self._on_setting_changed,
        )
        self.timezone_row = ComboRow(
            action_core=self,
            var_name="timezone",
            default_value=DEFAULT_TIMEZONE,
            items=[
                SimpleComboRowItem(value=zone, label=label)
                for zone, label in timezone_choices()
            ],
            title="actions.world_clock.timezone",
            enable_search=True,
            on_change=self._on_setting_changed,
        )
        legacy_format = "24h" if self.get_settings().get("use_24_hour", True) else "12h"
        self.hour_format_row = ComboRow(
            action_core=self,
            var_name="time_format",
            default_value=legacy_format,
            items=[
                SimpleComboRowItem(value="24h", label="24-hour — 23:45"),
                SimpleComboRowItem(value="12h", label="12-hour — 11:45 PM"),
            ],
            title="actions.world_clock.time_format",
            on_change=self._on_setting_changed,
        )
        self.date_row = SwitchRow(
            action_core=self,
            var_name="show_date",
            default_value=True,
            title="actions.world_clock.show_date",
            on_change=self._on_setting_changed,
        )
        # Generative rows auto-register and are added by the beta.16 sidebar.
        return []

    def _on_setting_changed(self, widget, new_value, old_value):
        self._render(force=True)
