import os
os.environ["TAVILY_API_KEY"] = "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"

import json
from typing import Annotated

from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage
from langchain_core.messages.ai import AIMessage
from typing_extensions import TypedDict

from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearch(max_results=2)
tools = [tool]

llm = ChatTongyi(
    model='qwen-plus',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
).bind_tools(tools)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:")
            print(type(value["messages"][-1]))
            print(value["messages"][-1])
            print("")
            # print(type(value["messages"][-1].content))
            # print("Assistant:", value["messages"][-1].content)
            # print("Assistant:\n", json.dumps(json.loads(value["messages"][-1].content), ensure_ascii=False))

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break
    stream_graph_updates(user_input)