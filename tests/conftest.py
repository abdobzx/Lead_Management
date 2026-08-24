import os
import pytest
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables before running any tests
load_env_file()

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Ensure environment variables are loaded for all tests"""
    assert 'ANTHROPIC_API_KEY' in os.environ, "ANTHROPIC_API_KEY must be set in environment or .env file (agents run on Claude, not xAI)"
    yield