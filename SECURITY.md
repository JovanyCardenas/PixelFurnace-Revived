# Security Policy

## Supported Versions

PixelFurnace-Revived is an independent, open-source project focused on restoring functionality to the original Minecraft Gameband.

Security fixes and maintenance updates are primarily provided for the latest published version of PixelFurnace Studio.

| Version | Supported |
|---|---|
| Latest release | Yes |
| Older releases | Limited support |
| Development builds | Experimental |

Users are encouraged to download the latest release from the official GitHub repository.

## Reporting a Vulnerability

If you discover a potential security vulnerability, please report it responsibly.

**Do not publicly disclose security vulnerabilities through GitHub Issues or Discussions before they have been reviewed.**

Preferred reporting method:

1. Navigate to the repository's **Security** tab.
2. Select **Advisories**.
3. Choose **Report a vulnerability**, if private vulnerability reporting is enabled.
4. Include a description of the issue, steps to reproduce it, and its potential impact.

If private reporting is not available, please avoid sharing exploit details publicly and request a private reporting channel through a general GitHub Discussion.

## Security Considerations

PixelFurnace Studio communicates directly with original Gameband hardware using USB HID.

Because the application can modify device configuration data, users should take the following precautions:

- Download releases only from trusted sources.
- Keep backups of the original Gameband configuration.
- Avoid disconnecting the device during configuration writes.
- Do not restore unknown or untrusted configuration files.
- Avoid running experimental builds on hardware containing important data.
- Do not disable Windows security protections to run the application.

## Hardware Safety

PixelFurnace Studio includes safeguards such as configuration validation, automatic backups, write verification, and confirmation prompts.

However, these safeguards do not eliminate all risks.

Incorrect configuration writes, unexpected device behavior, or incomplete operations may result in data loss or device malfunction.

Users should understand these risks before using experimental functionality.

## Dependencies and Distribution

PixelFurnace Studio uses Python and third-party dependencies, including `hidapi` and Pillow.

Windows executables are packaged using PyInstaller.

The project aims to keep dependencies updated and distribute application builds through official GitHub Releases.

## Responsible Disclosure

Please allow reasonable time for security issues to be investigated and addressed before publishing technical details.

Security reports and responsible contributions are appreciated.

## Disclaimer

PixelFurnace-Revived is an unofficial community project and is not affiliated with Mojang, Microsoft, or the original Gameband developers.
