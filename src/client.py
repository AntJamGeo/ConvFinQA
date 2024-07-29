from huggingface_hub import InferenceClient

class Client:
    """A wrapper class for HuggingFace InferenceClient."""

    def __init__(self, model: str, token: str):
        self._client = InferenceClient(model, token)

    def generate(self, messages: str, max_tokens: int = 500) -> str:
        return self._client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
        ).choices[0].message.content.strip()