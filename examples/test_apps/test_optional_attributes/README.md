# Optional Attributes Test Application

This example application creates a Matter node with multiple clusters on the root endpoint, each with all their optional attributes enabled. It serves as the device-side companion to the optional attributes test framework.

## Overview

The application:
- Creates a Matter Root Node on endpoint 0
- Adds optional attributes to existing clusters (Basic Information, General Diagnostics)
- Creates additional clusters (Boolean State Configuration, Electrical Energy Measurement, Electrical Power Measurement, Ethernet Network Diagnostics, Occupancy Sensing, HEPA Filter Monitoring, Software Diagnostics, Time Synchronization, WiFi Network Diagnostics) with their optional attributes enabled
- Enables the Matter console shell for diagnostics and attribute inspection

## Hardware Required

ESP32 board.

## Build and Flash

```bash
cd examples/test_apps/test_optional_attributes
idf.py set-target <target>
idf.py build flash monitor
```

## Configuration

The key sdkconfig option for this example is:
- `CONFIG_ESP_MATTER_ENABLE_OPTIONAL_ATTRIBUTES=y` — enables the optional attribute helper APIs

## Running Tests

This application is meant to be used with the optional attributes test framework. See [Optional Attributes Test Suite](../../../tools/test_optional_attributes/README.md) for instructions on commissioning the device and running the test scripts.
