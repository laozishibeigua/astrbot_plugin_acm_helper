from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import httpx
import time
from bs4 import BeautifulSoup

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    def _build_info_string(self, contests_info, type: str) -> str :
        try:
            final_contest_info = ""

            for contest_info in contests_info:
                final_contest_info += "--------------------\n"
                final_contest_info += contest_info[0] + "\n"
                if isinstance(contest_info[1], str):
                    final_contest_info += "开始时间：" + contest_info[1] + "\n"
                else:
                    final_contest_info += "开始时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(contest_info[1])) + "\n"
                final_contest_info += "持续时间：" + str(contest_info[2] // 3600) + "小时" + (str(contest_info[2] % 3600 // 60) + "分钟" if contest_info[2] % 3600 != 0 else "") + "\n"
        
            return final_contest_info
        
        except Exception as e:

            return "垃圾代码又挂了：" + str(e)

    def _get_cf_contest_info(self):
        cf_contest_request = httpx.get("https://codeforces.com/api/contest.list?gym=false")
        
        if cf_contest_request.status_code != 200:
            return "小北瓜查不到欸，是不是CF又爆炸了？\n"
        
        cf_contest_result  = cf_contest_request.json()

        if cf_contest_result["status"] != "OK":
            return "小北瓜查不到欸，是不是CF又爆炸了？\n"
        
        contests_info = [] # not all string 
        contest_result_recent5 = cf_contest_result["result"][:5][::-1] # get first 5 contest and reverse

        for contest_result in contest_result_recent5:
            if contest_result["phase"] == "FINISHED":
                continue
            contest_info = []
            contest_info.append(contest_result["name"])
            contest_info.append(contest_result["startTimeSeconds"])
            contest_info.append(contest_result["durationSeconds"])
            contests_info.append(contest_info)

        final_cf_contest_info = self._build_info_string(contests_info, "cf") if contests_info else "好像木有比赛唉\n"
        
        return final_cf_contest_info

    def _get_atc_contest_info(self):
        atc_contest_request = httpx.get("https://atcoder.jp/home")

        if atc_contest_request.status_code != 200:
            return "小北瓜查不到欸，是不是atc又爆炸了？\n"
        
        elems = BeautifulSoup(atc_contest_request.text,"html.parser").select("#contest-table-upcoming a")

        contest_set = []
        contests_info = []
        contest_max_limit = 2

        for index, element in enumerate(elems):
            element_text = str(element.getText())
            contest_set.append(element_text)

            if index % 2 == 1:
                element_link = str(element)
                start_index = element_link.find('"') + 1
                end_index = element_link[start_index:].find('"') + start_index
                contest_set.append("https://atcoder.jp" + element_link[start_index : end_index])
                contest_set[0] = contest_set[0][:-contest_max_limit]
                contest_set[0], contest_set[1] = contest_set[1], contest_set[0]
                if "Beginner" in contest_set[0]:
                    contest_set[2] = 6000
                if "Regular" in contest_set[0]:
                    contest_set[2] = 7200

                if "Beginner" in contest_set[0] or "Regular" in contest_set[0]:
                    contests_info.append(contest_set)
                    contest_set = []
        
        final_atc_contest_info = self._build_info_string(contests_info, "atc") if contests_info else "好像木有比赛唉\n"
        
        return final_atc_contest_info
    
    @filter.command("cpcquery")
    async def cpc_query(self, event: AstrMessageEvent):
        """用于给用户推送近期cpc比赛信息"""

        final_message = ""

        try:
            cf_context_info = self._get_cf_contest_info()
            atc_context_info = self._get_atc_contest_info()

            final_message +=  "即将到来的比赛：\n"
            final_message += "CodeForces:\n"
            final_message += cf_context_info
            final_message += "\n"
            final_message += "Atcoder:\n"
            final_message += atc_context_info
            final_message += "\n"
            final_message += "来集训室一起打，依然加练👆"
        
        except Exception as e:
            final_message += "垃圾代码又挂了：" + str(e)

        await event.send(event.plain_result(final_message))
