"""
Container Image Manager for secure image building and management.

Manages container images with security scanning, hardening,
and efficient caching for the Gadugi execution environment.
"""

import logging
import hashlib
import subprocess
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import json
import tempfile

if TYPE_CHECKING:
    import docker
else:
    docker = None

# Runtime import attempt
try:
    import docker  # type: ignore[import-untyped]

    docker_available = True
except ImportError:
    docker_available = False

# Import Enhanced Separation shared modules
import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", ".claude", "shared", "utils")
)
try:
    from error_handling import GadugiError  # type: ignore[import-not-found]
except ImportError:

    class GadugiError(Exception):  # type: ignore[import-not-found]
        pass


logger = logging.getLogger(__name__)


@dataclass
class ImageInfo:
    """Container image information."""

    name: str
    tag: str
    image_id: str
    size: int
    created: datetime
    layers: List[str]
    security_scan_date: Optional[datetime] = None
    vulnerability_count: Optional[int] = None
    security_score: Optional[float] = None


@dataclass
class BuildContext:
    """Container image build context."""

    base_image: str
    runtime: str  # python, node, shell, etc.
    packages: List[str]
    security_hardening: bool = True
    minimal_install: bool = True
    user_id: int = 1000
    group_id: int = 1000


class ImageManager:
    """
    Manages container images for secure execution environment.

    Provides image building, security scanning, caching, and
    lifecycle management for containerized execution.
    """

    def __init__(
        self,
        docker_client: Optional[Any] = None,
        image_cache_dir: Optional[Path] = None,
    ):
        """Initialize image manager."""
        if not docker_available:
            raise GadugiError("Docker is not available. Please install docker package.")

        self.client = docker_client or docker.from_env()  # type: ignore[attr-defined]
        self.image_cache_dir = image_cache_dir or Path("cache/images")
        self.image_cache_dir.mkdir(parents=True, exist_ok=True)

        self.image_registry: Dict[str, ImageInfo] = {}
        self.security_scanner_available = self._check_security_scanner()

        # Load existing image information
        self._load_image_registry()

        logger.info("Image manager initialized")

    def _check_security_scanner(self) -> bool:
        """Check if security scanner (trivy) is available."""
        try:
            result = subprocess.run(
                ["trivy", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logger.info("Trivy security scanner available")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass

        logger.warning(
            "Trivy security scanner not available - security scanning disabled"
        )
        return False

    def _load_image_registry(self) -> None:
        """Load image registry from cache."""
        registry_file = self.image_cache_dir / "image_registry.json"

        if registry_file.exists():
            try:
                with open(registry_file, "r") as f:
                    registry_data = json.load(f)

                for name, data in registry_data.items():
                    self.image_registry[name] = ImageInfo(
                        name=data["name"],
                        tag=data["tag"],
                        image_id=data["image_id"],
                        size=data["size"],
                        created=datetime.fromisoformat(data["created"]),
                        layers=data["layers"],
                        security_scan_date=datetime.fromisoformat(
                            data["security_scan_date"]
                        )
                        if data.get("security_scan_date")
                        else None,
                        vulnerability_count=data.get("vulnerability_count"),
                        security_score=data.get("security_score"),
                    )

                logger.info(f"Loaded {len(self.image_registry)} images from registry")

            except Exception as e:
                logger.warning(f"Failed to load image registry: {e}")

    def _save_image_registry(self) -> None:
        """Save image registry to cache."""
        registry_file = self.image_cache_dir / "image_registry.json"

        try:
            registry_data = {}
            for name, info in self.image_registry.items():
                registry_data[name] = {
                    "name": info.name,
                    "tag": info.tag,
                    "image_id": info.image_id,
                    "size": info.size,
                    "created": info.created.isoformat(),
                    "layers": info.layers,
                    "security_scan_date": info.security_scan_date.isoformat()
                    if info.security_scan_date
                    else None,
                    "vulnerability_count": info.vulnerability_count,
                    "security_score": info.security_score,
                }

            with open(registry_file, "w") as f:
                json.dump(registry_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save image registry: {e}")

    def create_runtime_image(self, context: BuildContext) -> str:
        """
        Create a hardened runtime image.

        Args:
            context: Build context with runtime specifications

        Returns:
            Image name with tag

        Raises:
            GadugiError: If image creation fails
        """
        image_name = f"gadugi/{context.runtime}"
        image_tag = self._generate_image_tag(context)
        full_name = f"{image_name}:{image_tag}"

        # Check if image already exists
        if self._image_exists(full_name):
            logger.info(f"Image {full_name} already exists")
            return full_name

        try:
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(context)

            # Build image
            with tempfile.TemporaryDirectory() as build_dir:
                dockerfile_path = Path(build_dir) / "Dockerfile"
                with open(dockerfile_path, "w") as f:
                    f.write(dockerfile_content)

                logger.info(f"Building image {full_name}")
                image, build_logs = self.client.images.build(
                    path=build_dir, tag=full_name, rm=True, pull=True, nocache=False
                )

                # Log build output
                for log in build_logs:
                    if isinstance(log, dict) and "stream" in log:
                        stream_content = log["stream"]
                        if isinstance(stream_content, str):
                            logger.debug(stream_content.strip())

            # Update registry
            self._register_image(image, context.runtime)

            # Perform security scan
            if self.security_scanner_available:
                self._scan_image_security(full_name)

            logger.info(f"Successfully created image {full_name}")
            return full_name

        except Exception as e:
            # Handle docker build errors and other exceptions
            if hasattr(e, "__class__") and "BuildError" in str(type(e)):
                raise GadugiError(f"Failed to build image: {e}")
            else:
                raise GadugiError(f"Unexpected error creating image: {e}")

    def _generate_image_tag(self, context: BuildContext) -> str:
        """Generate deterministic image tag based on context."""
        context_str = f"{context.base_image}:{context.runtime}:{context.packages}:{context.security_hardening}"
        return hashlib.sha256(context_str.encode()).hexdigest()[:12]

    def _generate_dockerfile(self, context: BuildContext) -> str:
        """Generate Dockerfile for runtime image."""

        # Base Dockerfiles for different runtimes
        dockerfiles = {
            "python": self._generate_python_dockerfile(context),
            "node": self._generate_node_dockerfile(context),
            "shell": self._generate_shell_dockerfile(context),
            "multi": self._generate_multi_runtime_dockerfile(context),
        }

        return dockerfiles.get(context.runtime, dockerfiles["shell"])

    def _generate_python_dockerfile(self, context: BuildContext) -> str:
        """Generate Dockerfile for Python runtime."""
        packages_str = " ".join(context.packages) if context.packages else ""

        dockerfile = f"""
FROM {context.base_image}

# Security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Install Python packages if specified
{f"RUN pip install --no-cache-dir {packages_str}" if packages_str else ""}

# Create non-root user
RUN groupadd -g {context.group_id} gadugi \\
    && useradd -u {context.user_id} -g gadugi -m gadugi \\
    && mkdir -p /workspace \\
    && chown -R gadugi:gadugi /workspace

# Security hardening
RUN chmod -R go-w /usr/local/lib/python* \\
    && find /usr/local/lib/python* -name "*.pyc" -delete \\
    && find /usr/local/lib/python* -name "__pycache__" -type d -exec rm -rf {{}} + || true

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER gadugi:gadugi

# Default command
CMD ["/bin/bash"]
"""

        return dockerfile.strip()

    def _generate_node_dockerfile(self, context: BuildContext) -> str:
        """Generate Dockerfile for Node.js runtime."""
        packages_str = " ".join(context.packages) if context.packages else ""

        dockerfile = f"""
FROM {context.base_image}

# Security updates
RUN apk update && apk upgrade \\
    && apk add --no-cache ca-certificates \\
    && rm -rf /var/cache/apk/*

# Install npm packages if specified
{f"RUN npm install -g {packages_str}" if packages_str else ""}

# Create non-root user
RUN addgroup -g {context.group_id} gadugi \\
    && adduser -u {context.user_id} -G gadugi -s /bin/sh -D gadugi \\
    && mkdir -p /workspace \\
    && chown -R gadugi:gadugi /workspace

# Security hardening
RUN find /usr/local/lib/node_modules -type f -name "*.md" -delete \\
    && find /usr/local/lib/node_modules -name "test" -type d -exec rm -rf {{}} + || true \\
    && find /usr/local/lib/node_modules -name "docs" -type d -exec rm -rf {{}} + || true

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER gadugi:gadugi

# Default command
CMD ["/bin/sh"]
"""

        return dockerfile.strip()

    def _generate_shell_dockerfile(self, context: BuildContext) -> str:
        """Generate Dockerfile for shell runtime."""

        dockerfile = f"""
FROM {context.base_image}

# Security updates and minimal tools
RUN apk update && apk upgrade \\
    && apk add --no-cache ca-certificates coreutils \\
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g {context.group_id} gadugi \\
    && adduser -u {context.user_id} -G gadugi -s /bin/sh -D gadugi \\
    && mkdir -p /workspace \\
    && chown -R gadugi:gadugi /workspace

# Remove unnecessary files
RUN rm -rf /tmp/* /var/tmp/* \\
    && find /usr -name "*.a" -delete \\
    && find /usr -name "*.la" -delete

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER gadugi:gadugi

# Default command
CMD ["/bin/sh"]
"""

        return dockerfile.strip()

    def _generate_multi_runtime_dockerfile(self, context: BuildContext) -> str:
        """Generate Dockerfile for multi-language runtime."""

        dockerfile = f"""
FROM {context.base_image}

# Install multiple runtimes
RUN apt-get update && apt-get install -y --no-install-recommends \\
    python3 python3-pip \\
    nodejs npm \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Create non-root user
RUN groupadd -g {context.group_id} gadugi \\
    && useradd -u {context.user_id} -g gadugi -m gadugi \\
    && mkdir -p /workspace \\
    && chown -R gadugi:gadugi /workspace

# Security hardening
RUN find /usr -name "*.pyc" -delete \\
    && find /usr -name "__pycache__" -type d -exec rm -rf {{}} + || true

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER gadugi:gadugi

# Default command
CMD ["/bin/bash"]
"""

        return dockerfile.strip()

    def _image_exists(self, image_name: str) -> bool:
        """Check if image exists locally."""
        try:
            self.client.images.get(image_name)
            return True
        except Exception as e:
            # Handle ImageNotFound and other exceptions
            if "ImageNotFound" in str(type(e)) or "not found" in str(e).lower():
                return False
            # Re-raise other exceptions
            raise

    def _register_image(self, image, runtime: str) -> None:
        """Register image in local registry."""
        try:
            # Get image information
            image.reload()

            image_info = ImageInfo(
                name=image.tags[0].split(":")[0] if image.tags else "unknown",
                tag=image.tags[0].split(":")[1]
                if image.tags and ":" in image.tags[0]
                else "latest",
                image_id=image.id,
                size=image.attrs.get("Size", 0),
                created=datetime.fromisoformat(
                    image.attrs.get("Created", "").replace("Z", "+00:00")
                ),
                layers=[layer["Id"] for layer in image.history()],
            )

            full_name = image.tags[0] if image.tags else image.id
            self.image_registry[full_name] = image_info

            # Save registry
            self._save_image_registry()

            logger.info(f"Registered image {full_name} in local registry")

        except Exception as e:
            logger.warning(f"Failed to register image: {e}")

    def _scan_image_security(self, image_name: str) -> Optional[Dict[str, Any]]:
        """Scan image for security vulnerabilities using Trivy."""
        if not self.security_scanner_available:
            return None

        try:
            logger.info(f"Scanning image {image_name} for vulnerabilities")

            # Run trivy scan
            result = subprocess.run(
                ["trivy", "image", "--format", "json", "--quiet", image_name],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.warning(
                    f"Security scan failed for {image_name}: {result.stderr}"
                )
                return None

            scan_data = json.loads(result.stdout)

            # Process scan results
            total_vulnerabilities = 0
            critical_count = 0
            high_count = 0

            for result_item in scan_data.get("Results", []):
                vulnerabilities = result_item.get("Vulnerabilities", [])
                total_vulnerabilities += len(vulnerabilities)

                for vuln in vulnerabilities:
                    severity = vuln.get("Severity", "").upper()
                    if severity == "CRITICAL":
                        critical_count += 1
                    elif severity == "HIGH":
                        high_count += 1

            # Calculate security score (0-100, higher is better)
            security_score = max(0, 100 - (critical_count * 10 + high_count * 5))

            # Update image registry
            if image_name in self.image_registry:
                self.image_registry[image_name].security_scan_date = datetime.now()
                self.image_registry[
                    image_name
                ].vulnerability_count = total_vulnerabilities
                self.image_registry[image_name].security_score = security_score
                self._save_image_registry()

            scan_summary = {
                "total_vulnerabilities": total_vulnerabilities,
                "critical_count": critical_count,
                "high_count": high_count,
                "security_score": security_score,
                "scan_date": datetime.now().isoformat(),
            }

            logger.info(
                f"Security scan completed for {image_name}: "
                f"{total_vulnerabilities} vulnerabilities, score: {security_score}"
            )

            return scan_summary

        except subprocess.TimeoutExpired:
            logger.warning(f"Security scan timed out for {image_name}")
            return None
        except Exception as e:
            logger.error(f"Security scan error for {image_name}: {e}")
            return None

    def get_or_create_runtime_image(
        self,
        runtime: str,
        base_image: Optional[str] = None,
        packages: Optional[List[str]] = None,
    ) -> str:
        """
        Get existing runtime image or create new one.

        Args:
            runtime: Runtime type (python, node, shell, multi)
            base_image: Base image to use
            packages: Additional packages to install

        Returns:
            Full image name with tag
        """
        # Default base images for each runtime
        default_base_images = {
            "python": "python:3.11-slim",
            "node": "node:18-alpine",
            "shell": "alpine:latest",
            "multi": "ubuntu:22.04",
        }

        context = BuildContext(
            base_image=base_image or default_base_images.get(runtime, "alpine:latest"),
            runtime=runtime,
            packages=packages or [],
            security_hardening=True,
            minimal_install=True,
        )

        return self.create_runtime_image(context)

    def list_images(self) -> List[ImageInfo]:
        """List all managed images."""
        return list(self.image_registry.values())

    def get_image_info(self, image_name: str) -> Optional[ImageInfo]:
        """Get information about specific image."""
        return self.image_registry.get(image_name)

    def cleanup_old_images(self, max_age_days: int = 30) -> int:
        """Clean up old unused images."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        images_removed = 0

        try:
            # Get all Docker images
            all_images = self.client.images.list()

            for image in all_images:
                if not image.tags:  # Skip untagged images
                    continue

                # Check if image is old
                created_date = datetime.fromisoformat(
                    image.attrs.get("Created", "").replace("Z", "+00:00")
                )

                if created_date < cutoff_date:
                    # Check if image is in use
                    image_id = getattr(image, "id", None)
                    if image_id and not self._image_in_use(image_id):
                        try:
                            image_name = image.tags[0] if image.tags else image_id
                            self.client.images.remove(image_id, force=True)

                            # Remove from registry
                            if image_name in self.image_registry:
                                del self.image_registry[image_name]

                            images_removed += 1
                            logger.info(f"Removed old image: {image_name}")

                        except Exception as e:
                            logger.warning(f"Failed to remove image {image.id}: {e}")

            # Save updated registry
            self._save_image_registry()

        except Exception as e:
            logger.error(f"Error during image cleanup: {e}")

        return images_removed

    def _image_in_use(self, image_id: str) -> bool:
        """Check if image is currently in use by any container."""
        try:
            containers = self.client.containers.list(all=True)
            for container in containers:
                if container.image.id == image_id:
                    return True
            return False
        except Exception:
            return True  # Assume in use if we can't check

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary for all managed images."""
        total_images = len(self.image_registry)
        scanned_images = sum(
            1
            for img in self.image_registry.values()
            if img.security_scan_date is not None
        )

        vulnerability_counts = [
            img.vulnerability_count
            for img in self.image_registry.values()
            if img.vulnerability_count is not None
        ]

        security_scores = [
            img.security_score
            for img in self.image_registry.values()
            if img.security_score is not None
        ]

        return {
            "total_images": total_images,
            "scanned_images": scanned_images,
            "scan_coverage": (scanned_images / total_images * 100)
            if total_images > 0
            else 0,
            "average_vulnerabilities": sum(vulnerability_counts)
            / len(vulnerability_counts)
            if vulnerability_counts
            else 0,
            "average_security_score": sum(security_scores) / len(security_scores)
            if security_scores
            else 0,
            "scanner_available": self.security_scanner_available,
        }
