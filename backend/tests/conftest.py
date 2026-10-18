import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    # Hand-written samples of each shop's response shape; *_real.json are trimmed live captures.
    return lambda name: json.loads((FIXTURES / name).read_text(encoding="utf-8"))
