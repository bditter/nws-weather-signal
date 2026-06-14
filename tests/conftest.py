"""Test path setup."""

import sys
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).parents[1]))

# Unit-test the pure normalization module without requiring Home Assistant.
package = ModuleType("custom_components.nws_weather_signal")
package.__path__ = [
    str(Path(__file__).parents[1] / "custom_components" / "nws_weather_signal")
]
sys.modules["custom_components.nws_weather_signal"] = package
