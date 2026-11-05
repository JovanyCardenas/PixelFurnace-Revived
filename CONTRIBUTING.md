# Contributing to PixelFurnace-Revived

Thank you for your interest in contributing to PixelFurnace-Revived!

This project aims to restore functionality to the original Minecraft Gameband, preserve knowledge about its hardware and software, and develop an open-source replacement for the discontinued PixelFurnace editor.

Contributions of all experience levels are welcome.

## Ways to Contribute

You can help by:

- Reporting bugs and compatibility issues
- Testing PixelFurnace Studio with original Gameband hardware
- Suggesting improvements and new features
- Contributing Python code
- Improving documentation and installation instructions
- Sharing reverse-engineering discoveries
- Investigating original Gameband and Minecraft launcher functionality

You do not need to be a developer to contribute.

## Before Contributing

Please check the existing GitHub Issues and Discussions before opening a new report.

- **Issues:** Confirmed bugs, actionable improvements, and development tasks
- **Discussions:** General questions, ideas, and community research
- **Wiki:** Documentation and known hardware information

For security vulnerabilities, follow the repository's `SECURITY.md` policy rather than publicly disclosing exploit details.

## Development Setup

PixelFurnace Studio is primarily developed in Python.

### Requirements

- Python 3
- Git
- Dependencies listed in `requirements.txt`
- Original Gameband hardware for device-specific testing

Clone the repository:

```bash
git clone https://github.com/JovanyCardenas/PixelFurnace-Revived.git
cd PixelFurnace-Revived
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python PixelFurnaceStudio.py
```

## Submitting Code Changes

1. Fork the repository.
2. Create a branch for your change.
3. Make your changes.
4. Test your code before submitting.
5. Open a Pull Request describing your changes.

Please keep pull requests focused on one feature or fix whenever possible.

## Testing Guidelines

Before submitting changes:

- Verify the Python application starts successfully.
- Check that existing features continue working.
- Test affected functionality where possible.
- Describe any hardware testing performed.
- Clearly state when hardware testing was not possible.

For changes involving HID commands, memory addresses, configuration structures, or clock synchronization, please include extra testing details.

**Never claim a hardware-related fix is verified unless it has actually been tested on compatible hardware.**

## Hardware Safety

PixelFurnace Studio communicates directly with original Gameband hardware and can modify device configuration data.

Please:

- Preserve unknown configuration fields unless their behavior is understood.
- Create backups before writing configuration data.
- Avoid unnecessary changes to HID commands or memory operations.
- Document any new protocol discoveries.
- Prefer read-only investigation when behavior is uncertain.

Hardware-related changes should be reviewed carefully before merging.

## Reporting Bugs

When reporting a bug, include:

- PixelFurnace Studio version
- Operating system
- Description of the problem
- Steps to reproduce
- Expected and actual behavior
- Relevant logs or screenshots
- Whether original Gameband hardware was used

## Documentation Contributions

Documentation improvements are welcome.

Technical discoveries should distinguish between:

- **Verified:** Confirmed through testing or reliable evidence
- **Experimental:** Implemented or observed but not fully validated
- **Under Investigation:** Suspected behavior requiring additional research

## Community

Please be respectful and constructive when discussing ideas, reviewing code, or reporting problems.

This project is a collaborative preservation effort, and contributions from the Gameband community are appreciated.

Thank you for helping bring the original Gameband back to life!
