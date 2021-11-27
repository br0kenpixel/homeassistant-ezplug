# EZPlug for Home Assistant
This custom integration allows you to detect and control your EZVIZ Smart Plugs.
The built-in EZVIZ integration for Home Assistant does not supprt smart plugs, so I decided to make my own integration.

Testted with: T30 plug

Notes:
- Turning the plugs on/off is quick
- Updating plug on/off state takes a while (minute or two) - I could make this faster, but since it's using a cloud API, you can't just spam it every X seconds
- Internet access required

⚠️You should not consider this integration stable. It's just something that I quickly put together, so don't expect it to be good, stable or fast

⚠️This integration uses the EZVIZ Cloud API, so it will not work offline!

## Setup
1. Clone this repo into your Home Assistant's `config/custom_components` directory (`git clone br0kenpixel/homeassistant-ezplug`). If you don't have a `custom_components` directory, create it.
2. Add the following to your Home Assistant configuration file:
```
switch:
  - platform: ezplug
    email: "your_ezviz_account@email.com"
    password: "your_password"
    id: "ezplug"
```
3. Restart your Home Assistant instance.
Your EZVIZ Smart Plugs should show up in Home Assistant.
