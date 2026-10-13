import pytest
from makma.store import Store
from makma.kernel import seed
from makma.config import Settings

@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path,token_budget=100000,scheduler_interval=.01)

@pytest.fixture
def store(tmp_path):
    result=Store(tmp_path/"test.sqlite3")
    seed(result)
    return result

