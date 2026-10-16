import os

import pytest

from app.config import get_settings
from app.llm.client import LLMClient

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.getenv("NEBIUS_API_KEY"), reason="no NEBIUS_API_KEY"),
]


@pytest.mark.parametrize("tier", ["fast", "mid", "deep"])
async def test_live_tier(tier):
    s = get_settings()
    if not s.model_for(tier):
        pytest.skip(f"MODEL_{tier.upper()} unset")
    r = await LLMClient(s).chat(tier, [{"role": "user", "content": "Say OK"}], max_tokens=16)
    assert r.text
