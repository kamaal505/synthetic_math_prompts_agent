from core.llm.openai_utils import extract_tokens_from_response


class MockUsage:
    def __init__(self, prompt_tokens=None, completion_tokens=None, input_tokens=None, output_tokens=None):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockResponse:
    def __init__(self, usage=None, response_metadata=None):
        self.usage = usage
        self.response_metadata = response_metadata


def test_extract_tokens_from_chat_format():
    response = MockResponse(usage=MockUsage(prompt_tokens=42, completion_tokens=100))
    tokens = extract_tokens_from_response(response)
    assert tokens == (42, 100)


def test_extract_tokens_from_response_format():
    metadata = type("Meta", (), {"usage": MockUsage(input_tokens=80, output_tokens=160)})
    response = MockResponse(response_metadata=metadata)
    tokens = extract_tokens_from_response(response)
    assert tokens == (80, 160)


def test_extract_tokens_missing_all():
    response = MockResponse()
    tokens = extract_tokens_from_response(response)
    assert tokens == (0, 0)
