from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import httpx

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    def get_gametime(self, data):
        if "gametime" not in data:
            return "没有游戏时间数据捏..."
        
        gametime_seconds = data["gametime"]
        if gametime_seconds == -1:
            return "人家不想告诉你啦！"
        
        hours = gametime_seconds // 3600
        return f"{hours} 小时"


    def get_gamesplayed(self, data):
        if "gamesplayed" not in data:
            return "没有游戏局数数据捏..."
        
        gamesplayed = data["gamesplayed"]
        
        return str(gamesplayed)


    def get_gameswon(self, data):
        if "gameswon" not in data:
            return "没有游戏胜利数据捏..."
        
        gameswon = data["gameswon"]
        
        return str(gameswon)
    
    def get_league_rating(self, user_name, headers):
        lg_r = httpx.get(f"https://ch.tetr.io/api/users/{user_name}/summaries/league", headers = headers)
        if lg_r.status_code != 200:
            return "获取rating失败了捏..."
        
        lg_result_data = lg_r.json()

        if lg_result_data["success"] == False:
            return "获取rating失败了捏..."

        if "data" not in lg_result_data:
            return "获取rating失败了捏..."
        
        lg_data = lg_result_data["data"]
        if "glicko" not in lg_data:
            return "获取rating失败了捏..."

        league_rating = lg_data["tr"]
        if league_rating == -1:
            return "打的太少，木有rating捏！"
        return str(league_rating)

    @filter.command("tetr")
    async def get_tetrio_user_info(self, event: AstrMessageEvent, user_name:str):
        """获取 TETR.IO 用户信息"""

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        r = httpx.get(f"https://ch.tetr.io/api/users/{user_name}", headers = headers)
        
        if r.status_code != 200:
            await event.send(event.plain_result(f"获取用户信息失败，状态码: {r.status_code}"))
            return
        
        result_data = r.json()

        if result_data["success"] == False:
            await event.send(event.plain_result(f"获取用户信息失败，错误信息: {result_data['error']}"))
            return
        if "data" not in result_data:
            await event.send(event.plain_result("获取用户信息失败，不知道为啥木有数据捏"))
            return
        
        data = result_data["data"] 

        gametime_info = self.get_gametime(data)
        gamesplayed_info = self.get_gamesplayed(data)
        gameswon_info = self.get_gameswon(data)
        league_rating_info = self.get_league_rating(user_name,headers)
        
        final_message = f"{user_name} 的 tetr.io 信息："
        final_message += f"\n游戏时间: {gametime_info}"
        final_message += f"\n游戏局数: {gamesplayed_info}"
        final_message += f"\n胜利局数: {gameswon_info}"
        final_message += f"\n联赛rating: {league_rating_info}"

        await event.send(event.plain_result(final_message))
