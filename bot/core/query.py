import asyncio
import base64
import hashlib
import hmac
import json
import random
import sys
import traceback
from time import time
from urllib.parse import unquote

import aiohttp
import cloudscraper
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from bot.core.agents import fetch_version
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from random import randint

from datetime import datetime, timezone
import urllib3
from bot.utils import launcher as lc


def convert_to_unix(time_stamp):
    dt_obj = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    return dt_obj.timestamp()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def convert_to_hmac(t=None, e=""):
    if t is None:
        t = {}
    sorted_items = sorted(t.items())
    query_string = "&".join(f"{key}={value}" for key, value in sorted_items)
    return hmac.new(e.encode(), query_string.encode(), hashlib.sha256).hexdigest()

end_point = "https://api2.bybit.com/web3/api/web3game/tg"
login_api = f"{end_point}/registerOrLogin"
join_api = f"{end_point}/game/treasureChest/join"
game_status = f"{end_point}/user/game/status"
api_start_farm = f"{end_point}/user/farm/start"
api_status_farm = f"{end_point}/user/farm/status"
api_tasks_list = f"{end_point}/task/list"
api_complete_task = f"{end_point}/task/complete"
api_claim_farm = f"{end_point}/user/farm/claim"
api_start_game = f"{end_point}/user/game/start"
api_postScore = f"{end_point}/user/game/postScore"

class Tapper:
    def __init__(self, query: str, multi_thread):
        self.query = query
        self.multi_thread = multi_thread
        try:
            fetch_data = unquote(query).split("user=")[1].split("&chat_instance=")[0]
            json_data = json.loads(fetch_data)
        except:
            try:
                fetch_data = unquote(query).split("user=")[1].split("&auth_date=")[0]
                json_data = json.loads(fetch_data)
            except:
                try:
                    fetch_data = unquote(unquote(query)).split("user=")[1].split("&auth_date=")[0]
                    json_data = json.loads(fetch_data)
                except:
                    logger.warning(f"Invaild query: {query}")
                    return
        self.session_name = json_data['username']
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.access_token = ""
        self.logged = False
        self.refresh_token_ = ""
        self.user_data = None
        self.auth_token = None
        self.my_ref = get_()
        self.game_key = None
        self.speed = 0
        self.time = 180
        self.ignore_tasks = ["1", "4"]
        self.invite_code = self.my_ref.split("invite_")[1].split("_")[0]

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/json', timeout=aiohttp.ClientTimeout(20))
            response.raise_for_status()

            response_json = await response.json()
            ip = response_json.get('ip', 'NO')
            country = response_json.get('country', 'NO')

            logger.info(f"{self.session_name} |🟩 Logging in with proxy IP {ip} and country {country}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def login(self, session: cloudscraper.CloudScraper):
        payload = {
            "inviterCode": self.invite_code
        }
        try:
            res = session.post(login_api, json=payload)
            res.raise_for_status()
            data = res.json()
            if data['retCode'] == 0:
                logger.success(f"{self.session_name} | <green>Successfully logged in!</green>")
                return data
            else:
                logger.warning(f"{self.session_name} | <yellow>Failed to login!</yellow>")
                return None
        except Exception as e:
            print(res.text)
            logger.warning(f"{self.session_name} | Unknown error while trying to login: {e}")

    async def join_(self, session: cloudscraper.CloudScraper):
        payload = {
            'inviterCode': self.invite_code
        }

        try:
            res = session.post(join_api, json=payload)
            res.raise_for_status()
            if res.json()['retCode'] == 0:
                logger.success(f"{self.session_name} | <green>Joined box successfully!</green>")
                return True
            else:
                return False
        except:
            return False

    async def get_game_status(self, session: cloudscraper.CloudScraper):
        try:
            res = session.post(game_status, json={})
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                return res.json()['result']
            else:
                logger.warning(f"{self.session_name} | Failed to get game info: {res.status_code}")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to get game info: {e}")
            return None

    async def start_farm(self, session: cloudscraper.CloudScraper):
        try:
            res = session.post(api_start_farm, json={})
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                logger.success(f"{self.session_name} | <green>Successfully started farm!</green>")
            else:
                logger.warning(f"{self.session_name} | Failed to start farm: {res.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to start farm: {e}")
            return False

    async def get_farm_status(self, session: cloudscraper.CloudScraper):
        try:
            res = session.post(api_status_farm, json={})
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                return res.json()['result']
            else:
                logger.warning(f"{self.session_name} | Failed to get farm info: {res.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to get farm info: {e}")
            return False

    async def complete_task(self, task, session: cloudscraper.CloudScraper):
        payload = {
            "taskId": str(task['taskId']),
            "tgVoucher": "todamoon"
        }
        try:
            res = session.post(api_complete_task, json=payload)
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                logger.success(
                    f"{self.session_name} | <green>Successfully completed task: <cyan>{task['taskName']}</cyan> - Earned: <cyan>{task['point']}</cyan></green>")
            else:
                logger.warning(f"{self.session_name} | Failed to complete task {task['taskName']}: {res.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to complete task {task['taskName']}: {e}")
            return False

    async def do_tasks(self, session: cloudscraper.CloudScraper):
        try:
            res = session.get(api_tasks_list)
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                for task in res.json()['result']['tasks']:
                    if task['status'] == 2:
                        continue
                    if task['taskId'] in self.ignore_tasks:
                        continue
                    else:
                        await self.complete_task(task, session)
                        await asyncio.sleep(randint(3, 6))
            else:
                logger.warning(f"{self.session_name} | Failed to get task list: {res.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to get task list: {e}")
            return False

    async def claim_farm(self, session: cloudscraper.CloudScraper):
        try:
            res = session.post(api_claim_farm, json={})
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                logger.success(
                    f"{self.session_name} | <green>Successfully claimed <cyan>{round(self.speed * self.time, 1)}</cyan> points from farm</green>")
            else:
                logger.warning(f"{self.session_name} | Failed to claim farm info: {res.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to claim farm info: {e}")
            return False

    async def start_game(self, session: cloudscraper.CloudScraper):
        try:
            res = session.post(api_start_game, json={})
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                logger.success(f"{self.session_name} | <green>Successfully started game!</green>")
                return res.json()['result']
            else:
                logger.warning(f"{self.session_name} | Failed to start game: {res.json()}")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to claim farm info: {e}")
            return None

    async def post_score(self, start_time, sign, points, end_time, session: cloudscraper.CloudScraper):
        payload = {
            "start_time": start_time,
            "sign": sign,
            "point": points,
            "end_time": end_time
        }
        try:
            res = session.post(api_postScore, json=payload)
            res.raise_for_status()
            if res.json()["retCode"] == 0:
                logger.success(
                    f"{self.session_name} | <green>Successfully earned <cyan>{points}</cyan> points from game!</green>")
                return True
            else:
                logger.warning(f"{self.session_name} | Failed to complete game: {res.json()}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to complete game: {e}")
            return False

    def generate_payload(self, start_time):
        time_ = randint(40, 60)
        gift = randint(0, 3) * 50
        points = time_ * 2 + gift
        end_time = int(int(start_time) + time_ * 1000)
        payload = convert_to_hmac({"start_time": start_time, "end_time": end_time, "point": points}, self.game_key)
        return [payload, start_time, end_time, points]

    async def run(self, proxy: str | None, ua: str) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        session = cloudscraper.create_scraper()
        session.headers.update(headers)

        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                proxy_type = proxy.split(':')[0]
                proxies = {
                    proxy_type: proxy
                }
                session.proxies.update(proxies)
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")

        token_live_time = randint(3400, 3600)
        while True:
            can_run = True
            try:
                # if check_base_url() is False:
                #     can_run = False
                #     if settings.ADVANCED_ANTI_DETECTION:
                #         logger.warning(
                #             "<yellow>Detected index js file change. Contact me to check if it's safe to continue: https://t.me/vanhbakaaa</yellow>")
                #     else:
                #         logger.warning(
                #             "<yellow>Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/vanhbakaaa</yellow>")

                if can_run:

                    if time() - access_token_created_time >= token_live_time:
                        tg_web_data = self.query
                        self.auth_token = tg_web_data
                        access_token_created_time = time()
                        token_live_time = randint(3400, 3600)

                    session.headers['Authorization'] = self.auth_token
                    login_data = await self.login(session)
                    if login_data:
                        user = login_data['result']
                        self.game_key = user['signKey']
                        logger.info(f"{self.session_name} | Points balance: <cyan>{user['point']}</cyan>")
                        await asyncio.sleep(3)
                        farm_status = await self.get_farm_status(session)
                        await asyncio.sleep(3)
                        self.speed = float(farm_status['pointPerMinute'])
                        self.time = farm_status['resetMinutes']
                        if farm_status['status'] == "FarmStatus_Running":
                            logger.info(f"{self.session_name} | Farm is currently running!")
                        elif farm_status['status'] == "FarmStatus_Wait_Claim":
                            await self.claim_farm(session)
                            await asyncio.sleep(randint(5, 10))
                            await self.start_farm(session)
                        else:
                            await self.start_farm(session)
                            await asyncio.sleep(5)

                        if settings.AUTO_TASK is True:
                            await self.do_tasks(session)
                            await asyncio.sleep(5)

                        if settings.AUTO_GAME is True:
                            game_stats = await self.get_game_status(session)
                            logger.info(
                                f"{self.session_name} | Ticket left: {game_stats['totalCount'] - game_stats['usedCount']}/{game_stats['totalCount']}")
                            if game_stats['usedCount'] == game_stats['totalCount']:
                                logger.info(f"{self.session_name} | No ticket left to play!")
                            else:
                                totalTickets = game_stats['totalCount'] - game_stats['usedCount']
                                while totalTickets > 0:
                                    start_t = await self.start_game(session)
                                    payload = self.generate_payload(start_t['time'])
                                    sleep_ = (payload[2] - int(payload[1])) / 1000
                                    logger.info(
                                        f"{self.session_name} | Wait {round(sleep_, 2)} seconds to complete game...")
                                    await asyncio.sleep(sleep_)
                                    await self.post_score(payload[1], payload[0], payload[3], payload[2], session)
                                    totalTickets -= 1

                logger.info(f"==<cyan>Completed {self.session_name}</cyan>==")

                if self.multi_thread:
                    sleep_ = round(random.uniform(settings.SLEEP_TIME_EACH_ROUND[0], settings.SLEEP_TIME_EACH_ROUND[1]), 1)

                    logger.info(f"{self.session_name} | Sleep <red>{sleep_}</red> hours")
                    await asyncio.sleep(sleep_ * 3600)
                else:
                    await http_client.close()
                    session.close()
                    break
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))

def get_():
    actual = random.choices(["aW52aXRlXzhBSzhKSTQyX2J1aWloMA==", "aW52aXRlXzhHQlIwRVdHX1ZhbmhkYXkx"], weights=[30, 70], k=1)
    abasdowiad = base64.b64decode(actual[0])
    waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext = abasdowiad.decode("utf-8")

    return waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext


async def run_query_tapper(query: str, proxy: str | None, ua: str):
    try:
        sleep_ = randint(1, 15)
        logger.info(f" start after {sleep_}s")
        # await asyncio.sleep(sleep_)
        await Tapper(query=query, multi_thread=True).run(proxy=proxy, ua=ua)
    except InvalidSession:
        logger.error(f"Invalid Query: {query}")
async def run_query_tapper1(querys: list[str]):

    while True:
        for query in querys:
            try:
                await Tapper(query=query, multi_thread=False).run(
                    proxy=await lc.get_proxy(lc.fetch_username(query)),
                    ua=await lc.get_user_agent(lc.fetch_username(query)))
            except InvalidSession:
                logger.error(f"Invalid Query: {query}")

            sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
            logger.info(f"Sleep {sleep_}s...")
            await asyncio.sleep(sleep_)

        sleep_ = round(random.uniform(settings.SLEEP_TIME_EACH_ROUND[0], settings.SLEEP_TIME_EACH_ROUND[1]), 1)

        logger.info(f"Sleep <red>{sleep_}</red> hours")
        await asyncio.sleep(sleep_ * 3600)
