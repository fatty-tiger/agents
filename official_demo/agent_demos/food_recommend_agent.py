import os
# os.environ["OPENAI_API_KEY"] = "****"

from typing import Annotated
from typing import List

from langchain_community.chat_models.tongyi import ChatTongyi
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command, interrupt


memory = MemorySaver()


llm = ChatTongyi(
    # model='qwen-plus',
    model='qwen-turbo',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
)


# class State(TypedDict):
#     messages: Annotated[list, add_messages]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    restaurant_list: List[str]
    exclude_list: List[str]



def recmmend_node(state: State):
    """ 构建提示词进行推荐 """
    return {"messages": [llm.invoke( ["messages"])]}


# @tool
# # Note that because we are generating a ToolMessage for a state update, we
# # generally require the ID of the corresponding tool call. We can use
# # LangChain's InjectedToolCallId to signal that this argument should not
# # be revealed to the model in the tool's schema.
# def human_assistance(
#     name: str, tool_call_id: Annotated[str, InjectedToolCallId]
# ) -> str:
#     """Request assistance from a human."""
#     human_response = interrupt(
#         {
#             "question": "Are you satisfied with the restaurant I recommended?",
#             "restaurant_name": name
#         },
#     )
#     # If the information is correct, update the state as-is.
#     if human_response.get("correct", "").lower().startswith("y"):
#         response = "Yes"
#     # Otherwise, receive information from the human reviewer.
#     else:
#         response = "No"

#     # This time we explicitly update the state with a ToolMessage inside
#     # the tool.
#     state_update = {
#         "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
#     }
#     # We return a Command object in the tool to update our state.
#     return Command(update=state_update)


# @tool
# def human_assistance(query: str) -> str:
#     """Request assistance from a human."""
#     human_response = interrupt({"query": query})
#     return human_response["data"]



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