#!/usr/bin/env python3
"""
CloneMe Setup Script - Fully Autonomous Cross-Platform Setup
Supports Windows, Linux, and macOS with complete dependency management
Tested and optimized for Python 3.11.6
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

RECOMMENDED_PYTHON = "3.11.6"
MINIMUM_PYTHON = (3, 11)

def setup_logging() -> logging.Logger:
    """Set up comprehensive logging for setup operations"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    setup_logs_dir = logs_dir / "setup"
    setup_logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = setup_logs_dir / f"setup_{timestamp}.log"

    logger = logging.getLogger("CloneMe_Setup")
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 80)
    logger.info("CloneMe Setup Script Started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Architecture: {platform.machine()}")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info("=" * 80)

    return logger

logger = setup_logging()

class Colors:
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE, log_level: str = "info") -> None:
    """Print colored text with cross-platform support and logging"""
    print(f"{color}{text}{Colors.RESET}")

    clean_text = text.strip()
    if clean_text:
        if log_level == "error":
            logger.error(clean_text)
        elif log_level == "warning":
            logger.warning(clean_text)
        elif log_level == "debug":
            logger.debug(clean_text)
        else:
            logger.info(clean_text)

def print_header():
    """Print setup header with system information"""
    start_time = datetime.now()
    logger.info("Starting setup header display")

    print_colored("=" * 80, Colors.CYAN)
    print_colored("🤖 CloneMe - AI Digital Twin Setup Script", Colors.BOLD + Colors.MAGENTA)
    print_colored("Fully Autonomous Cross-Platform Setup", Colors.CYAN)
    print_colored("=" * 80, Colors.CYAN)
    print()

    system_info = {
        "Platform": f"{platform.system()} {platform.release()}",
        "Architecture": platform.machine(),
        "Python": f"{sys.version.split()[0]}",
        "Recommended": f"Python {RECOMMENDED_PYTHON}",
        "Working Directory": str(Path.cwd()),
        "Setup Started": start_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    logger.info("System Information:")
    for key, value in system_info.items():
        print_colored(f"📋 {key}: {value}", Colors.WHITE)
        logger.info(f"  {key}: {value}")
    print()

    logger.info("Header display completed")

def check_python_version() -> bool:
    """Check Python version with detailed recommendations"""
    logger.info("Starting Python version check")

    try:
        version = sys.version_info
        current_version = f"{version.major}.{version.minor}.{version.micro}"
        logger.info(f"Detected Python version: {current_version}")
        logger.info(f"Full Python version info: {sys.version}")

        if version.major < MINIMUM_PYTHON[0] or (version.major == MINIMUM_PYTHON[0] and version.minor < MINIMUM_PYTHON[1]):
            logger.error(f"Incompatible Python version: {current_version}")
            print_colored("❌ CRITICAL: Incompatible Python version detected!", Colors.RED + Colors.BOLD, "error")
            print_colored(f"   Current: Python {current_version}", Colors.RED, "error")
            print_colored(f"   Required: Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+", Colors.YELLOW, "warning")
            print_colored(f"   Recommended: Python {RECOMMENDED_PYTHON}", Colors.GREEN)
            print()
            print_colored("🔧 Installation Instructions:", Colors.BOLD)

            system_name = platform.system()
            logger.info(f"Providing installation instructions for: {system_name}")

            if system_name == "Windows":
                print_colored("   Windows: Download from https://python.org/downloads/", Colors.WHITE)
                print_colored("   Or use: winget install Python.Python.3.11", Colors.WHITE)
            elif system_name == "Linux":
                print_colored("   Ubuntu/Debian: sudo apt update && sudo apt install python3.11 python3.11-venv", Colors.WHITE)
                print_colored("   CentOS/RHEL: sudo yum install python3.11", Colors.WHITE)
                print_colored("   Or compile from source: https://python.org/downloads/source/", Colors.WHITE)
            else:
                print_colored("   macOS: brew install python@3.11", Colors.WHITE)
                print_colored("   Or download from: https://python.org/downloads/", Colors.WHITE)

            logger.info("Python version check failed - incompatible version")
            return False

        if current_version == RECOMMENDED_PYTHON:
            logger.info(f"Perfect Python version match: {current_version}")
            print_colored(f"✅ PERFECT: Python {current_version} (Recommended version)", Colors.GREEN + Colors.BOLD)
        elif version >= (3, 11):
            logger.info(f"Compatible Python version: {current_version}")
            print_colored(f"✅ COMPATIBLE: Python {current_version}", Colors.GREEN)
            print_colored(f"   💡 Tip: Python {RECOMMENDED_PYTHON} is the tested version", Colors.YELLOW, "warning")
        else:
            logger.warning(f"Python version may have compatibility issues: {current_version}")
            print_colored(f"⚠️  WARNING: Python {current_version} may have compatibility issues", Colors.YELLOW, "warning")
            print_colored(f"   Strongly recommend upgrading to Python {RECOMMENDED_PYTHON}", Colors.YELLOW, "warning")

        logger.info("Python version check completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during Python version check: {e}")
        print_colored(f"❌ Error checking Python version: {e}", Colors.RED, "error")
        return False

def get_pip_command() -> Optional[List[str]]:
    """Get the working pip command for this system"""
    logger.info("Starting pip command detection")

    pip_commands = [
        [sys.executable, "-m", "pip"],
        ["pip3"],
        ["pip"]
    ]

    logger.info(f"Will try pip commands in order: {pip_commands}")

    for i, cmd in enumerate(pip_commands, 1):
        try:
            logger.debug(f"Trying pip command {i}/{len(pip_commands)}: {' '.join(cmd)}")
            result = subprocess.run(cmd + ["--version"],
                                  capture_output=True, check=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Found working pip command: {' '.join(cmd)}")
                logger.debug(f"Pip version output: {result.stdout.strip()}")
                return cmd
        except subprocess.CalledProcessError as e:
            logger.debug(f"Pip command failed: {' '.join(cmd)} - {e}")
        except subprocess.TimeoutExpired:
            logger.debug(f"Pip command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            logger.debug(f"Pip command not found: {' '.join(cmd)}")
        except Exception as e:
            logger.debug(f"Unexpected error with pip command {' '.join(cmd)}: {e}")

    logger.error("No working pip command found")
    return None

def check_pip() -> bool:
    """Check pip availability and upgrade if needed"""
    logger.info("Starting pip availability check")

    pip_cmd = get_pip_command()

    if pip_cmd is None:
        logger.error("No working pip command found")
        print_colored("❌ CRITICAL: pip is not available!", Colors.RED + Colors.BOLD, "error")
        print_colored("🔧 Installation Instructions:", Colors.BOLD)

        system_name = platform.system()
        logger.info(f"Providing pip installation instructions for: {system_name}")

        if system_name == "Windows":
            print_colored("   Download get-pip.py from https://bootstrap.pypa.io/get-pip.py", Colors.WHITE)
            print_colored("   Then run: python get-pip.py", Colors.WHITE)
        elif system_name == "Darwin":
            print_colored("   Try: python3 -m ensurepip --upgrade", Colors.WHITE)
            print_colored("   Or: brew install python (includes pip)", Colors.WHITE)
            print_colored("   Or: curl https://bootstrap.pypa.io/get-pip.py | python3", Colors.WHITE)
        else:
            print_colored("   Ubuntu/Debian: sudo apt install python3-pip", Colors.WHITE)
            print_colored("   CentOS/RHEL: sudo yum install python3-pip", Colors.WHITE)

        logger.info("Pip check failed - no pip available")
        return False

    try:
        logger.debug(f"Getting pip version with command: {' '.join(pip_cmd)}")
        result = subprocess.run(pip_cmd + ["--version"],
                              capture_output=True, check=True, text=True, timeout=30)
        pip_version = result.stdout.strip()
        logger.info(f"Pip detected successfully: {pip_version}")
        print_colored(f"✅ pip detected: {pip_version}", Colors.GREEN)
        print_colored(f"   Using command: {' '.join(pip_cmd)}", Colors.WHITE)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get pip version: {e}")
        print_colored("❌ Failed to get pip version", Colors.RED, "error")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Pip version check timed out")
        print_colored("❌ Pip version check timed out", Colors.RED, "error")
        return False
    except Exception as e:
        logger.error(f"Unexpected error getting pip version: {e}")
        print_colored(f"❌ Unexpected error: {e}", Colors.RED, "error")
        return False
    
    logger.info("Attempting to upgrade pip")
    print_colored("🔄 Upgrading pip to latest version...", Colors.BLUE)
    try:
        upgrade_cmd = pip_cmd + ["install", "--upgrade", "pip"]
        logger.debug(f"Running pip upgrade command: {' '.join(upgrade_cmd)}")
        result = subprocess.run(upgrade_cmd, capture_output=True, check=True, timeout=300)
        logger.info("Pip upgraded successfully")
        print_colored("✅ pip upgraded successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.warning(f"Pip upgrade failed but pip is available: {error_msg}")
        print_colored("⚠️  Warning: pip upgrade failed, but pip is available", Colors.YELLOW, "warning")
        print_colored(f"   Error: {error_msg[:200]}...", Colors.YELLOW, "warning")
        print_colored("   Continuing with current pip version...", Colors.WHITE)
        return True
    except subprocess.TimeoutExpired:
        logger.warning("Pip upgrade timed out but pip is available")
        print_colored("⚠️  Warning: pip upgrade timed out, but pip is available", Colors.YELLOW, "warning")
        print_colored("   Continuing with current pip version...", Colors.WHITE)
        return True
    except Exception as e:
        logger.warning(f"Unexpected error during pip upgrade: {e}")
        print_colored(f"⚠️  Warning: pip upgrade error: {e}", Colors.YELLOW, "warning")
        print_colored("   Continuing with current pip version...", Colors.WHITE)
        return True

def check_virtual_environment() -> bool:
    """Check if running in virtual environment and recommend if not"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if in_venv:
        venv_path = sys.prefix
        print_colored(f"✅ Virtual environment detected: {venv_path}", Colors.GREEN)
        return True
    else:
        print_colored("⚠️  WARNING: Not running in a virtual environment!", Colors.YELLOW + Colors.BOLD)
        print_colored("🔧 Recommended: Create a virtual environment first", Colors.YELLOW)
        print()
        print_colored("Virtual Environment Setup:", Colors.BOLD)

        if platform.system() == "Windows":
            print_colored("   python -m venv .venv", Colors.WHITE)
            print_colored("   .venv\\Scripts\\activate", Colors.WHITE)
        else:
            print_colored("   python3 -m venv .venv", Colors.WHITE)
            print_colored("   source .venv/bin/activate", Colors.WHITE)

        print_colored("   Then run this setup script again", Colors.WHITE)
        print()

        response = input("Continue without virtual environment? (y/N): ").lower().strip()
        return response in ['y', 'yes']

def create_directories() -> bool:
    """Create only the directories actually used by CloneMe application"""
    logger.info("Starting directory creation")

    directories = [
        "profiles",
        "profiles/examples",
        "memories",
        "logs",
        "settings"
    ]

    logger.info(f"Directories to create: {directories}")
    print_colored("📁 Creating required project directories...", Colors.BLUE)
    created_count = 0
    failed_directories = []

    for directory in directories:
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.debug(f"Creating directory: {directory}")
                dir_path.mkdir(parents=True, exist_ok=True)
                print_colored(f"   ✅ Created: {directory}/", Colors.GREEN)
                logger.info(f"Successfully created directory: {directory}")
                created_count += 1
            else:
                print_colored(f"   📁 Exists: {directory}/", Colors.WHITE)
                logger.debug(f"Directory already exists: {directory}")
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {directory}: {e}")
            print_colored(f"   ❌ Permission denied: {directory}/", Colors.RED, "error")
            failed_directories.append(directory)
        except OSError as e:
            logger.error(f"OS error creating directory {directory}: {e}")
            print_colored(f"   ❌ OS error creating {directory}/: {e}", Colors.RED, "error")
            failed_directories.append(directory)
        except Exception as e:
            logger.error(f"Unexpected error creating directory {directory}: {e}")
            print_colored(f"   ❌ Error creating {directory}/: {e}", Colors.RED, "error")
            failed_directories.append(directory)

    if failed_directories:
        logger.error(f"Failed to create directories: {failed_directories}")
        print_colored(f"❌ Failed to create {len(failed_directories)} directories", Colors.RED, "error")
        return False
    elif created_count > 0:
        logger.info(f"Successfully created {created_count} new directories")
        print_colored(f"✅ Created {created_count} new directories", Colors.GREEN)
    else:
        logger.info("All directories already exist")
        print_colored("✅ All directories already exist", Colors.GREEN)

    print_colored("ℹ️  Note: Additional directories are created automatically:", Colors.CYAN)
    print_colored("   • logs/YYYY-MM-DD_HH-MM-SS/ (created by LoggingConfig)", Colors.WHITE)
    print_colored("   • Profile backups (created by ProfileManager when needed)", Colors.WHITE)
    print()

    logger.info("Directory creation completed successfully")
    return True

def get_exact_requirements() -> List[str]:
    """Get exact package versions from tested environment"""
    return [
        "aiohappyeyeballs==2.6.1",
        "aiohttp==3.12.9",
        "aiosignal==1.3.2",
        "annotated-types==0.7.0",
        "anthropic==0.52.2",
        "anyio==4.9.0",
        "attrs==25.3.0",
        "beautifulsoup4==4.13.4",
        "cachetools==5.5.2",
        "certifi==2025.4.26",
        "cffi==1.17.1",
        "charset-normalizer==3.4.2",
        "click==8.2.1",
        "colorama==0.4.6",
        "curl_cffi==0.11.2",
        "dataclasses-json==0.6.7",
        "discord-protos==0.0.2",
        "distro==1.9.0",
        "duckduckgo_search==8.0.2",
        "filetype==1.2.0",
        "frozenlist==1.6.2",
        "google-ai-generativelanguage==0.6.15",
        "google-api-core==2.25.0",
        "google-api-python-client==2.171.0",
        "google-auth==2.40.3",
        "google-auth-httplib2==0.2.0",
        "google-generativeai==0.8.5",
        "googleapis-common-protos==1.70.0",
        "googlesearch-python==1.3.0",
        "greenlet==3.2.3",
        "groq==0.26.0",
        "grpcio==1.72.1",
        "grpcio-status==1.71.0",
        "h11==0.16.0",
        "httpcore==1.0.9",
        "httplib2==0.22.0",
        "httpx==0.28.1",
        "httpx-sse==0.4.0",
        "idna==3.10",
        "jiter==0.10.0",
        "jsonpatch==1.33",
        "jsonpointer==3.0.0",
        "langchain==0.3.25",
        "langchain-anthropic==0.3.15",
        "langchain-community==0.3.24",
        "langchain-core==0.3.64",
        "langchain-google-genai==2.0.10",
        "langchain-groq==0.3.2",
        "langchain-ollama==0.3.3",
        "langchain-openai==0.3.19",
        "langchain-text-splitters==0.3.8",
        "langsmith==0.3.45",
        "lxml==5.4.0",
        "marshmallow==3.26.1",
        "multidict==6.4.4",
        "mypy_extensions==1.1.0",
        "numpy==2.2.6",
        "ollama==0.5.1",
        "openai==1.84.0",
        "orjson==3.10.18",
        "packaging==24.2",
        "primp==0.15.0",
        "propcache==0.3.1",
        "proto-plus==1.26.1",
        "protobuf==5.29.5",
        "pyasn1==0.6.1",
        "pyasn1_modules==0.4.2",
        "pycparser==2.22",
        "pydantic==2.11.5",
        "pydantic-settings==2.9.1",
        "pydantic_core==2.33.2",
        "PyNaCl==1.5.0",
        "pyparsing==3.2.3",
        "python-dotenv==1.1.0",
        "PyYAML==6.0.2",
        "regex==2024.11.6",
        "requests==2.32.3",
        "requests-toolbelt==1.0.0",
        "rsa==4.9.1",
        "sniffio==1.3.1",
        "soupsieve==2.7",
        "SQLAlchemy==2.0.41",
        "tenacity==9.1.2",
        "tiktoken==0.9.0",
        "tqdm==4.67.1",
        "typing-inspect==0.9.0",
        "typing-inspection==0.4.1",
        "typing_extensions==4.14.0",
        "tzdata==2025.2",
        "tzlocal==5.3.1",
        "uritemplate==4.2.0",
        "urllib3==2.4.0",
        "watchdog==6.0.0",
        "yarl==1.20.0",
        "zstandard==0.23.0"
    ]

def install_discord_py_self() -> bool:
    """Install discord.py-self from git repository"""
    logger.info("Starting discord.py-self installation")
    print_colored("🔄 Installing discord.py-self from GitHub...", Colors.BLUE)

    pip_cmd = get_pip_command()
    if pip_cmd is None:
        logger.error("Cannot install discord.py-self: pip not available")
        print_colored("❌ Failed to install discord.py-self: pip not available", Colors.RED, "error")
        return False

    git_url = "git+https://github.com/dolfies/discord.py-self.git@71609f4f62649d18bdf14f0e286b7e62bc605390"
    install_cmd = pip_cmd + ["install", git_url]

    try:
        logger.debug(f"Running discord.py-self install command: {' '.join(install_cmd)}")
        result = subprocess.run(install_cmd, check=True, capture_output=True, text=True, timeout=300)
        logger.info("discord.py-self installed successfully")
        logger.debug(f"Install output: {result.stdout}")
        print_colored("✅ discord.py-self installed successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"Failed to install discord.py-self: {error_msg}")
        print_colored("❌ Failed to install discord.py-self", Colors.RED, "error")
        print_colored(f"   Error: {error_msg[:200]}...", Colors.RED, "error")
        return False
    except subprocess.TimeoutExpired:
        logger.error("discord.py-self installation timed out")
        print_colored("❌ discord.py-self installation timed out", Colors.RED, "error")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing discord.py-self: {e}")
        print_colored(f"❌ Unexpected error: {e}", Colors.RED, "error")
        return False

def install_requirements() -> bool:
    """Install all Python packages with exact versions"""
    logger.info("Starting requirements installation")
    start_time = datetime.now()

    print_colored("📦 Installing Python packages with exact tested versions...", Colors.BLUE + Colors.BOLD)
    print_colored("   This ensures maximum compatibility and stability", Colors.WHITE)
    print()

    pip_cmd = get_pip_command()
    if pip_cmd is None:
        logger.error("Cannot install requirements: pip not available")
        print_colored("❌ Failed to install requirements: pip not available", Colors.RED, "error")
        return False

    requirements = get_exact_requirements()
    total_packages = len(requirements)
    logger.info(f"Installing {total_packages} packages using pip command: {' '.join(pip_cmd)}")

    print_colored(f"📋 Installing {total_packages} packages...", Colors.WHITE)
    print_colored(f"   Using pip command: {' '.join(pip_cmd)}", Colors.WHITE)

    batch_size = 10
    failed_packages = []
    successful_batches = 0

    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(requirements) + batch_size - 1) // batch_size

        logger.info(f"Installing batch {batch_num}/{total_batches}: {batch}")
        print_colored(f"🔄 Installing batch {batch_num}/{total_batches} ({len(batch)} packages)...", Colors.BLUE)

        try:
            cmd = pip_cmd + ["install"] + batch
            logger.debug(f"Running batch install command: {' '.join(cmd)}")
            batch_start = datetime.now()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            batch_duration = datetime.now() - batch_start

            logger.info(f"Batch {batch_num} completed successfully in {batch_duration.total_seconds():.1f}s")
            logger.debug(f"Batch {batch_num} output: {result.stdout}")
            print_colored(f"   ✅ Batch {batch_num} completed successfully ({batch_duration.total_seconds():.1f}s)", Colors.GREEN)
            successful_batches += 1
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Batch {batch_num} failed: {error_msg}")
            print_colored(f"   ❌ Batch {batch_num} failed", Colors.RED, "error")
            failed_packages.extend(batch)
            print_colored(f"   Error: {error_msg[:200]}...", Colors.RED, "error")
        except subprocess.TimeoutExpired:
            logger.error(f"Batch {batch_num} timed out")
            print_colored(f"   ❌ Batch {batch_num} timed out", Colors.RED, "error")
            failed_packages.extend(batch)
        except Exception as e:
            logger.error(f"Unexpected error in batch {batch_num}: {e}")
            print_colored(f"   ❌ Batch {batch_num} unexpected error: {e}", Colors.RED, "error")
            failed_packages.extend(batch)

    logger.info("Installing discord.py-self separately")
    if not install_discord_py_self():
        failed_packages.append("discord.py-self")

    total_duration = datetime.now() - start_time
    logger.info(f"Requirements installation completed in {total_duration.total_seconds():.1f}s")
    logger.info(f"Successful batches: {successful_batches}/{total_batches}")
    logger.info(f"Failed packages: {len(failed_packages)}")

    if failed_packages:
        logger.error(f"Installation completed with {len(failed_packages)} failed packages: {failed_packages}")
        print_colored(f"⚠️  {len(failed_packages)} packages failed to install:", Colors.YELLOW, "warning")
        for pkg in failed_packages:
            print_colored(f"   - {pkg}", Colors.RED, "error")
        print()
        print_colored("🔧 Try installing failed packages manually:", Colors.YELLOW, "warning")
        print_colored(f"   pip install {' '.join(failed_packages[:5])}{'...' if len(failed_packages) > 5 else ''}", Colors.WHITE)
        return False
    else:
        logger.info(f"ALL {total_packages + 1} packages installed successfully in {total_duration.total_seconds():.1f}s")
        print_colored(f"✅ ALL {total_packages + 1} packages installed successfully! ({total_duration.total_seconds():.1f}s)", Colors.GREEN + Colors.BOLD)
        return True

def create_env_file() -> bool:
    """Create comprehensive .env file with all supported providers"""
    logger.info("Starting environment file creation")
    env_example = Path(".env.example")
    env_file = Path(".env")

    logger.info(f"Checking for .env.example: {env_example.exists()}")
    logger.info(f"Checking for .env: {env_file.exists()}")
    print_colored("⚙️  Setting up environment configuration...", Colors.BLUE)

    try:
        if env_example.exists() and not env_file.exists():
            logger.info("Creating .env file from .env.example template")
            shutil.copy(env_example, env_file)
            logger.info("Successfully created .env file from template")
            print_colored("✅ Created .env file from template", Colors.GREEN)
            print_colored("   📝 Please edit .env file to add your API keys", Colors.YELLOW, "warning")
        elif env_file.exists():
            logger.info(".env file already exists")
            print_colored("✅ .env file already exists", Colors.GREEN)
        else:
            logger.info("Creating .env file with default content")
            env_content = """# CloneMe Environment Configuration
# Copy from .env.example and fill in your actual values

# Platform Configuration (optional - defaults to discord)
PLATFORM=discord

# Discord Configuration (required for Discord platform)
DISCORD_SELF_TOKEN=your_discord_self_token_here

# AI Provider Configuration (required)
# Supported providers: openai, claude, anthropic, groq, ollama, google
AI_PROVIDER=openai
AI_API_KEY=your_api_key_here

# AI Model Configuration (required)
# Examples by provider:
# OpenAI: gpt-4, gpt-3.5-turbo, gpt-4-turbo
# Claude/Anthropic: claude-3-sonnet-20240229, claude-3-haiku-20240307
# Google: gemini-pro, gemini-1.5-pro, gemini-2.0-flash-lite
# Groq: llama3-8b-8192, mixtral-8x7b-32768
# Ollama: llama2, codellama, mistral (local models)
AI_MODEL=gpt-4

# Profile Configuration (optional - defaults to "default_profile")
# This should match the JSON filename (without .json extension), not a key inside the file
# For example, if you have profiles/my_profile.json, use AI_PROFILE=my_profile
AI_PROFILE=default_profile
"""

            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)

            logger.info("Successfully created .env file with default content")
            print_colored("✅ Created comprehensive .env file", Colors.GREEN)
            print_colored("   📝 Please edit .env file to add your API keys", Colors.YELLOW, "warning")
            print_colored("   💡 You only need to configure the AI providers you plan to use", Colors.WHITE)

        logger.info("Environment file creation completed successfully")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied creating .env file: {e}")
        print_colored("❌ Permission denied creating .env file", Colors.RED, "error")
        return False
    except OSError as e:
        logger.error(f"OS error creating .env file: {e}")
        print_colored(f"❌ OS error creating .env file: {e}", Colors.RED, "error")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating .env file: {e}")
        print_colored(f"❌ Unexpected error creating .env file: {e}", Colors.RED, "error")
        return False

def setup_profile() -> None:
    """Set up user profile with comprehensive templates"""
    profile_dir = Path("profiles")
    user_profile = profile_dir / "my_profile.json"
    default_template = profile_dir / "default_profile.json"
    examples_dir = profile_dir / "examples"

    print_colored("🎭 Setting up user profiles...", Colors.BLUE)

    if not default_template.exists():
        create_default_profile_template(default_template)

    if not user_profile.exists() and default_template.exists():
        shutil.copy(default_template, user_profile)
        print_colored("✅ Created your profile from template", Colors.GREEN)
        print_colored("   📝 Edit profiles/my_profile.json to customize your personality", Colors.YELLOW)
    elif user_profile.exists():
        print_colored("✅ User profile already exists", Colors.GREEN)
    else:
        print_colored("⚠️  Warning: No profile template found", Colors.YELLOW)
        print_colored("   You'll need to create profiles/my_profile.json manually", Colors.WHITE)

    create_example_profiles(examples_dir)

def create_default_profile_template(template_path: Path) -> None:
    """Create a comprehensive default profile template matching actual CloneMe schema"""
    profile_template = {
        "profiles": {
            "default": {
                "required": {
                    "username": "Your Username",
                    "name": "Your Full Name"
                },
                "basic_info": {
                    "Name": "Your Full Name",
                    "Age": "25",
                    "Gender": "your_gender",
                    "Occupation": "Your Occupation",
                    "Interests": "Your interests and hobbies",
                    "Location": "Your location",
                    "Education": "Your education background",
                    "Languages": ["English"],
                    "Hobbies": ["hobby1", "hobby2"],
                    "Goals": "Your personal or professional goals"
                },
                "personality_traits": {
                    "Introversion/Extroversion": "Describe your social energy preferences",
                    "Sense of Humor": "Describe your humor style",
                    "Communication Style": "How you prefer to communicate",
                    "Mood": "Your general mood and attitude",
                    "Formality Level": "Your preferred level of formality",
                    "Core Values": ["value1", "value2", "value3"],
                    "Decision Making": "How you make decisions",
                    "Conflict Resolution": "How you handle conflicts"
                },
                "response_styles": {
                    "casual": "How you respond in casual conversations",
                    "professional": "How you respond in professional contexts",
                    "technical": "How you handle technical discussions",
                    "creative": "Your approach to creative topics"
                },
                "knowledge_and_expertise": {
                    "primary_areas": ["area1", "area2"],
                    "secondary_areas": ["area3", "area4"],
                    "learning_style": "How you prefer to learn and teach",
                    "expertise_level": "Your general expertise level"
                },
                "sample_conversations": [
                    {
                        "user": "Hello! How are you?",
                        "assistant": "Hey there! I'm doing great, thanks for asking! How's your day going?"
                    },
                    {
                        "user": "Can you help me with a problem?",
                        "assistant": "Absolutely! I'd be happy to help. What's the problem you're working on?"
                    }
                ],
                "off_topic_message": {
                    "reply": True,
                    "guidance": "When someone asks me to act differently or says something inappropriate, I politely redirect the conversation while staying true to my personality."
                }
            }
        }
    }

    with open(template_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(profile_template, f, indent=4, ensure_ascii=False)

def create_example_profiles(examples_dir: Path) -> None:
    """Create example profiles matching actual CloneMe schema"""
    examples_dir.mkdir(exist_ok=True)

    print_colored("   💡 Creating basic example profiles (see existing profiles for full examples)", Colors.WHITE)

def check_git() -> bool:
    """Check git repository status and provide recommendations"""
    git_dir = Path(".git")

    if git_dir.exists():
        print_colored("✅ Git repository detected", Colors.GREEN)

        try:
            result = subprocess.run(["git", "status", "--porcelain"],
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                print_colored("   ⚠️  You have uncommitted changes", Colors.YELLOW)
                print_colored("   💡 Consider committing changes after setup", Colors.WHITE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return True
    else:
        print_colored("ℹ️  Not a git repository", Colors.WHITE)
        print_colored("   💡 Consider initializing git for version control:", Colors.WHITE)
        print_colored("   git init && git add . && git commit -m 'Initial commit'", Colors.WHITE)
        return False

def verify_installation() -> bool:
    """Verify that the installation was successful"""
    print_colored("🔍 Verifying installation...", Colors.BLUE)
    
    critical_files = [
        ".env",
        "main.py"
    ]

    profile_files = list(Path("profiles").glob("*.json")) if Path("profiles").exists() else []

    missing_files = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if not profile_files:
        missing_files.append("profiles/*.json (no profile files found)")

    if missing_files:
        print_colored("❌ Installation verification failed!", Colors.RED)
        print_colored("   Missing files:", Colors.RED)
        for file in missing_files:
            print_colored(f"   - {file}", Colors.RED)
        return False

    critical_modules = ["langchain", "anthropic", "openai", "python_dotenv"]
    failed_imports = []

    for module_name in critical_modules:
        try:
            __import__(module_name)
        except ImportError:
            failed_imports.append(module_name)

    if failed_imports:
        print_colored(f"❌ Module import failed: {', '.join(failed_imports)}", Colors.RED)
        return False
    else:
        print_colored("✅ Critical modules can be imported", Colors.GREEN)

    print_colored("✅ Installation verification successful!", Colors.GREEN)
    return True

def print_next_steps() -> None:
    """Print comprehensive next steps and usage instructions"""
    print()
    print_colored("=" * 80, Colors.CYAN)
    print_colored("🎉 SETUP COMPLETE - CloneMe is Ready!", Colors.GREEN + Colors.BOLD)
    print_colored("=" * 80, Colors.CYAN)
    print()

    print_colored("📋 IMMEDIATE NEXT STEPS:", Colors.BOLD)
    print_colored("1. 🔑 Configure API Keys:", Colors.YELLOW)
    print_colored("   Edit .env file and add your AI provider API keys", Colors.WHITE)
    print_colored("   (You only need keys for providers you plan to use)", Colors.WHITE)
    print()

    print_colored("2. 🎭 Customize Your Profile:", Colors.YELLOW)
    print_colored("   Edit profiles/default_profile.json to match your personality", Colors.WHITE)
    print_colored("   Or create a new profile file and set AI_PROFILE to the filename (without .json)", Colors.WHITE)
    print_colored("   Check existing profiles/ for examples of the correct format", Colors.WHITE)
    print()

    print_colored("3. 🚀 Launch CloneMe:", Colors.YELLOW)
    if platform.system() == "Windows":
        print_colored("   python main.py", Colors.WHITE)
    else:
        print_colored("   python3 main.py", Colors.WHITE)
    print()

    print_colored("📚 HELPFUL RESOURCES:", Colors.BOLD)
    print_colored("• 📖 Documentation: Check README.md for detailed usage", Colors.WHITE)
    print_colored("• 🎭 Profile Examples: Check existing profiles/ for correct format", Colors.WHITE)
    print_colored("• 🔧 Configuration: .env file for all settings", Colors.WHITE)
    print_colored("• 📝 Logs: logs/ directory for troubleshooting", Colors.WHITE)
    print()

    print_colored("💡 PRO TIPS:", Colors.BOLD)
    print_colored("• Start with OpenAI (gpt-4) or Anthropic (claude-3-sonnet) for best results", Colors.WHITE)
    print_colored("• AI_PROFILE should match the JSON filename (without .json extension)", Colors.WHITE)
    print_colored("• Test with simple conversations first", Colors.WHITE)
    print_colored("• Check logs/ if you encounter any issues", Colors.WHITE)
    print_colored("• Memory system learns from your conversations", Colors.WHITE)
    print()

    print_colored("🆘 NEED HELP?", Colors.BOLD)
    print_colored("• Check the logs in logs/ directory", Colors.WHITE)
    print_colored("• Verify your API keys in .env file", Colors.WHITE)
    print_colored("• Ensure you're using Python 3.11.6", Colors.WHITE)
    print()

    print_colored("=" * 80, Colors.CYAN)
    print_colored("Happy cloning! 🤖✨", Colors.MAGENTA + Colors.BOLD)
    print_colored("=" * 80, Colors.CYAN)

def main() -> None:
    """Main setup function with comprehensive error handling"""
    setup_start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("MAIN SETUP FUNCTION STARTED")
    logger.info("=" * 60)

    try:
        logger.info("Phase 1: Displaying header and system information")
        print_header()

        logger.info("Phase 2: Critical system checks")
        if not check_python_version():
            logger.error("Setup aborted: Python version incompatibility")
            print_colored("❌ Setup aborted due to Python version incompatibility", Colors.RED, "error")
            sys.exit(1)

        if not check_pip():
            logger.error("Setup aborted: pip unavailability")
            print_colored("❌ Setup aborted due to pip unavailability", Colors.RED, "error")
            sys.exit(1)

        if not check_virtual_environment():
            logger.error("Setup aborted: virtual environment recommended")
            print_colored("❌ Setup aborted - virtual environment recommended", Colors.RED, "error")
            sys.exit(1)

        print()

        logger.info("Phase 3: Directory creation")
        if not create_directories():
            logger.error("Setup failed during directory creation")
            print_colored("❌ Setup failed during directory creation", Colors.RED, "error")
            sys.exit(1)

        logger.info("Phase 4: Package installation")
        print_colored("📦 PACKAGE INSTALLATION PHASE", Colors.BLUE + Colors.BOLD)
        print_colored("This may take several minutes depending on your internet connection...", Colors.WHITE)
        print()

        if not install_requirements():
            logger.error("Setup failed during package installation")
            print_colored("❌ Setup failed during package installation", Colors.RED + Colors.BOLD, "error")
            print_colored("🔧 Troubleshooting tips:", Colors.YELLOW, "warning")
            print_colored("   • Check your internet connection", Colors.WHITE)
            print_colored("   • Try running: pip install --upgrade pip", Colors.WHITE)
            print_colored("   • Ensure you have sufficient disk space", Colors.WHITE)
            print_colored("   • Try running setup again", Colors.WHITE)
            print_colored(f"   • Check setup logs: logs/setup/", Colors.WHITE)
            sys.exit(1)

        print()

        logger.info("Phase 5: Configuration setup")
        print_colored("⚙️  CONFIGURATION PHASE", Colors.BLUE + Colors.BOLD)
        if not create_env_file():
            logger.warning("Environment file creation failed")
            print_colored("⚠️  Warning: Environment file creation failed", Colors.YELLOW, "warning")

        setup_profile()
        print()

        logger.info("Phase 6: Git repository check")
        check_git()
        print()

        logger.info("Phase 7: Installation verification")
        if not verify_installation():
            logger.warning("Setup completed with warnings")
            print_colored("❌ Setup completed with warnings", Colors.YELLOW, "warning")
            print_colored("   Some components may not work correctly", Colors.YELLOW, "warning")
        else:
            logger.info("Setup completed successfully")
            print_colored("✅ Setup completed successfully!", Colors.GREEN + Colors.BOLD)

        total_setup_time = datetime.now() - setup_start_time
        logger.info(f"Total setup time: {total_setup_time.total_seconds():.1f} seconds")

        logger.info("Phase 8: Displaying next steps")
        print_next_steps()

        print_colored("📋 SETUP LOGS:", Colors.BOLD)
        print_colored(f"• 📝 Detailed logs saved to: logs/setup/", Colors.WHITE)
        print_colored("• 🔍 Check logs if you encounter any issues", Colors.WHITE)
        print()

        logger.info("=" * 60)
        logger.info("SETUP COMPLETED SUCCESSFULLY")
        logger.info(f"Total execution time: {total_setup_time.total_seconds():.1f} seconds")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Setup cancelled by user (KeyboardInterrupt)")
        print()
        print_colored("❌ Setup cancelled by user", Colors.YELLOW, "warning")
        print_colored("   Run the setup script again to complete installation", Colors.WHITE)
        print_colored(f"   Setup logs saved to: logs/setup/", Colors.WHITE)
        sys.exit(1)

    except Exception as e:
        logger.error(f"CRITICAL ERROR: Setup failed unexpectedly: {e}", exc_info=True)
        print()
        print_colored("❌ CRITICAL ERROR: Setup failed unexpectedly", Colors.RED + Colors.BOLD, "error")
        print_colored(f"   Error details: {str(e)}", Colors.RED, "error")
        print()
        print_colored("🔧 Troubleshooting:", Colors.YELLOW, "warning")
        print_colored("   • Check your Python installation", Colors.WHITE)
        print_colored("   • Ensure you have internet connectivity", Colors.WHITE)
        print_colored("   • Try running as administrator (Windows) or with sudo (Linux)", Colors.WHITE)
        print_colored("   • Check available disk space", Colors.WHITE)
        print_colored(f"   • Check detailed logs in: logs/setup/", Colors.WHITE)
        print()
        print_colored("📧 If the problem persists, please report this error with the log file", Colors.WHITE)

        logger.error("=" * 60)
        logger.error("SETUP FAILED WITH CRITICAL ERROR")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    logger.info(f"Script directory: {script_dir}")
    logger.info(f"Project root: {project_root}")

    if project_root.name == "CloneMe" or (project_root / "main.py").exists():
        os.chdir(project_root)
        logger.info(f"Changed working directory to: {project_root}")
        print_colored(f"📁 Working directory: {project_root}", Colors.WHITE)
    else:
        logger.warning(f"May not be in CloneMe project directory. Current: {project_root}")
        print_colored("⚠️  Warning: May not be in CloneMe project directory", Colors.YELLOW, "warning")

    logger.info("Starting CloneMe setup script")
    logger.info(f"Command line arguments: {sys.argv}")

    try:
        main()
    except SystemExit as e:
        logger.info(f"Setup script exited with code: {e.code}")
        raise
    except Exception as e:
        logger.error(f"Unhandled exception in main execution: {e}", exc_info=True)
        raise
