---
name: greenlight
description: Pre-submission compliance scanner for the Apple App Store. Use this skill to scan iOS, macOS, tvOS, watchOS, or visionOS app code (Swift, Objective-C, React Native, Expo) to identify potential App Store rejection risks before submission. Triggers on tasks involving app review preparation, compliance checking, App Store submission readiness, or when a user asks about App Store guidelines.
---

# Greenlight — App Store Pre-Submission Scanner

You are an expert at preparing iOS apps for App Store submission. You have access to the `greenlight` CLI, which runs automated compliance checks. Your job is to run the checks, interpret the results, fix every issue, and re-run until the app passes with GREENLIT status.

## Step 1: Install Greenlight

If `greenlight` is not already installed, you can install it using one of the following methods. If you are unsure, you can check by running `greenlight --version`.

```shell
# Homebrew (macOS)
brew install revylai/tap/greenlight

# Go
go install github.com/RevylAI/greenlight/cmd/greenlight@latest

# Build from source
git clone https://github.com/RevylAI/greenlight.git
cd greenlight && make build
# The binary will be at: build/greenlight
```

## Step 2: Run the Scan

Run `greenlight preflight` on the project root. This single command runs all scanners in parallel, entirely offline, and requires no account.

```shell
greenlight preflight .
```

If the user has a built IPA file, include it for binary analysis:

```shell
greenlight preflight . --ipa /path/to/build.ipa
```

For a detailed breakdown of the different scanners and their checks, you can read the reference file at `/home/ubuntu/skills/greenlight/references/scanners.md`.

## Step 3: Analyze the Output and Fix Issues

Each finding from the scan includes a severity level, a reference to the relevant Apple guideline, the file location of the issue, and a suggestion for a fix. Address the findings in order of severity:

1.  **CRITICAL**: These issues will almost certainly lead to rejection. They must be fixed.
2.  **WARN**: These issues represent a high risk of rejection and should be fixed.
3.  **INFO**: These are best-practice recommendations that you should consider addressing.

When fixing issues, refer to the following common solutions:

*   **Hardcoded Secrets**: Move secrets to environment variables.
*   **External Payments for Digital Goods**: Use Apple's In-App Purchase (IAP) system for digital content. External payment methods are only permissible for physical goods.
*   **Social Login Without Sign in with Apple**: Implement Sign in with Apple alongside other social login options.
*   **Account Creation Without Deletion**: Ensure your app provides a clear and accessible option for users to delete their accounts.
*   **Platform References**: Remove any mentions of competing platforms like "Android," "Google Play," or "Windows."
*   **Placeholder Content**: Replace all placeholder text (e.g., "Lorem ipsum," "Coming soon") with final content.
*   **Vague Purpose Strings**: Rewrite permission request strings to be specific and clear about why the app needs the requested permission.
*   **Hardcoded IPv4 Addresses**: Replace IP addresses with hostnames.
*   **Insecure HTTP URLs**: Use HTTPS for all network connections.

## Step 4: Re-run and Repeat

After you have addressed the issues, re-run the scan to verify that they have been resolved:

```shell
greenlight preflight .
```

Continue this process of scanning and fixing until the output shows a **GREENLIT** status, indicating that there are no remaining CRITICAL findings. Be aware that some fixes may introduce new issues, so it is important to re-run the scan frequently.

## Other Useful Commands

*   `greenlight codescan .`: Run only the code scanner.
*   `greenlight privacy .`: Run only the privacy manifest scanner.
*   `greenlight ipa /path/to/build.ipa`: Inspect a binary file.
*   `greenlight scan --app-id <ID>`: Perform checks against your app in App Store Connect (requires authentication).
*   `greenlight guidelines search "privacy"`: Search Apple's guidelines.
