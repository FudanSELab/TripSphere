import json
from pathlib import Path

import pytest
from celery import Task
from pytest_mock import MockerFixture, MockType

from review_summary.models import TextUnit


@pytest.fixture
def mock_task(mocker: MockerFixture) -> MockType:
    """Mock Celery Task object."""
    mock_task: MockType = mocker.MagicMock(spec=Task)
    return mock_task


@pytest.fixture
def text_units_parquet_uuid() -> str:
    return "019b7e54-d609-70a1-9142-c75f8504cd42"


@pytest.fixture
def text_units() -> list[TextUnit]:
    """Load text units from fixtures file."""
    fixtures_path = Path("tests") / "fixtures" / "text_units.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        text_units_data = json.load(f)
    return [TextUnit.model_validate(unit) for unit in text_units_data]


@pytest.fixture
def graph_parquet_uuid() -> str:
    return "019b7ecb-616b-70ce-af4a-755199b8064b"


@pytest.fixture
def final_graph_parquet_uuid() -> str:
    return "019b87f2-4107-7199-80ff-3d24c91943ad"
