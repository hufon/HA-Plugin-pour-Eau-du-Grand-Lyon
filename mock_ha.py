import sys
from unittest.mock import MagicMock

class MockModule(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

sys.modules['homeassistant'] = MockModule()
sys.modules['homeassistant.config_entries'] = MockModule()
sys.modules['homeassistant.core'] = MockModule()
sys.modules['homeassistant.helpers'] = MockModule()
sys.modules['homeassistant.helpers.typing'] = MockModule()
sys.modules['homeassistant.const'] = MockModule()
sys.modules['homeassistant.helpers.config_validation'] = MockModule()
sys.modules['homeassistant.helpers.storage'] = MockModule()
sys.modules['homeassistant.helpers.update_coordinator'] = MockModule()
sys.modules['homeassistant.util'] = MockModule()
sys.modules['homeassistant.components'] = MockModule()
sys.modules['homeassistant.components.sensor'] = MockModule()
sys.modules['homeassistant.components.binary_sensor'] = MockModule()
sys.modules['homeassistant.components.repairs'] = MockModule()

import voluptuous as vol
sys.modules['voluptuous'] = vol

import aiohttp
sys.modules['aiohttp'] = aiohttp

sys.path.append('custom_components')

try:
    import eau_grand_lyon.config_flow
    print("Config flow loaded successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
