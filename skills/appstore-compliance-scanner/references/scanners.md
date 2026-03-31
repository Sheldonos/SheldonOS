# Greenlight Scanners

This document provides a detailed breakdown of the scanners included in the `greenlight` tool.

## Preflight

The `preflight` command is the main command and runs all of the following scanners in parallel for a comprehensive analysis.

## Scanners Included in Preflight

| Scanner | Checks |
| --- | --- |
| **metadata** | Scans `app.json` or `Info.plist` for name, version, bundle ID format, icon, privacy policy URL, and purpose strings. |
| **codescan** | Performs a static analysis of the source code for over 30 common issues, including private API usage, hardcoded secrets, payment violations, missing ATT, social login, and placeholder content. |
| **privacy** | Validates the `PrivacyInfo.xcprivacy` file for completeness, checks for Required Reason APIs, and verifies the implementation of the App Tracking Transparency (ATT) framework against any tracking SDKs. |
| **ipa** | Inspects the compiled IPA binary for `Info.plist` keys, launch storyboard, app icons, app size, and privacy manifests of embedded frameworks. |

## Standalone Scanners

Each of the scanners included in `preflight` can also be run as a standalone command for more targeted analysis.

*   `greenlight codescan [path]`: Runs only the code pattern scan.
*   `greenlight privacy [path]`: Runs only the privacy manifest validator.
*   `greenlight ipa <path.ipa>`: Runs only the binary inspector.

## App Store Connect Scanner

In addition to the local scanners, Greenlight can also perform API-based checks against your app's metadata in App Store Connect.

*   `greenlight scan --app-id <ID>`: Runs checks for metadata completeness, screenshot verification, build processing status, age rating, and encryption compliance.

This command requires authentication with App Store Connect. You can set up authentication using the `greenlight auth setup` and `greenlight auth login` commands.
