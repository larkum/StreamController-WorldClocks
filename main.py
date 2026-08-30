from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.PluginManager.PluginBase import PluginBase

from .actions.world_clock import WorldClockAction


class WorldClocksPlugin(PluginBase):
    def __init__(self):
        super().__init__(use_legacy_locale=False)

        self.add_action_holder(
            ActionHolder(
                plugin_base=self,
                action_core=WorldClockAction,
                action_id_suffix="WorldClock",
                action_name=self.locale_manager.get("actions.world_clock.name"),
                description="Displays the current time and optional date for a configured world timezone.",
                requirements="A valid IANA timezone name from the system timezone database.",
                settings_schema={
                    "city": {
                        "type": "string",
                        "description": "Short label shown at the top of the key.",
                        "default": "London",
                        "example": "Tokyo",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone used for the clock.",
                        "default": "Europe/London",
                        "example": "Asia/Tokyo",
                        "required": True,
                    },
                    "time_format": {
                        "type": "string",
                        "description": "Select 24-hour or 12-hour time.",
                        "default": "24h",
                        "values": ["24h", "12h"],
                    },
                    "show_date": {
                        "type": "boolean",
                        "description": "Show the abbreviated day and date at the bottom.",
                        "default": True,
                    },
                },
                action_support={
                    Input.Key: ActionInputSupport.SUPPORTED,
                    Input.Dial: ActionInputSupport.UNSUPPORTED,
                    Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
                },
            )
        )

        self.register(
            plugin_name="World Clocks",
            github_repo="https://github.com/larkum/StreamController-WorldClocks",
            plugin_version="0.1.0",
            app_version="1.5.0-beta.16",
        )
