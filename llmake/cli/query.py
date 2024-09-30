import sys
from os import getenv
from pathlib import Path

from litellm import completion


def query(input_file: str, output_file: str) -> str:
    messages = [{"content": Path(input_file).read_text(), "role": "user"}]
    model = getenv("MODEL")
    if not model:
        print("Please set the MODEL environment variable to the model you want to use.")
        print(
            "You can find models in the LiteLLM documentation. For OpenAI models, you can refer to the following page:"
        )
        print("https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models")
        sys.exit(-1)
    response = completion(model=model, messages=messages)
    return response.choices[0].message.content  # type: ignore [reportArgumentType]
