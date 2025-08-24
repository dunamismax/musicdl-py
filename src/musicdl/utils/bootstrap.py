"""UV environment bootstrap functionality."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List, Optional

# Required packages for the application
REQUIRED_PACKAGES = [
    "textual>=5.3,<6.0",
    "yt-dlp>=2025.0.0",
    "imageio-ffmpeg>=0.4.9",
    "pydantic>=2.0.0",
    "platformdirs>=4.0.0",
    "rich>=13.0.0",
]


class BootstrapError(Exception):
    """Raised when bootstrap process fails."""


def _validate_executable(path: str, expected_name: str) -> bool:
    """Validate that an executable is safe to use."""
    import stat
    
    try:
        # Check if file exists and is a regular file
        if not os.path.isfile(path):
            return False
        
        # Check file permissions - must be executable
        file_stat = os.stat(path)
        if not (file_stat.st_mode & stat.S_IEXEC):
            return False
        
        # Prevent path traversal
        normalized_path = os.path.normpath(os.path.abspath(path))
        if '..' in normalized_path:
            return False
        
        # Basic filename validation
        filename = os.path.basename(path).lower()
        if expected_name not in filename:
            return False
            
        return True
        
    except (OSError, ValueError):
        return False


def _validate_path_safe(path: str) -> bool:
    """Validate that a path is safe to use."""
    try:
        # Prevent path traversal attempts
        if '..' in path or path.startswith('/') and not path.startswith(os.getcwd()):
            return False
        
        # Normalize and check
        normalized = os.path.normpath(path)
        if normalized != path.replace('\\\\', '/').replace('\\', '/'):
            return False
            
        return True
        
    except (OSError, ValueError):
        return False


def _validate_package_name(package: str) -> bool:
    """Validate package name format for security."""
    import re
    
    # Allow standard package name format with version specifiers
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]?(?:[><=!~]+[0-9][a-zA-Z0-9.,<>]*)?(?:,[<>=!~]+[0-9][a-zA-Z0-9.,<>]*)*$'
    
    if not re.match(pattern, package):
        return False
    
    # Reject obviously malicious patterns
    dangerous_chars = ['&', '|', ';', '`', '$', '(', ')', '{', '}', '[', ']']
    if any(char in package for char in dangerous_chars):
        return False
        
    return True


def _get_safe_env() -> dict:
    """Get a minimal safe environment for subprocess execution."""
    safe_env = {
        'PATH': os.environ.get('PATH', ''),
        'HOME': os.environ.get('HOME', ''),
        'USER': os.environ.get('USER', ''),
        'SHELL': os.environ.get('SHELL', ''),
        'TERM': os.environ.get('TERM', 'xterm'),
        'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
        'LC_ALL': os.environ.get('LC_ALL', ''),
    }
    
    # Add UV-specific environment variables if they exist
    uv_vars = ['UV_CACHE_DIR', 'UV_CONFIG_FILE', 'UV_NO_CACHE']
    for var in uv_vars:
        if var in os.environ:
            safe_env[var] = os.environ[var]
    
    return safe_env


def get_venv_python(venv_dir: Path) -> Path:
    """Get Python executable path in venv."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def is_running_in_target_venv(venv_dir: Path) -> bool:
    """Check if already running in the target virtual environment."""
    if not venv_dir.exists():
        return False

    target_python = get_venv_python(venv_dir).resolve()
    current_python = Path(sys.executable).resolve()

    return current_python == target_python


def ensure_uv_available() -> str:
    """Ensure uv is available and return path with security validation."""
    uv_path = shutil.which("uv")
    if not uv_path:
        error_msg = textwrap.dedent("""
        UV package manager is required but not found on PATH.
        
        Install UV:
          macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh
          Windows:      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        
        Then restart your terminal and try again.
        """).strip()
        raise BootstrapError(error_msg)

    # Validate the UV executable for security
    if not _validate_executable(uv_path, "uv"):
        raise BootstrapError(f"UV executable validation failed: {uv_path}")

    return uv_path


def create_venv(uv_path: str, project_root: Path, venv_dir: Path) -> None:
    """Create virtual environment using UV with security validation."""
    # Validate inputs
    if not _validate_path_safe(str(venv_dir)):
        raise BootstrapError(f"Unsafe venv directory path: {venv_dir}")
    if not _validate_path_safe(str(project_root)):
        raise BootstrapError(f"Unsafe project root path: {project_root}")
    
    try:
        # Use validated paths and restrict subprocess environment
        result = subprocess.run(
            [uv_path, "venv", str(venv_dir)],
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            env=_get_safe_env()
        )
    except subprocess.TimeoutExpired as e:
        raise BootstrapError(f"Venv creation timed out after 2 minutes") from e
    except subprocess.CalledProcessError as e:
        raise BootstrapError(f"Failed to create venv: {e.stderr}") from e


def install_packages(uv_path: str, venv_dir: Path, packages: List[str]) -> None:
    """Install packages into venv using UV with security validation."""
    python_path = str(get_venv_python(venv_dir))
    
    # Validate python executable
    if not _validate_executable(python_path, "python"):
        raise BootstrapError(f"Python executable validation failed: {python_path}")
    
    # Validate package names for security
    for package in packages:
        if not _validate_package_name(package):
            raise BootstrapError(f"Invalid package name: {package}")

    cmd = [uv_path, "pip", "install", "--python", python_path, "--upgrade", *packages]

    try:
        subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=300,  # 5 minute timeout for package installation
            env=_get_safe_env()
        )
    except subprocess.TimeoutExpired as e:
        raise BootstrapError(f"Package installation timed out after 5 minutes") from e
    except subprocess.CalledProcessError as e:
        raise BootstrapError(f"Failed to install packages: {e.stderr}") from e


def reexec_in_venv(venv_dir: Path, script_path: Path, args: List[str]) -> None:
    """Re-execute the script in the virtual environment."""
    python_path = str(get_venv_python(venv_dir))
    exec_args = [python_path, str(script_path)] + args

    # Replace current process
    os.execv(python_path, exec_args)


def ensure_uv_environment(
    project_root: Path,
    venv_dir: Optional[Path] = None,
    packages: Optional[List[str]] = None,
    script_path: Optional[Path] = None,
    reexec: bool = True,
) -> None:
    """
    Ensure UV virtual environment is set up with required packages.

    Args:
        project_root: Root directory of the project
        venv_dir: Virtual environment directory (default: project_root/.venv)
        packages: Packages to install (default: REQUIRED_PACKAGES)
        script_path: Script to re-execute (default: __main__ module)
        reexec: Whether to re-execute in venv if not already running
    """

    if venv_dir is None:
        venv_dir = project_root / ".venv"

    if packages is None:
        packages = REQUIRED_PACKAGES

    # Check if already running in target venv
    if is_running_in_target_venv(venv_dir):
        return

    # Ensure UV is available
    uv_path = ensure_uv_available()

    # Create venv if it doesn't exist
    if not venv_dir.exists():
        create_venv(uv_path, project_root, venv_dir)

    # Install/upgrade packages
    install_packages(uv_path, venv_dir, packages)

    # Re-execute in venv if requested
    if reexec:
        if script_path is None:
            # Use the main script that was executed
            script_path = Path(sys.argv[0]).resolve()

        reexec_in_venv(venv_dir, script_path, sys.argv[1:])


def bootstrap_standalone_script() -> None:
    """Bootstrap for standalone script execution."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent

    ensure_uv_environment(
        project_root=project_root,
        script_path=script_path,
    )
