#!/usr/bin/env python3
"""Generate Python bindings from protobuf definitions."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def generate_python_bindings(proto_dir: Optional[Path] = None) -> None:
    """Generate Python bindings for all proto files.
    
    Args:
        proto_dir: Directory containing proto files. Defaults to current directory.
    """
    if proto_dir is None:
        proto_dir = Path(__file__).parent
    
    output_dir = proto_dir / "generated" / "python"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py for the generated package
    init_file = output_dir / "__init__.py"
    init_file.write_text(
        '"""Generated protobuf Python bindings for Gadugi v0.3."""\n\n'
        '__version__ = "0.3.0"\n'
    )
    
    # Find all proto files
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print(f"No proto files found in {proto_dir}")
        return
    
    print(f"Found {len(proto_files)} proto files to process")
    
    # Generate bindings for each proto file
    for proto_file in proto_files:
        print(f"Processing {proto_file.name}...")
        
        # Use protoc directly if available, otherwise use grpc_tools
        try:
            # Try using protoc directly
            cmd = [
                "protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={output_dir}",
                f"--pyi_out={output_dir}",  # Generate type stubs
                str(proto_file)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Fall back to grpc_tools if protoc fails
                print(f"protoc failed, trying grpc_tools.protoc...")
                cmd = [
                    sys.executable, "-m", "grpc_tools.protoc",
                    f"--proto_path={proto_dir}",
                    f"--python_out={output_dir}",
                    str(proto_file)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✓ Generated bindings for {proto_file.name}")
            else:
                print(f"  ✗ Failed to generate bindings for {proto_file.name}")
                print(f"    Error: {result.stderr}")
                
        except FileNotFoundError:
            # protoc not found, use grpc_tools
            print(f"protoc not found, using grpc_tools.protoc...")
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={output_dir}",
                str(proto_file)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✓ Generated bindings for {proto_file.name}")
            else:
                print(f"  ✗ Failed to generate bindings for {proto_file.name}")
                print(f"    Error: {result.stderr}")
    
    # Fix imports in generated files to use relative imports
    fix_imports(output_dir)
    
    print(f"\nGenerated files in: {output_dir}")
    generated_files = list(output_dir.glob("*_pb2.py"))
    for f in generated_files:
        print(f"  - {f.name}")


def fix_imports(output_dir: Path) -> None:
    """Fix imports in generated protobuf files to use relative imports.
    
    Args:
        output_dir: Directory containing generated Python files.
    """
    for py_file in output_dir.glob("*_pb2.py"):
        content = py_file.read_text()
        
        # Fix import statements to use relative imports
        content = content.replace("import common_pb2", "from . import common_pb2")
        content = content.replace("from common_pb2", "from .common_pb2")
        
        py_file.write_text(content)


def verify_installation() -> bool:
    """Verify that required packages are installed.
    
    Returns:
        True if all requirements are met, False otherwise.
    """
    # Map package names to their import names
    required_imports = {"google.protobuf": "protobuf"}
    optional_imports = {"grpc_tools": "grpcio-tools"}
    
    missing_required = []
    missing_optional = []
    
    for import_name, package_name in required_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_required.append(package_name)
    
    for import_name, package_name in optional_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_optional.append(package_name)
    
    if missing_required:
        print("ERROR: Missing required packages:")
        for pkg in missing_required:
            print(f"  - {pkg}")
        print("\nInstall with: uv add " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print("WARNING: Missing optional packages:")
        for pkg in missing_optional:
            print(f"  - {pkg}")
        print("\nFor better protobuf support, install with: uv add " + " ".join(missing_optional))
    
    return True


def main():
    """Main entry point."""
    print("Gadugi v0.3 Protobuf Generator")
    print("=" * 40)
    
    if not verify_installation():
        sys.exit(1)
    
    proto_dir = Path(__file__).parent
    generate_python_bindings(proto_dir)
    
    print("\n✅ Protobuf generation complete!")
    print("\nTo use the generated bindings:")
    print("  from gadugi.protos.generated.python import agent_events_pb2")
    print("  from gadugi.protos.generated.python import task_events_pb2")
    print("  from gadugi.protos.generated.python import common_pb2")


if __name__ == "__main__":
    main()