import os
# os.environ["OPENAI_API_KEY"] = "****"

from typing import Annotated

from langchain.chat_models import init_chat_model
from langchain_community.llms import tongyi
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# llm = init_chat_model("openai:gpt-4o-mini-2024-07-18")
# llm = init_chat_model("openai:gpt-3.5-turbo")
llm = tongyi.Tongyi(
    model='qwen-plus',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)



def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()



def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print(type(value))
            print(type(value["messages"]))
            print(value)
            print("Assistant:", value["messages"][-1])
            # print("Assistant:", value["messages"][-1]['content'])


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break