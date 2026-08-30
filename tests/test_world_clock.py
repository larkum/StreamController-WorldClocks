import importlib.util
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# Stub application-only imports so the pure formatting helper can be tested
# without installing StreamController or GTK.
module_names = [
    "GtkHelper",
    "GtkHelper.ComboRow",
    "GtkHelper.GenerativeUI",
    "GtkHelper.GenerativeUI.ComboRow",
    "GtkHelper.GenerativeUI.EntryRow",
    "GtkHelper.GenerativeUI.SwitchRow",
    "src",
    "src.backend",
    "src.backend.PluginManager",
    "src.backend.PluginManager.ActionCore",
    "actions",
]
for module_name in module_names:
    sys.modules[module_name] = types.ModuleType(module_name)

class DummyActionCore:
    def __init__(self, *args, **kwargs):
        self.generative_ui_objects = []
        self.settings = {}

    def get_settings(self):
        return self.settings

    def set_settings(self, settings):
        self.settings = settings


class DummyGenerativeRow:
    def __init__(self, action_core, var_name, default_value, **kwargs):
        self.var_name = var_name
        self.kwargs = kwargs
        action_core.generative_ui_objects.append(self)


class DummyComboItem:
    def __init__(self, value, label):
        self.value = value
        self.label = label


sys.modules["GtkHelper.ComboRow"].SimpleComboRowItem = DummyComboItem
sys.modules["GtkHelper.GenerativeUI.ComboRow"].ComboRow = DummyGenerativeRow
sys.modules["GtkHelper.GenerativeUI.EntryRow"].EntryRow = DummyGenerativeRow
sys.modules["GtkHelper.GenerativeUI.SwitchRow"].SwitchRow = DummyGenerativeRow
sys.modules["src.backend.PluginManager.ActionCore"].ActionCore = DummyActionCore

actions_path = Path(__file__).parents[1] / "actions"
sys.modules["actions"].__path__ = [str(actions_path)]

catalog_path = actions_path / "timezone_catalog.py"
catalog_spec = importlib.util.spec_from_file_location(
    "actions.timezone_catalog", catalog_path
)
timezone_catalog = importlib.util.module_from_spec(catalog_spec)
sys.modules["actions.timezone_catalog"] = timezone_catalog
catalog_spec.loader.exec_module(timezone_catalog)

action_path = actions_path / "world_clock.py"
spec = importlib.util.spec_from_file_location("actions.world_clock", action_path)
world_clock = importlib.util.module_from_spec(spec)
sys.modules["actions.world_clock"] = world_clock
spec.loader.exec_module(world_clock)


class ClockTextTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 30, 9, 5, tzinfo=ZoneInfo("Europe/London"))

    def test_24_hour_time_and_date(self):
        self.assertEqual(
            world_clock.clock_text(self.now, True, True),
            ("09:05", "Sun 30 Aug"),
        )

    def test_12_hour_time_without_date(self):
        self.assertEqual(
            world_clock.clock_text(self.now, False, False),
            ("9:05 AM", ""),
        )

    def test_timezone_conversion_uses_zoneinfo(self):
        new_york = self.now.astimezone(ZoneInfo("America/New_York"))
        self.assertEqual(world_clock.clock_text(new_york, True, False)[0], "04:05")

    def test_explicit_time_format_is_unambiguous(self):
        self.assertTrue(world_clock.use_24_hour_format({"time_format": "24h"}))
        self.assertFalse(world_clock.use_24_hour_format({"time_format": "12h"}))

    def test_legacy_time_format_is_preserved(self):
        self.assertFalse(world_clock.use_24_hour_format({"use_24_hour": False}))
        self.assertTrue(world_clock.use_24_hour_format({"use_24_hour": True}))

    def test_font_size_stays_preferred_when_text_fits(self):
        size = world_clock.fit_font_size(
            "London", 12, 7, 80, lambda text, font_size: len(text) * font_size
        )
        self.assertEqual(size, 12)

    def test_font_size_reduces_until_text_fits(self):
        size = world_clock.fit_font_size(
            "Los Angeles", 12, 7, 88, lambda text, font_size: len(text) * font_size
        )
        self.assertEqual(size, 8)

    def test_font_size_never_drops_below_minimum(self):
        size = world_clock.fit_font_size(
            "A very long city name", 12, 7, 10, lambda text, font_size: 999
        )
        self.assertEqual(size, 7)


class ConfigurationTests(unittest.TestCase):
    def test_configuration_rows_are_created_once(self):
        action = world_clock.WorldClockAction()

        self.assertEqual(action.get_config_rows(), [])
        self.assertEqual(
            [row.var_name for row in action.generative_ui_objects],
            ["city", "timezone", "time_format", "show_date"],
        )

        action.get_config_rows()
        self.assertEqual(len(action.generative_ui_objects), 4)

    def test_timezone_picker_is_searchable(self):
        action = world_clock.WorldClockAction()
        action.get_config_rows()

        timezone_row = action.generative_ui_objects[1]
        self.assertTrue(timezone_row.kwargs["enable_search"])

    def test_texas_search_choices_cover_both_timezones(self):
        texas_choices = {
            zone
            for zone, label in timezone_catalog.timezone_choices()
            if "Texas" in label
        }
        self.assertEqual(texas_choices, {"America/Chicago", "America/Denver"})

    def test_catalog_is_searchable_by_country_city_and_state(self):
        choices = timezone_catalog.timezone_choices()

        def zones_matching(term):
            return {zone for zone, label in choices if term.casefold() in label.casefold()}

        self.assertIn("Asia/Kolkata", zones_matching("India"))
        self.assertIn("Asia/Kolkata", zones_matching("Mumbai"))
        self.assertIn("America/Los_Angeles", zones_matching("California"))
        self.assertIn("Europe/Berlin", zones_matching("Germany"))

    def test_every_normal_system_timezone_is_available(self):
        choice_zones = {zone for zone, _ in timezone_catalog.timezone_choices()}
        expected = {
            zone
            for zone in timezone_catalog.available_timezones()
            if zone not in timezone_catalog.EXCLUDED_NAMES
            and not zone.startswith(timezone_catalog.EXCLUDED_PREFIXES)
        }
        self.assertTrue(expected.issubset(choice_zones))


if __name__ == "__main__":
    unittest.main()
