# Privacy Policy

DeepSeek Balance Monitor is a local Windows desktop application.

## Data processed

The application processes:

- the DeepSeek API Key entered by the user;
- balance information returned by the DeepSeek API;
- local UI settings such as refresh interval, theme, window position, and auto-start preference.

## Network requests

The application connects to `https://api.deepseek.com/user/balance` to retrieve account balance information. The API Key is sent to DeepSeek in the HTTPS Authorization header for that request.

## Local storage

User settings and the encoded API Key are stored on the user's own computer at:

```text
%APPDATA%\DeepSeekMonitor\snapshot.json
```

The application does not upload this local configuration file to any server controlled by this project.

## Telemetry

This project does not include analytics, telemetry, advertising SDKs, or background tracking.

## Uninstalling

The installer uninstaller asks whether to delete local user configuration data. If users choose to keep it, `%APPDATA%\DeepSeekMonitor\snapshot.json` remains on the machine.
