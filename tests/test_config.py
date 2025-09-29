import os
import tempfile
import json
import pytest
from utils.config import Config

@pytest.fixture
def sample_config_dict():
    return {
        "DB_PATH": "test.db",
        "STATE_PATH": "state.json",
        "SFTP_HOST": "localhost",
        "SFTP_PORT": 22,
        "SFTP_USER": "user",
        "SFTP_PASS": "pass",
        "SSH_KEY_PATH": "/home/user/.ssh/id_rsa",
        "PATHS": ["/remote/dir1", "/remote/dir2"],
        "SLEEP_SECONDS": 60
    }

@pytest.fixture
def sample_config_file(sample_config_dict):
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        json.dump(sample_config_dict, tmp)
        tmp.flush()
        yield tmp.name
    os.remove(tmp.name)

def test_load_config(sample_config_file, sample_config_dict):
    config = Config(sample_config_file)
    assert config.get("DB_PATH").endswith(sample_config_dict["DB_PATH"])
    assert config.get("STATE_PATH") == sample_config_dict["STATE_PATH"]
    assert config.get("SFTP_HOST") == sample_config_dict["SFTP_HOST"]
    assert config.get("SFTP_PORT") == sample_config_dict["SFTP_PORT"]
    assert config.get("SFTP_USER") == sample_config_dict["SFTP_USER"]
    assert config.get("SFTP_PASS") == sample_config_dict["SFTP_PASS"]
    assert config.get("SSH_KEY_PATH") == sample_config_dict["SSH_KEY_PATH"]
    assert config.get("PATHS") == sample_config_dict["PATHS"]
    assert config.get("SLEEP_SECONDS") == sample_config_dict["SLEEP_SECONDS"]

def test_remote_path_str(sample_config_dict):
    # REMOTE_PATH as string
    sample_config_dict["PATHS"] = ["/remote/dir"]
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        json.dump(sample_config_dict, tmp)
        tmp.flush()
        config = Config(tmp.name)
        assert config.get("PATHS") == ["/remote/dir"]
    os.remove(tmp.name)

def test_get_and_set(sample_config_file):
    config = Config(sample_config_file)
    config.set("NEW_KEY", "value")
    assert config.get("NEW_KEY") == "value"

def test_save_and_reload(sample_config_file):
    config = Config(sample_config_file)
    config.set("NEW_KEY", 123)
    config.save()
    config2 = Config(sample_config_file)
    assert config2.get("NEW_KEY") == 123

def test_missing_file():
    with pytest.raises(FileNotFoundError):
        Config("/nonexistent/path/config.json")