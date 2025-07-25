import os
import json
import requests

from typing import Annotated
from typing import List, Dict
from typing_extensions import TypedDict

from langchain_core.tools import tool
from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langgraph.prebuilt import ToolNode, tools_condition
# from langchain_core.messages import ToolMessage
# from langchain_core.tools import InjectedToolCallId, tool
# from langgraph.types import Command, interrupt

@tool
def search_meishi(
        latitude: Annotated[float, "user location latitude"],
        longitude: Annotated[float, "user location longitude"],
        radius: Annotated[int, "radius(metres) of search"],
    ):
    """ search pois of restaurants near user location """
    url = "https://api.map.baidu.com/place/v2/search"
    ak = os.environ["BAIDU_MAP_API_KEY"]
    params = {
        "query": "美食",
        "location": f"{latitude},{longitude}",
        "radius": f"{radius}",
        "output": "json",
        "scope": 2,
        "ak": ak,
        "page_size": 20,
        "page_num": 0
    }
    response = requests.get(url=url, params=params)
    poi_list = []
    if response:
        res_d = response.json()
        for item in res_d['results']:
            new_item = {}
            for k in ["name", "location", "telephone"]:
                if k in item and item[k]:
                    new_item[k] = item[k]
            new_item["address"] = " ".join([item["province"], item["city"], item["area"], item["address"]])
            for k in [ "shop_hours", "distance", "price", "overall_rating"]:
                if "detail_info" in item and k in item["detail_info"] and item["detail_info"][k]:
                    new_item[k] = item["detail_info"][k]
            tags = set()
            for k in ["classified_poi_tag", "tag", "label"]:
                if "detail_info" in item and "classified_poi_tag" in item["detail_info"]:
                    tags.update(item["detail_info"]["classified_poi_tag"].split(";"))
            new_item["tags"] = list(tags)
            poi_list.append(new_item)
    return poi_list


# class State(TypedDict):
#     messages: Annotated[list, add_messages]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    datetime: str
    weekday: str
    latitude: float
    longitude: float
    # restaurant_list: List[str]
    # exclude_list: List[str]
    # preference: Dict[str, str]


def recommend_bot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}



def stream_graph_updates(input_d: dict, config: dict):
    for event in graph.stream(input_d, config, stream_mode="values"):
        # for message in event["messages"]:
        #     message.pretty_print()
        event["messages"][-1].pretty_print()


tools = [search_meishi]
llm = ChatTongyi(
    # model='qwen-plus',
    model='qwen-turbo',
    streaming=True,
    api_key=os.environ["BAILIAN_API_KEY"]
)
llm = llm.bind_tools(tools)

tool_node = ToolNode(tools=[search_meishi])


graph_builder = StateGraph(State)
graph_builder.add_node("recommend_bot", recommend_bot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "recommend_bot")
graph_builder.add_conditional_edges(
    "recommend_bot",
    tools_condition,
)
graph_builder.add_edge("recommend_bot", END)
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)



from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass


# config = {"configurable": {"thread_id": "1"}}
# input_d = {
#     "datetime": "2025-07-21 10:30:00",
#     "weekday": "星期一",
#     "latitude": 31.200765,
#     "longitude": 121.316499
# }
# prompt = """你是一名美食专家, 请结合用户当前的基本信息，推荐一个餐厅用餐。
# 基本信息: %s
# """ % json.dumps(input_d, ensure_ascii=False)
# print(prompt)
# input_d["messages"] = [{"role": "user", "content": prompt}]

# stream_graph_updates(input_d, config)

# while True:
#     user_input = input("User: ")
#     if user_input.lower() in ["quit", "exit", "q"]:
#         print("Goodbye!")
#         snapshot = graph.get_state(config)
#         print(snapshot)
#         break
#     input_d["messages"] = [{"role": "user", "content": user_input}]
#     stream_graph_updates(input_d, config)
