import os
import requests 
import json

from langchain_core.tools import tool


# 服务地址
host = "https://api.map.baidu.com"

# 接口地址
uri = "/place/v2/search"

# 此处填写你在控制台-应用管理-创建应用后获取的AK
ak = os.environ["BAIDU_MAP_API_KEY"]


# @tool(description="search poi about foods")

def search_meishi():
    params = {
        "query":    "美食",
        "location":    "31.200765,121.316499",
        "radius":    "2000",
        "output":    "json",
        "scope": 2,
        "ak":       ak,
        "page_size": 20,
        "page_num": 0
    }
    response = requests.get(url = host + uri, params = params)
    poi_list = []
    if response:
        res_d = response.json()
        if 'results' in res_d:
            for item in res_d['results']:
                poi_list.append(item['name'])
    if poi_list:
        return json.dumps(poi_list, ensure_ascii=False)
    else:
        return "[]"
    # return response.json() if response else "查询失败"
    # if response:
    #     print(json.dumps(response.json(), ensure_ascii=False))


if __name__ == "__main__":
    print(search_meishi())