[![Donate](https://img.shields.io/badge/donate-Coffee-yellow.svg)](https://www.buymeacoffee.com/renierm)
![Upload Python Package](https://github.com/RenierM26/pyUbersolar/workflows/Upload%20Python%20Package/badge.svg)

Library to control UberSolar UberSmart devices.

## Command line interface

The package ships with a simple CLI that can scan for nearby UberSolar devices and run a few built-in actions for testing.

1. Install the package: `pip install PyUbersolar`
2. Run the CLI module: `python -m pyubersolar [options]`

If you omit `--address`, the command scans for all discoverable devices and prints their status. Provide an address to target a specific device (use the address shown in the discovery output).

### Options

- `--address <address>` – Bluetooth address (MAC or UUID on macOS) of the device to connect to.
- `--switch <hex>` – Send a raw switch payload (for example `0600000002`). This toggles the device switches after connecting.
- `--wifiap` – Enable the Wi-Fi AP mode on the device.
- `--time` – Set the device clock to the current system time.
- `-d`, `--debug` – Enable verbose debug logging.

All actions that modify the device (`--switch`, `--wifiap`, `--time`) require that you also provide `--address`.

Example: `python -m pyubersolar --address AA:BB:CC:DD:EE:FF --time --debug`
