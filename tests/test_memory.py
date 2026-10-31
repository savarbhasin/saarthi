import uuid

from saarthi.memory import store
from saarthi.memory.transcript import for_memory

CALL = """assistant: नमस्ते सबर जी! बताइए, क्या करना है?
user: pernicious ka matlab batao
assistant: Pernicious का मतलब है छिपकर धीरे-धीरे नुकसान पहुँचाने वाला।
user: aur meri beti ka naam yaad rakhna
assistant: ज़रूर, उसका नाम क्या है?
user: Priya
assistant: Elon Musk announced that he will give every American child a SpaceX share,
and the markets reacted strongly."""


def test_only_the_callers_words_and_saarthis_questions_reach_memory():
    kept = for_memory(CALL)
    assert "user: Priya" in kept and "उसका नाम क्या है?" in kept
    assert "Pernicious का मतलब" not in kept
    assert "Elon Musk" not in kept and "markets reacted" not in kept


def test_a_call_where_the_caller_said_nothing_is_skipped():
    assert for_memory("assistant: हैलो? क्या आप मुझे सुन पा रहे हैं?") == ""


async def test_calls_are_sent_with_extraction_guidance(monkeypatch):
    sent = {}

    class FakeClient:
        async def add(self, namespace, **kwargs):
            sent.update(kwargs, namespace=namespace)

    monkeypatch.setattr(store, "_client", lambda: FakeClient())
    assert await store.add_transcript(uuid.uuid4(), "exec-1", CALL)
    assert sent["supporting_context"] == store.CALL_CONTEXT
    assert "Elon Musk" not in sent["content"]
    assert not await store.add_transcript(uuid.uuid4(), "exec-2", "assistant: हैलो?")
