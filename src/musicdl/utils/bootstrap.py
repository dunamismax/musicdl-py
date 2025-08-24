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
    """Ensure uv is available and return path."""
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
    
    return uv_path


def create_venv(uv_path: str, project_root: Path, venv_dir: Path) -> None:
    """Create virtual environment using UV."""
    try:
        subprocess.run(
            [uv_path, "venv", str(venv_dir)],
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise BootstrapError(f"Failed to create venv: {e.stderr}") from e


def install_packages(
    uv_path: str, 
    venv_dir: Path, 
    packages: List[str]
) -> None:
    """Install packages into venv using UV."""
    python_path = str(get_venv_python(venv_dir))
    
    cmd = [
        uv_path, "pip", "install", 
        "--python", python_path,
        "--upgrade",
        *packages
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
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