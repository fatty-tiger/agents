import os
os.environ["TAVILY_API_KEY"] = "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"

import json
import traceback

from typing import Annotated
from typing_extensions import TypedDict

# from langchain_community.llms.tongyi import Tongyi
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage

class State(TypedDict):
    messages: Annotated[list, add_messages]


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


search_tool = TavilySearch(max_results=2)
tools = [search_tool]
llm = ChatTongyi(
    model='qwen-plus',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
).bind_tools(tools)

# from langchain.chat_models import init_chat_model
# llm = init_chat_model("openai:gpt-4o-mini-2024-07-18")
# llm.bind_tools


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = BasicToolNode(tools=[search_tool])
graph_builder.add_node("tools", tool_node)


# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "END" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            # print("Assistant:", value["messages"][-1].content)
            print("Assistant:", value["messages"][-1])

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        traceback.print_exc()
        # fallback if input() is not available
        # user_input = "What do you know about LangGraph?"
        # print("User: " + user_input)
        # stream_graph_updates(user_input)
        # break