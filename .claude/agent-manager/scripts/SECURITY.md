# Agent Manager Scripts Security

## Overview

The agent-manager uses a checksum-based integrity verification system to ensure that downloaded scripts have not been tampered with.

## Security Model

1. **Checksum File**: `checksums.sha256` contains SHA-256 hashes of all scripts
2. **Verification Process**:
   - Checksums are downloaded before scripts
   - Each script is verified against its expected checksum
   - Failed verification results in script deletion
   - Local scripts are also verified if checksums are available

## Updating Scripts

When modifying scripts, you must regenerate the checksums:

```bash
cd .claude/agent-manager/scripts
sha256sum *.sh > checksums.sha256
```

## Security Considerations

- **Trust Model**: You trust the initial checksums from the repository
- **HTTPS**: All downloads use HTTPS to prevent MITM attacks
- **Fail-Safe**: Scripts that fail verification are deleted
- **Graceful Degradation**: If sha256sum is unavailable, a warning is shown but execution continues (for compatibility)

## Future Improvements

Consider:
- GPG signature verification for stronger authenticity
- Pinning to specific commit hashes instead of main branch
- Local-only mode that disables all downloads
