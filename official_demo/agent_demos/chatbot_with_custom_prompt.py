import os
# os.environ["OPENAI_API_KEY"] = "****"

from typing import Annotated

# from langchain.chat_models import init_chat_model
from langchain_community.chat_models.tongyi import ChatTongyi
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()


llm = ChatTongyi(
    # model='qwen-plus',
    model='qwen-turbo',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": [llm.invoke( ["messages"])]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
# graph = graph_builder.compile()
graph = graph_builder.compile(checkpointer=memory)


def stream_graph_updates(user_input: str, config: dict):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config, stream_mode="values"):
        for message in event["messages"]:
            message.pretty_print()
        # event["messages"][-1].pretty_print()


config = {"configurable": {"thread_id": "1"}}
while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        # snapshot = graph.get_state(config)
        # print(snapshot)
        break
    res = graph.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
    print(res["messages"])
    # stream_graph_updates(user_input, config)