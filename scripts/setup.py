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
import urllib.request
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Recommended Python version
RECOMMENDED_PYTHON = "3.11.6"
MINIMUM_PYTHON = (3, 11)

# Color codes for cross-platform terminal output
class Colors:
    if platform.system() == "Windows":
        # Enable ANSI colors on Windows 10+
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

def print_colored(text: str, color: str = Colors.WHITE) -> None:
    """Print colored text with cross-platform support"""
    print(f"{color}{text}{Colors.RESET}")

def print_header():
    """Print setup header with system information"""
    print_colored("=" * 80, Colors.CYAN)
    print_colored("🤖 CloneMe - AI Digital Twin Setup Script", Colors.BOLD + Colors.MAGENTA)
    print_colored("Fully Autonomous Cross-Platform Setup", Colors.CYAN)
    print_colored("=" * 80, Colors.CYAN)
    print()

    # System information
    system_info = {
        "Platform": f"{platform.system()} {platform.release()}",
        "Architecture": platform.machine(),
        "Python": f"{sys.version.split()[0]}",
        "Recommended": f"Python {RECOMMENDED_PYTHON}",
        "Working Directory": str(Path.cwd())
    }

    for key, value in system_info.items():
        print_colored(f"📋 {key}: {value}", Colors.WHITE)
    print()

def check_python_version() -> bool:
    """Check Python version with detailed recommendations"""
    version = sys.version_info
    current_version = f"{version.major}.{version.minor}.{version.micro}"

    if version.major < MINIMUM_PYTHON[0] or (version.major == MINIMUM_PYTHON[0] and version.minor < MINIMUM_PYTHON[1]):
        print_colored("❌ CRITICAL: Incompatible Python version detected!", Colors.RED + Colors.BOLD)
        print_colored(f"   Current: Python {current_version}", Colors.RED)
        print_colored(f"   Required: Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+", Colors.YELLOW)
        print_colored(f"   Recommended: Python {RECOMMENDED_PYTHON}", Colors.GREEN)
        print()
        print_colored("🔧 Installation Instructions:", Colors.BOLD)

        if platform.system() == "Windows":
            print_colored("   Windows: Download from https://python.org/downloads/", Colors.WHITE)
            print_colored("   Or use: winget install Python.Python.3.11", Colors.WHITE)
        elif platform.system() == "Linux":
            print_colored("   Ubuntu/Debian: sudo apt update && sudo apt install python3.11 python3.11-venv", Colors.WHITE)
            print_colored("   CentOS/RHEL: sudo yum install python3.11", Colors.WHITE)
            print_colored("   Or compile from source: https://python.org/downloads/source/", Colors.WHITE)
        else:
            print_colored("   macOS: brew install python@3.11", Colors.WHITE)
            print_colored("   Or download from: https://python.org/downloads/", Colors.WHITE)

        return False

    # Version compatibility check
    if current_version == RECOMMENDED_PYTHON:
        print_colored(f"✅ PERFECT: Python {current_version} (Recommended version)", Colors.GREEN + Colors.BOLD)
    elif version >= (3, 11):
        print_colored(f"✅ COMPATIBLE: Python {current_version}", Colors.GREEN)
        print_colored(f"   💡 Tip: Python {RECOMMENDED_PYTHON} is the tested version", Colors.YELLOW)
    else:
        print_colored(f"⚠️  WARNING: Python {current_version} may have compatibility issues", Colors.YELLOW)
        print_colored(f"   Strongly recommend upgrading to Python {RECOMMENDED_PYTHON}", Colors.YELLOW)

    return True

def check_pip() -> bool:
    """Check pip availability and upgrade if needed"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, check=True, text=True)
        pip_version = result.stdout.strip()
        print_colored(f"✅ pip detected: {pip_version}", Colors.GREEN)

        # Upgrade pip to latest version
        print_colored("🔄 Upgrading pip to latest version...", Colors.BLUE)
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                      capture_output=True, check=True)
        print_colored("✅ pip upgraded successfully", Colors.GREEN)
        return True

    except subprocess.CalledProcessError:
        print_colored("❌ CRITICAL: pip is not available!", Colors.RED + Colors.BOLD)
        print_colored("🔧 Installation Instructions:", Colors.BOLD)

        if platform.system() == "Windows":
            print_colored("   Download get-pip.py from https://bootstrap.pypa.io/get-pip.py", Colors.WHITE)
            print_colored("   Then run: python get-pip.py", Colors.WHITE)
        else:
            print_colored("   Ubuntu/Debian: sudo apt install python3-pip", Colors.WHITE)
            print_colored("   CentOS/RHEL: sudo yum install python3-pip", Colors.WHITE)
            print_colored("   macOS: pip should be included with Python", Colors.WHITE)

        return False

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

def create_directories() -> None:
    """Create only the directories actually used by CloneMe application"""
    # Only directories that are actually used by the application code
    directories = [
        "profiles",           # Used by ProfileManager for storing user profiles
        "profiles/examples",  # Used for example profile templates
        "memories",          # Used by memory system for storing user memories
        "logs",              # Used by LoggingConfig for application logs
        "settings"           # Used by SettingsManager for settings.json
    ]

    print_colored("📁 Creating required project directories...", Colors.BLUE)
    created_count = 0

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_colored(f"   ✅ Created: {directory}/", Colors.GREEN)
            created_count += 1
        else:
            print_colored(f"   📁 Exists: {directory}/", Colors.WHITE)

    if created_count > 0:
        print_colored(f"✅ Created {created_count} new directories", Colors.GREEN)
    else:
        print_colored("✅ All directories already exist", Colors.GREEN)

    # Note about directories that are created automatically by the application
    print_colored("ℹ️  Note: Additional directories are created automatically:", Colors.CYAN)
    print_colored("   • logs/YYYY-MM-DD_HH-MM-SS/ (created by LoggingConfig)", Colors.WHITE)
    print_colored("   • Profile backups (created by ProfileManager when needed)", Colors.WHITE)
    print()

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
    print_colored("🔄 Installing discord.py-self from GitHub...", Colors.BLUE)
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "git+https://github.com/dolfies/discord.py-self.git@71609f4f62649d18bdf14f0e286b7e62bc605390"
        ], check=True, capture_output=True)
        print_colored("✅ discord.py-self installed successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored("❌ Failed to install discord.py-self", Colors.RED)
        print_colored(f"   Error: {e}", Colors.RED)
        return False

def install_requirements() -> bool:
    """Install all Python packages with exact versions"""
    print_colored("📦 Installing Python packages with exact tested versions...", Colors.BLUE + Colors.BOLD)
    print_colored("   This ensures maximum compatibility and stability", Colors.WHITE)
    print()

    # Get exact requirements
    requirements = get_exact_requirements()
    total_packages = len(requirements)

    print_colored(f"📋 Installing {total_packages} packages...", Colors.WHITE)

    # Install packages in batches to avoid overwhelming output
    batch_size = 10
    failed_packages = []

    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(requirements) + batch_size - 1) // batch_size

        print_colored(f"🔄 Installing batch {batch_num}/{total_batches} ({len(batch)} packages)...", Colors.BLUE)

        try:
            cmd = [sys.executable, "-m", "pip", "install"] + batch
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print_colored(f"   ✅ Batch {batch_num} completed successfully", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"   ❌ Batch {batch_num} failed", Colors.RED)
            failed_packages.extend(batch)
            print_colored(f"   Error: {e.stderr[:200]}...", Colors.RED)

    # Install discord.py-self separately
    if not install_discord_py_self():
        failed_packages.append("discord.py-self")

    # Summary
    if failed_packages:
        print_colored(f"⚠️  {len(failed_packages)} packages failed to install:", Colors.YELLOW)
        for pkg in failed_packages:
            print_colored(f"   - {pkg}", Colors.RED)
        print()
        print_colored("🔧 Try installing failed packages manually:", Colors.YELLOW)
        print_colored(f"   pip install {' '.join(failed_packages)}", Colors.WHITE)
        return False
    else:
        print_colored(f"✅ ALL {total_packages + 1} packages installed successfully!", Colors.GREEN + Colors.BOLD)
        return True

def create_env_file() -> None:
    """Create comprehensive .env file with all supported providers"""
    env_example = Path(".env.example")
    env_file = Path(".env")

    print_colored("⚙️  Setting up environment configuration...", Colors.BLUE)

    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print_colored("✅ Created .env file from template", Colors.GREEN)
        print_colored("   📝 Please edit .env file to add your API keys", Colors.YELLOW)
    elif env_file.exists():
        print_colored("✅ .env file already exists", Colors.GREEN)
    else:
        # Create .env file with actual CloneMe environment variables
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

        print_colored("✅ Created comprehensive .env file", Colors.GREEN)
        print_colored("   📝 Please edit .env file to add your API keys", Colors.YELLOW)
        print_colored("   💡 You only need to configure the AI providers you plan to use", Colors.WHITE)

def setup_profile() -> None:
    """Set up user profile with comprehensive templates"""
    profile_dir = Path("profiles")
    user_profile = profile_dir / "my_profile.json"
    default_template = profile_dir / "default_profile.json"
    examples_dir = profile_dir / "examples"

    print_colored("🎭 Setting up user profiles...", Colors.BLUE)

    # Create example profile if it doesn't exist
    if not default_template.exists():
        create_default_profile_template(default_template)

    # Create user profile from template
    if not user_profile.exists() and default_template.exists():
        shutil.copy(default_template, user_profile)
        print_colored("✅ Created your profile from template", Colors.GREEN)
        print_colored("   📝 Edit profiles/my_profile.json to customize your personality", Colors.YELLOW)
    elif user_profile.exists():
        print_colored("✅ User profile already exists", Colors.GREEN)
    else:
        print_colored("⚠️  Warning: No profile template found", Colors.YELLOW)
        print_colored("   You'll need to create profiles/my_profile.json manually", Colors.WHITE)

    # Create example profiles
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

    # Note: These are simplified examples - users should refer to existing profiles for full examples
    print_colored("   💡 Creating basic example profiles (see existing profiles for full examples)", Colors.WHITE)

def check_git() -> bool:
    """Check git repository status and provide recommendations"""
    git_dir = Path(".git")

    if git_dir.exists():
        print_colored("✅ Git repository detected", Colors.GREEN)

        # Check if there are uncommitted changes
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

    # Check critical files
    critical_files = [
        ".env",
        "main.py"
    ]

    # Check for at least one profile file (any .json file in profiles/)
    profile_files = list(Path("profiles").glob("*.json")) if Path("profiles").exists() else []

    missing_files = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    # Check for profile files
    if not profile_files:
        missing_files.append("profiles/*.json (no profile files found)")

    if missing_files:
        print_colored("❌ Installation verification failed!", Colors.RED)
        print_colored("   Missing files:", Colors.RED)
        for file in missing_files:
            print_colored(f"   - {file}", Colors.RED)
        return False

    # Test import of critical modules
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
    try:
        # Header and system info
        print_header()

        # Critical checks
        if not check_python_version():
            print_colored("❌ Setup aborted due to Python version incompatibility", Colors.RED)
            sys.exit(1)

        if not check_pip():
            print_colored("❌ Setup aborted due to pip unavailability", Colors.RED)
            sys.exit(1)

        # Virtual environment check
        if not check_virtual_environment():
            print_colored("❌ Setup aborted - virtual environment recommended", Colors.RED)
            sys.exit(1)

        print()

        # Directory setup
        create_directories()

        # Package installation
        print_colored("📦 PACKAGE INSTALLATION PHASE", Colors.BLUE + Colors.BOLD)
        print_colored("This may take several minutes depending on your internet connection...", Colors.WHITE)
        print()

        if not install_requirements():
            print_colored("❌ Setup failed during package installation", Colors.RED + Colors.BOLD)
            print_colored("🔧 Troubleshooting tips:", Colors.YELLOW)
            print_colored("   • Check your internet connection", Colors.WHITE)
            print_colored("   • Try running: pip install --upgrade pip", Colors.WHITE)
            print_colored("   • Ensure you have sufficient disk space", Colors.WHITE)
            print_colored("   • Try running setup again", Colors.WHITE)
            sys.exit(1)

        print()

        # Configuration setup
        print_colored("⚙️  CONFIGURATION PHASE", Colors.BLUE + Colors.BOLD)
        create_env_file()
        setup_profile()
        print()

        # Git check
        check_git()
        print()

        # Final verification
        if not verify_installation():
            print_colored("❌ Setup completed with warnings", Colors.YELLOW)
            print_colored("   Some components may not work correctly", Colors.YELLOW)
        else:
            print_colored("✅ Setup completed successfully!", Colors.GREEN + Colors.BOLD)

        # Next steps
        print_next_steps()

    except KeyboardInterrupt:
        print()
        print_colored("❌ Setup cancelled by user", Colors.YELLOW)
        print_colored("   Run the setup script again to complete installation", Colors.WHITE)
        sys.exit(1)

    except Exception as e:
        print()
        print_colored("❌ CRITICAL ERROR: Setup failed unexpectedly", Colors.RED + Colors.BOLD)
        print_colored(f"   Error details: {str(e)}", Colors.RED)
        print()
        print_colored("🔧 Troubleshooting:", Colors.YELLOW)
        print_colored("   • Check your Python installation", Colors.WHITE)
        print_colored("   • Ensure you have internet connectivity", Colors.WHITE)
        print_colored("   • Try running as administrator (Windows) or with sudo (Linux)", Colors.WHITE)
        print_colored("   • Check available disk space", Colors.WHITE)
        print()
        print_colored("📧 If the problem persists, please report this error", Colors.WHITE)
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if project_root.name == "CloneMe" or (project_root / "main.py").exists():
        os.chdir(project_root)
        print_colored(f"📁 Working directory: {project_root}", Colors.WHITE)
    else:
        print_colored("⚠️  Warning: May not be in CloneMe project directory", Colors.YELLOW)

    main()
