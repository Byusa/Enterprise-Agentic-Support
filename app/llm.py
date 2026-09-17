from langchain_openai import ChatOpenAI

DEFAULT_MODEL = "gpt-4.1-mini"


def get_chat_model(**overrides) -> ChatOpenAI:
    params = {"model": DEFAULT_MODEL, "temperature": 0}
    params.update(overrides)
    return ChatOpenAI(**params)
