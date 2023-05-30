"""Test Vertex AI API wrapper.
In order to run this test, you need to install VertexAI SDK (that is is the private
preview)  and be whitelisted to list the models themselves:
In order to run this test, you need to install VertexAI SDK 
pip install google-cloud-aiplatform>=1.25.0

Your end-user credentials would be used to make the calls (make sure you've run 
`gcloud auth login` first).
"""
import pytest

from langchain.chat_models import ChatVertexAI
from langchain.chat_models.vertexai import _MessagePair, _parse_chat_history
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)


def test_vertexai_single_call() -> None:
    model = ChatVertexAI()
    message = HumanMessage(content="Hello")
    response = model([message])
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, str)
    assert model._llm_type == "vertexai"
    assert model.model_name == model.client._model_id


def test_vertexai_single_call_with_context() -> None:
    model = ChatVertexAI()
    raw_context = (
        "My name is Ned. You are my personal assistant. My favorite movies "
        "are Lord of the Rings and Hobbit."
    )
    question = (
        "Hello, could you recommend a good movie for me to watch this evening, please?"
    )
    context = SystemMessage(content=raw_context)
    message = HumanMessage(content=question)
    response = model([context, message])
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, str)


def test_parse_chat_history_correct() -> None:
    text_context = (
        "My name is Ned. You are my personal assistant. My "
        "favorite movies are Lord of the Rings and Hobbit."
    )
    context = SystemMessage(content=text_context)
    text_question = (
        "Hello, could you recommend a good movie for me to watch this evening, please?"
    )
    question = HumanMessage(content=text_question)
    text_answer = (
        "Sure, You might enjoy The Lord of the Rings: The Fellowship of the Ring "
        "(2001): This is the first movie in the Lord of the Rings trilogy."
    )
    answer = AIMessage(content=text_answer)
    history = _parse_chat_history([context, question, answer, question, answer])
    assert history.system_message == context
    assert len(history.history) == 2
    assert history.history[0] == _MessagePair(question=question, answer=answer)


def test_parse_chat_history_wrong_sequence() -> None:
    text_question = (
        "Hello, could you recommend a good movie for me to watch this evening, please?"
    )
    question = HumanMessage(content=text_question)
    with pytest.raises(ValueError) as exc_info:
        _ = _parse_chat_history([question, question])
    assert (
        str(exc_info.value)
        == "A human message should follow a bot one, got human, human."
    )


def test_vertexai_single_call_failes_no_message() -> None:
    chat = ChatVertexAI()
    with pytest.raises(ValueError) as exc_info:
        _ = chat([])
    assert (
        str(exc_info.value)
        == "You should provide at least one message to start the chat!"
    )


def test_vertexai_parameter_integrity() -> None:
    """Vertex AI sdk does not maintain hyper-parameters for chat sessions when calling
    model.send_message method. It is necessary to pass the parameters set in Chat object
    inside the call to send_message. This is really an error in vertexai sdk but a quick fix here
    can be added without much risk of forward incompatibilities.
    """
    model = ChatVertexAI(max_output_tokens=1024, temperature=0.1)
    raw_context = (
        "My name is Ned. You are my personal assistant. My favorite movies "
        "are Lord of the Rings and Hobbit."
    )
    question = (
        "Hello, could you recommend a good movie for me to watch this evening, please?"
    )
    context = SystemMessage(content=raw_context)
    message = HumanMessage(content=question)
    response = model([context, message])
    # this tests that the larger max_output_tokens value is being passed. the default of 128 will
    # will cause this to fail. sorry I couldn't think of a better way to do it in short order.
    assert len(response.content.split(' ')) * 3/4 > 128
