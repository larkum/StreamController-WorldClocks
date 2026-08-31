# World Clocks for StreamController

![World Clocks banner](store/Thumbnail.png)

An offline world-clock action for StreamController 1.5.0-beta.16.

## Install locally

Copy this entire folder into StreamController's plugin directory, then restart
StreamController. For the Flatpak build, the usual destination is:

```text
~/.var/app/com.core447.StreamController/data/plugins/com_larkum_WorldClocks
```

Add **World Clocks → World Clock** to a key. In the key's configuration, set a
short city label and search by country, major city, US state, region, or IANA
timezone. For example, searching for `Texas` offers Central Time for most of
the state and Mountain Time for the El Paso area. Searching for `Mumbai` shows
that it uses `Asia/Kolkata`. The complete system timezone catalog remains
available.

The plugin uses Python's standard `zoneinfo` module, so it needs no network
connection and automatically follows daylight-saving changes from the system's
timezone database.

## Features

- Search by country, city, US state, region, or IANA timezone
- Includes major cities worldwide and every timezone installed on the system
- Automatic daylight-saving adjustment
- Explicit 12-hour and 24-hour time formats
- Optional date display
- Automatic label sizing so longer city names fit the key

## Requirements

- StreamController 1.5.0-beta.16 or newer
- A system timezone database available to Python's standard `zoneinfo` module

No additional Python packages or network services are required.

## License

MIT
