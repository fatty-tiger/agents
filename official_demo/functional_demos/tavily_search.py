import json
from langchain_tavily import TavilySearch

tool = TavilySearch(max_results=2)
tools = [tool]
#result = tool.invoke("What's a 'node' in LangGraph?")
result = tool.invoke("What is the weather in shanghai today?")

print(json.dumps(result, ensure_ascii=False))