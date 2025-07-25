import os
import sys
import re
import json
import requests
import collections
from textwrap import dedent

from typing import List, Literal, Dict, TypedDict, Any

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, create_react_agent
from langchain.chat_models import init_chat_model


class AgentState(MessagesState):
    raw_query: str
    # predict_categorys: List[str]
    # extract_entitys: Dict[str, str]
    final_answer: Dict[str, Any]



search_tool = TavilySearch(
    max_results=5,
    topic="general",
    # country="china"
)
tools = [search_tool]

llm_with_tools = init_chat_model(
    "azure_openai:gpt-4o-mini",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
).bind_tools(tools)


common_llm = init_chat_model(
    "azure_openai:gpt-4o-mini",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)

common_llm = ChatTongyi(
    model="qwen-plus",
    streaming=True,
    temperature=1.0,
    top_p=0.9,
    api_key=os.environ["BAILIAN_API_KEY"]
)


# Define the function that calls the model
def call_model(state: AgentState):
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def respond(state: AgentState):
    # prompt = (
    #     "请对商品属性分析的结果进行JSON结构化输出\n"
    #     "要求结果为一个2层JSON结构：\n"
    #     "第1层的key为属性名称;\n"
    #     "第二层字典的key有2个，一个为`属性值`, 另一个为`改写值`; 第二层字典的value均为列表\n"
    #     "示例: {\"品牌\":{\"属性值\":[\"CHINT/正泰\"],\"改写值\":[\"正泰电器\"]},\"产品名称\":{\"属性值\":[\"电流动作断路器\"],\"改写值\":[]},\"系列\":{\"属性值\":[\"DZ47LE系列\"],\"改写值\":[]},\"额定电压\":{\"属性值\":[\"AC230V\"],\"改写值\":[\"交流230V\"]},\"额定电流\":{\"属性值\":[\"16\"],\"改写值\":[\"16A\",\"16安培\"]},\"极数\":{\"属性值\":[\"2P\"],\"改写值\":[\"双极\"]}}\n"
    #     "输入:\n"
    # )
    prompt = state["messages"][-1].content + "\n请将上述内容整理为JSON格式输出"
    # prompt = prompt + state["messages"][-1].content
    # print(f"respond prompt: \n{prompt}")
    response = common_llm.invoke(
        [HumanMessage(content=prompt)]
    )
    # We return the final answer
    return {"messages": [response]}


# Define the function that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we respond to the user
    if not last_message.tool_calls:
        return "respond"
    # Otherwise if there is, we continue
    else:
        return "continue"


def stream_graph_updates(agent: StateGraph, input_d: dict, config: dict):
    for event in agent.stream(input_d, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            event["messages"][-1].pretty_print()

system_prompt = dedent(
    """你是一名MRO工业品领域的选型专家。
    ** Your objectives **
    core objective: 分析“需求描述”中提及的商品属性信息
    other objectives:
    - 如果属性值缺失单位，尝试进行补充
    - 如果属性还有一些常见说法、同义词，尝试进行补充
    
    ** Guidelines to follow **
    1. 只能找出需求中提及的属性，不要进行推测、猜想！
    2. 可以通过查阅资料来深入理解相关行业、产品和属性。
    3. 可以通过用户提供的参考信息来辅助判断
    """
)

# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("model", call_model)
workflow.add_node("respond", respond)
workflow.add_node("tools", ToolNode(tools))

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("model")

# We now add a conditional edge
workflow.add_conditional_edges(
    "model",
    should_continue,
    {
        "continue": "tools",
        "respond": "respond",
    },
)

workflow.add_edge("tools", "model")
workflow.add_edge("respond", END)
agent = workflow.compile()



raw_query = "CHINT正泰 DZ47LE-32 2P C16"
prompt = f"需求描述: {raw_query}\n"
# related_products = invoke_sku_search(raw_query, 2)
# if related_products:
#     prompt = prompt + "参考信息(一些可能相关的商品示例，不要分析该内容！):\n" + "\n".join([json.dumps(d, ensure_ascii=False) for d in related_products])
# print(prompt)
config = {"configurable": {"thread_id": 1}}
input_d = {
    "messages": [{"role": "user", "content": prompt}]
}
stream_graph_updates(agent, input_d, config)