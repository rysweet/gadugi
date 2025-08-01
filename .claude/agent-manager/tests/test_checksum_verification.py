#!/usr/bin/env python3
"""
Test the checksum verification functionality for downloaded scripts.
"""

import tempfile
import unittest
from pathlib import Path
import subprocess
import shutil


class TestChecksumVerification(unittest.TestCase):
    """Test checksum verification for script downloads."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.scripts_dir = Path(self.test_dir) / '.claude' / 'agent-manager' / 'scripts'
        self.scripts_dir.mkdir(parents=True)
        
        # Create a test script
        self.test_script = self.scripts_dir / 'test-script.sh'
        self.test_script.write_text('#!/bin/sh\necho "Test script"\n')
        
        # Create checksums file
        result = subprocess.run(
            ['sha256sum', 'test-script.sh'],
            cwd=self.scripts_dir,
            capture_output=True,
            text=True
        )
        self.checksums_file = self.scripts_dir / 'checksums.sha256'
        self.checksums_file.write_text(result.stdout)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_valid_checksum_passes(self):
        """Test that valid checksum verification passes."""
        # Create verification script
        verify_script = self.scripts_dir / 'verify.sh'
        verify_script.write_text('''#!/bin/bash
verify_script_integrity() {
    local script_file="$1"
    local checksums_file="$2"
    local script_name=$(basename "$script_file")
    
    if ! command -v sha256sum >/dev/null 2>&1; then
        echo "WARNING: sha256sum not found"
        return 0
    fi
    
    local expected_checksum=$(grep "$script_name" "$checksums_file" | awk '{print $1}')
    if [ -z "$expected_checksum" ]; then
        echo "No checksum found"
        return 1
    fi
    
    local actual_checksum=$(sha256sum "$script_file" | awk '{print $1}')
    
    if [ "$expected_checksum" = "$actual_checksum" ]; then
        echo "Integrity verified"
        return 0
    else
        echo "Integrity check failed"
        return 1
    fi
}

verify_script_integrity "$1" "$2"
''')
        verify_script.chmod(0o755)
        
        # Run verification
        result = subprocess.run(
            [str(verify_script), str(self.test_script), str(self.checksums_file)],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, f"Verification failed: {result.stderr}")
        self.assertIn("Integrity verified", result.stdout)
    
    def test_modified_script_fails(self):
        """Test that modified script fails checksum verification."""
        # Modify the script after checksum was calculated
        self.test_script.write_text('#!/bin/sh\necho "Modified script"\n')
        
        # Create verification script
        verify_script = self.scripts_dir / 'verify.sh'
        verify_script.write_text('''#!/bin/bash
verify_script_integrity() {
    local script_file="$1"
    local checksums_file="$2"
    local script_name=$(basename "$script_file")
    
    if ! command -v sha256sum >/dev/null 2>&1; then
        echo "WARNING: sha256sum not found"
        return 0
    fi
    
    local expected_checksum=$(grep "$script_name" "$checksums_file" | awk '{print $1}')
    if [ -z "$expected_checksum" ]; then
        echo "No checksum found"
        return 1
    fi
    
    local actual_checksum=$(sha256sum "$script_file" | awk '{print $1}')
    
    if [ "$expected_checksum" = "$actual_checksum" ]; then
        echo "Integrity verified"
        return 0
    else
        echo "Integrity check failed"
        return 1
    fi
}

verify_script_integrity "$1" "$2"
''')
        verify_script.chmod(0o755)
        
        # Run verification
        result = subprocess.run(
            [str(verify_script), str(self.test_script), str(self.checksums_file)],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0, "Verification should have failed")
        self.assertIn("Integrity check failed", result.stdout)


if __name__ == '__main__':
    unittest.main()