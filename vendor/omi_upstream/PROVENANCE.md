# Omi Upstream Provenance

This directory contains a snapshot of the Omi open-source project, vendored for use as the foundation of Echo.

## Source Information

- **Upstream Repository**: https://github.com/BasedHardware/Omi
- **Commit SHA**: e1c5e81fb1c72f49ac8b7c2a86c45838b0b94a52
- **Import Date**: 2025-12-26
- **License**: MIT License

## License

The original Omi code is licensed under the MIT License.
See LICENSE file in this directory (copied from upstream).

```
MIT License

Copyright (c) 2024 Based Hardware Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Contents

This vendor snapshot includes:
- `app/` - Flutter mobile application
- `backend/` - FastAPI backend service
- `LICENSE` - Original MIT license

## Usage in Echo

The code from this vendor directory is copied to:
- `/apps/echo_mobile` - Rebranded Flutter app
- `/services/echo_backend` - Rebranded backend service

Do NOT modify files in this vendor directory directly. It serves as a read-only reference
for the original upstream code. All modifications should be made in the product directories.

## Updating from Upstream

To update from upstream:
1. Clone fresh copy of https://github.com/BasedHardware/Omi
2. Update this PROVENANCE.md with new commit SHA and date
3. Copy updated app/backend to vendor
4. Merge changes into product directories
5. Re-apply Echo branding changes
