#!/usr/bin/env python3
"""
Development Environment Setup Script
Creates virtual environments and installs dependencies for all services.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Execute a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def setup_service_venv(service_path):
    """Set up virtual environment for a service"""
    service_name = service_path.name
    print(f"Setting up {service_name}...")
    
    venv_path = service_path / "venv"
    requirements_path = service_path / "requirements.txt"
    
    if not requirements_path.exists():
        print(f"  ⚠️  No requirements.txt found for {service_name}")
        return False
    
    # Create virtual environment
    success, output = run_command(f"python -m venv venv", cwd=service_path)
    if not success:
        print(f"  ❌ Failed to create venv: {output}")
        return False
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        pip_cmd = str(venv_path / "Scripts" / "pip")
    else:  # Unix-like
        activate_script = venv_path / "bin" / "activate"
        pip_cmd = str(venv_path / "bin" / "pip")
    
    # Install dependencies
    success, output = run_command(f"{pip_cmd} install -r requirements.txt", cwd=service_path)
    if not success:
        print(f"  ❌ Failed to install dependencies: {output}")
        return False
    
    print(f"  ✅ {service_name} environment ready")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up BMAD development environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    
    if not services_dir.exists():
        print("❌ Services directory not found")
        sys.exit(1)
    
    # Setup each service
    services = [d for d in services_dir.iterdir() if d.is_dir()]
    successful = 0
    
    for service in services:
        if setup_service_venv(service):
            successful += 1
    
    print(f"\n✅ Setup complete! {successful}/{len(services)} services ready")
    print(f"\n📝 Next steps:")
    print(f"   1. Copy .env.example to .env in each service")
    print(f"   2. Configure database connection settings")
    print(f"   3. Run 'make test' to validate setup")

if __name__ == "__main__":
    main()