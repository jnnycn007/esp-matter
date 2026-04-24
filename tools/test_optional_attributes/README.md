# Test Optional Attributes Suite

This directory contains test scripts to verify the presence and readability of optional attributes in various Matter clusters which are migrated to be code driven.

## Prerequisites

1.  **Environment**: You need to be in a Matter build environment (e.g., `connectedhomeip` SDK environment) where the python controller and testing libraries are built and available.
    ```bash
    # Example setup in connectedhomeip
    source ./scripts/activate.sh
    ```
2.  **Device**: A Matter device must be commissioned and reachable.

## Usage

1. **Build the Example App**:
    
    The example application with all clusters enabled is located at `examples/test_apps/test_optional_attributes`.
    
    ```bash
    cd examples/test_apps/test_optional_attributes
    idf.py build
    idf.py flash monitor
    ```

2. **Build Python Environment**:

    The test requires the Matter Python controller and test framework. You can build the environment using the installation script:

    ```bash
    ./install.sh --build-python
    ```
    
    This will create a virtual python environment at `connectedhomeip/connectedhomeip/out/py_env`.

3. **Run the Test**:

    Activate the Python environment and run the test. Below is an example command for BLE-WiFi commissioning:

    ```bash
    source connectedhomeip/connectedhomeip/out/py_env/bin/activate
    python3 tools/test_optional_attributes/test_optional_attributes_framework.py \
        -n 1 \
        --commissioning-method ble-wifi \
        --wifi-ssid <WIFI_SSID> \
        --wifi-passphrase <WIFI_PASSWORD> \
        --passcode 20202021 \
        --discriminator 3840 \
        --paa-trust-store-path connectedhomeip/connectedhomeip/credentials/development/paa-root-certs
    ```

    Note: Adjust passcode/discriminator as per your device configuration (default for `test_optional_attributes` is usually `20202021`/`3840`).

## Tested Clusters

The scripts check for optional attributes in:
-   Basic Information
-   Boolean State Configuration
-   Descriptor
-   Electrical Energy Measurement
-   Electrical Power Measurement
-   Ethernet Network Diagnostics
-   General Diagnostics
-   Occupancy Sensing
-   Resource Monitoring
-   Software Diagnostics
-   Time Synchronization
-   WiFi Network Diagnostics
