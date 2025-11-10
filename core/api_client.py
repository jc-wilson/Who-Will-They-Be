from core.detection import MatchDetectionHandler
from core.local_api import LockfileHandler
from core.valorant_uuid import UUIDHandler
import requests
import valo_api
import sys
import os
import math
import time
import asyncio
import json
import aiohttp
from dotenv import load_dotenv
from valo_api import set_api_key
from valo_api.endpoints import (get_mmr_details_by_puuid_v2, get_match_history_by_puuid_v3_async,
get_account_details_by_puuid_v2, get_match_history_by_puuid_v3, get_lifetime_matches_by_puuid_v1)
from valo_api.exceptions.rate_limit import rate_limit
from valo_api.exceptions.valo_api_exception import ValoAPIException

class ValoRank:
    def __init__(self):
        self.used_puuids = []
        self.last_match_id = None
        self.frontend_data = {}     # Dictionary of stats for each player
        self.cmp = []   #Current Match PUUIDs
        self.ca = {}  # Current Agent
        self.zero_check = {}    # Total amount of competitive matches a player has that can be loaded
        self.mmr = {}
        self.match_stats = {}
        self.pip = []   # Duplicate of player_info_pre so that it doesn't get lost when you load into a match
        self.handler = None
        self.start = 10
        self.end = 20
        self.gs = []    # Gamemode and Server
        self.gamemode_list = {
            "Swiftplay": "Swiftplay",
            "Deathmatch": "Deathmatch",
            "HURM": "Team Deathmatch",
            "Quickbomb": "Spike Rush",
            "Bomb": "Competitive",
        }

        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        loaded = load_dotenv(dotenv_path)

        if not loaded:
            base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
            dotenv_path = os.path.join(base_path, "core", ".env")
            loaded = load_dotenv(dotenv_path)

        VAL_API_KEY = os.getenv("VAL_API_KEY")
        valo_api.set_api_key(VAL_API_KEY)

    # Refreshes frontend
    async def updater_func(self, on_update):
        if on_update:
            on_update(self.frontend_data)
        await asyncio.sleep(0.05)

    async def lobby_load(self, on_update=None):
        try:
            self.handler.in_match
        except:
            self.frontend_data = {}
            await self.updater_func(on_update)
            if self.handler.party_id.status_code != 500:
                self.handler.party_id = self.handler.party_id.json()
                print(self.handler.party_id["CurrentPartyID"])
                party_info = requests.get(
                    f"https://glz-eu-1.eu.a.pvp.net/parties/v1/parties/{self.handler.party_id["CurrentPartyID"]}",
                    headers=self.handler.match_id_header
                ).json()
                pmi = []    # Party Members Info
                print(party_info)
                for player in party_info["Members"]:
                    pmi.append({
                        "puuid": player.get("Subject"),
                        "rank_up": player.get("CompetitiveTier"),    # Rank unpatched
                        "level": player.get("PlayerIdentity")("AccountLevel"),
                        "name": None,
                        "tag": None
                    })
                puuids = []
                for player in pmi:
                    puuids.append(player.get("puuid"))
                nt = requests.put(
                    "https://pd.eu.a.pvp.net/name-service/v2/players",
                    json=[puuids],
                    headers={**self.handler.match_id_header, "Content-Type": "application/json"}
                ).json()

                for index, player in pmi:
                    self.frontend_data[pmi[index]["puuid"]] = {
                        "name": f"{nt[index]['GameName']}#{nt[index]['TagLine']}",
                        "agent": "N/A",
                        "level": player.get("level"),
                        "matches": "N/A",
                        "wl": "N/A",
                        "acs": "N/A",
                        "kd": "N/A",
                        "hs": "N/A",
                        "rank": player.get("rank_up"),
                        "rr": "N/A",
                        "peak_rank": "N/A",
                        "peak_act": "N/A",
                        "team": "Red"
                    }
                    await self.updater_func(on_update)
            else:
                puuid = self.handler.user_puuid
                nt = requests.put(
                    "https://pd.eu.a.pvp.net/name-service/v2/players",
                    json=[puuid],
                    headers={**self.handler.match_id_header, "Content-Type": "application/json"}
                ).json()

                self.frontend_data[puuid] = {
                    "name": f"{nt[0]['GameName']}#{nt[0]['TagLine']}",
                    "agent": "N/A",
                    "level": "N/A",
                    "matches": "N/A",
                    "wl": "N/A",
                    "acs": "N/A",
                    "kd": "N/A",
                    "hs": "N/A",
                    "rank": "N/A",
                    "rr": "N/A",
                    "peak_rank": "N/A",
                    "peak_act": "N/A",
                    "team": "Red"
                }
                await self.updater_func(on_update)

    # Gamemode and server detection function
    def gs_func(self):
        self.gs = []
        if self.handler.player_info_pre:
            self.gs.append(self.handler.player_info_pre["Mode"])
            self.gs.append(self.handler.player_info_pre["GamePodID"])
        elif self.handler.player_info:
            self.gs.append(self.handler.player_info["ModeID"])
            self.gs.append(self.handler.player_info["GamePodID"])

        if self.gs:
            try:
                word = [word in self.gs[0] for word in self.gamemode_list]
                for i, x in enumerate(word):
                    if x == True:
                        pos = i
                for i, x in enumerate(self.gamemode_list):
                    if i == pos:
                        self.gs[0] = self.gamemode_list[x]
            except:
                self.gs[0] = "Unknown"

            self.gs[1] = self.gs[1][29:-2].capitalize()


    async def valo_stats(self, on_update=None):
        self.handler = MatchDetectionHandler()
        await asyncio.to_thread(self.handler.player_info_retrieval)

        self.uuid_handler = UUIDHandler()
        self.uuid_handler.agent_uuid_function()
        try:
            current_match_id = self.handler.in_match
        except AttributeError:
            await self.lobby_load()
            return

        if self.last_match_id != current_match_id:
            self.used_puuids = []
            self.last_match_id = current_match_id
            self.frontend_data = {}
            self.cmp = []
            self.ca = {}
            self.zero_check = {}
            self.mmr = {}
            self.match_stats = {}
            self.pip = []
            self.start = 10
            self.end = 20
            self.gs = []
            self.gs_func()

        if self.handler.player_info_pre:
            self.pip = self.handler.player_info_pre
        else:
            pass

        if self.handler.player_info:
            if not self.cmp:
                for player in self.handler.player_info["Players"]:
                    self.cmp.append(player.get("Subject"))
            elif len(self.cmp) < 10:
                for player in self.handler.player_info["Players"]:
                    if player["TeamID"] != self.pip["AllyTeam"]["TeamID"]:
                        self.cmp.append(player.get("Subject"))
            else:
                pass
        elif self.pip:
            if not self.cmp:
                for player in self.pip["AllyTeam"]["Players"]:
                    self.cmp.append(player.get("Subject"))
            else:
                pass


        if self.cmp:
            if not self.pip and len(self.ca) != 10:
                self.ca = {}
                for i, player in enumerate(self.handler.player_info["Players"]):
                    self.ca[self.cmp[i]] = player.get("CharacterID")
            elif self.pip and not self.handler.player_info:
                self.ca = {}
                for i, player in enumerate(self.pip["AllyTeam"]["Players"]):
                    self.ca[self.cmp[i]] = player.get("CharacterID")
            elif self.pip and self.handler.player_info and len(self.ca) == 5:
                self.ca = {}
                for i, player in enumerate(self.handler.player_info["Players"]):
                    if player["TeamID"] == self.pip["AllyTeam"]["TeamID"]:
                        self.ca[self.cmp[i]] = player.get("CharacterID")
                for i, player in enumerate(self.handler.player_info["Players"]):
                    if player["TeamID"] != self.pip["AllyTeam"]["TeamID"]:
                        self.ca[self.cmp[i]] = player.get("CharacterID")

        def to_dict(obj):
            if isinstance(obj, list):
                return [to_dict(item) for item in obj]
            if not hasattr(obj, "__dict__"):
                return obj
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = to_dict(value)
            return result

        def get_player_stats(data):
            results = []

            for match in data:
                stats = match.get("stats")

                results.append(stats.get("shots"))

            return results

        for puuid in self.cmp:
            if puuid in self.used_puuids:
                continue
            else:
                self.valorant_mmr = None
                try:
                    self.valorant_mmr = get_mmr_details_by_puuid_v2(region="eu", puuid=f"{puuid}")
                except ValoAPIException as e:
                    if e.status == 429:
                        print("Rate Limit Reached")
                    else:
                        pass


                if self.valorant_mmr:
                    self.mmr[puuid] = to_dict(self.valorant_mmr)
                else:
                    self.mmr[puuid] = {
                        "current_data": {
                            "currenttierpatched": "Unranked",
                            "ranking_in_tier": 0
                        },
                        "highest_rank": {
                            "patched_tier": "Unranked",
                            "peak_act": "N/A",
                            "season": "N/A"
                        }
                    }

                self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e10", "v25")
                self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e11", "v26")

                self.mmr[puuid]["highest_rank"]["patched_tier"] = self.mmr[puuid]["highest_rank"]["patched_tier"].replace("Unset","Unranked")
                self.mmr[puuid]["highest_rank"]["patched_tier"] = self.mmr[puuid]["highest_rank"]["patched_tier"].replace("Unrated", "Unranked")

                self.mmr[puuid]["current_data"]["currenttierpatched"] = self.mmr[puuid]["current_data"]["currenttierpatched"].replace("Unset", "Unranked")
                self.mmr[puuid]["current_data"]["currenttierpatched"] = self.mmr[puuid]["current_data"]["currenttierpatched"].replace("Unrated", "Unranked")

                self.riot_matches = requests.get(
                    f"https://pd.eu.a.pvp.net/match-history/v1/history/{puuid}?startIndex={0}&endIndex={10}&queue=competitive",
                    headers=self.handler.match_id_header
                ).json()

                self.zero_check[puuid] = (self.riot_matches["Total"])

                if self.riot_matches["Total"] == 0:
                    self.riot_name = requests.get(
                        f"https://pd.eu.a.pvp.net/match-history/v1/history/{puuid}?startIndex={0}&endIndex={1}",
                        headers=self.handler.match_id_header
                    ).json()

                    if self.riot_name["Total"] == 0:
                        nt = requests.put(
                            "https://pd.eu.a.pvp.net/name-service/v2/players",
                            json = [puuid],
                            headers={**self.handler.match_id_header, "Content-Type": "application/json"}
                        ).json()

                        print(f"{nt[0]["GameName"]}#{nt[0]["TagLine"]} ({self.uuid_handler.agent_converter(self.ca[puuid])}) has not played a game in the last 30 days")

                        if self.handler.player_info:
                            for player in self.handler.player_info["Players"]:
                                if player["Subject"] == puuid:
                                    bor = player["TeamID"]
                        elif self.handler.player_info_pre:
                            bor = self.handler.player_info_pre["AllyTeam"]["TeamID"]

                        self.frontend_data[puuid] = {
                            "name": f"{nt[0]['GameName']}#{nt[0]['TagLine']}",
                            "agent": self.uuid_handler.agent_converter(self.ca[puuid]),
                            "level": "N/A",
                            "matches": 0,
                            "wl": "N/A",
                            "acs": "N/A",
                            "kd": "N/A",
                            "hs": "N/A",
                            "rank": self.mmr[puuid]["current_data"]["currenttierpatched"],
                            "rr": self.mmr[puuid]["current_data"]["ranking_in_tier"],
                            "peak_rank": self.mmr[puuid]["highest_rank"]["patched_tier"],
                            "peak_act": self.mmr[puuid]["highest_rank"]["season"].upper(),
                            "team": bor
                        }
                        await self.updater_func(on_update)
                        self.used_puuids.append(puuid)
                        continue

                    match_id_name = self.riot_name["History"][0]["MatchID"]
                    match_stats_name = requests.get(
                        f"https://pd.eu.a.pvp.net/match-details/v1/matches/{match_id_name}",
                        headers=self.handler.match_id_header
                    ).json()
                    ntl = []    # Name Tag Level
                    for player in match_stats_name["players"]:
                        if player["subject"] == puuid:
                            ntl.append({
                                "name": player.get("gameName"),
                                "tag": player.get("tagLine"),
                                "level": player.get("accountLevel"),
                            })

                    print(f"{ntl[0]["name"]}#{ntl[0]["tag"]} ({self.uuid_handler.agent_converter(self.ca[puuid])}) has not played competitive in the last 30 days/100 matches")

                    if self.handler.player_info:
                        for player in self.handler.player_info["Players"]:
                            if player["Subject"] == puuid:
                                bor = player["TeamID"]
                    elif self.handler.player_info_pre:
                        bor = self.handler.player_info_pre["AllyTeam"]["TeamID"]

                    self.frontend_data[puuid] = {
                        "name": f"{ntl[0]['name']}#{ntl[0]['tag']}",
                        "agent": self.uuid_handler.agent_converter(self.ca[puuid]),
                        "level": ntl[0]["level"],
                        "matches": 0,
                        "wl": "N/A",
                        "acs": "N/A",
                        "kd": "N/A",
                        "hs": "N/A",
                        "rank": self.mmr[puuid]["current_data"]["currenttierpatched"],
                        "rr": self.mmr[puuid]["current_data"]["ranking_in_tier"],
                        "peak_rank": self.mmr[puuid]["highest_rank"]["patched_tier"],
                        "peak_act": self.mmr[puuid]["highest_rank"]["season"].upper(),
                        "team": bor
                    }
                    await self.updater_func(on_update)
                    self.used_puuids.append(puuid)
                    continue

                #if self.valorant_mmr:
                    #converted = to_dict(self.valorant_mmr)
                    #with open(f"account_mmr.json", "w", encoding="utf-8") as f:
                        #json.dump(converted, f, default=lambda o: o.__dict__, indent=2)
                    #with open(f"account_mmr.json") as a:
                        #mmr = json.load(a)  # Account MMR Details

                riot_match_ids = []
                for match in self.riot_matches["History"]:
                    riot_match_ids.append(match["MatchID"])


                match_urls = []
                for matchID in riot_match_ids:
                    match_urls.append(f"https://pd.eu.a.pvp.net/match-details/v1/matches/{matchID}")


                async def gather_matches():
                    async with aiohttp.ClientSession(headers=self.handler.match_id_header) as session:
                        tasks = [self.fetch(session, match_url) for match_url in match_urls]
                        self.match_stats[puuid] = await asyncio.gather(*tasks)

                await gather_matches()

                await self.calc_stats(puuid)

                await self.updater_func(on_update)

                self.used_puuids.append(puuid)

        for index, puuid in enumerate(self.cmp):
            self.frontend_data[puuid]["agent"] = self.uuid_handler.agent_converter(self.ca[puuid])
            await self.updater_func(on_update)


    async def calc_stats(self, puuid, on_update=None):
        stats_list = []
        wl_list = []  # tracks wins and losses
        hs_list = []
        for match in self.match_stats[puuid]:
            for player in match["players"]:
                if player["subject"] == puuid:
                    stats_list.append({
                        "name": player.get("gameName"),
                        "tag": player.get("tagLine"),
                        "stats": player.get("stats"),
                        "level": player.get("accountLevel"),
                        "team": player.get("teamId")
                    })

        for i, match in enumerate(self.match_stats[puuid]):
            for team in match["teams"]:
                if team["teamId"] == stats_list[i]["team"]:
                    wl_list.append(team.get("won"))


        for match in self.match_stats[puuid]:
            for round in match["roundResults"]:
                for player in round["playerStats"]:
                    if player["subject"] == puuid:
                        for round2 in player["damage"]:
                            hs_list.append({
                                "legshots": round2.get("legshots"),
                                "bodyshots": round2.get("bodyshots"),
                                "headshots": round2.get("headshots")
                            })

        team = []
        wins = []
        match_count_wl = 0
        for match in wl_list:
            match_count_wl += 1
        wl = f"{math.floor(sum(wl_list) / len(wl_list) * 100)}%"

        score = 0
        rounds_played = 0
        for match in stats_list:
            score += match["stats"]["score"]
            rounds_played += match["stats"]["roundsPlayed"]
        acs = score / rounds_played

        kills = 0
        deaths = 0
        match_count_kd = 0
        for match in stats_list:
            match_count_kd += 1
            kills += match["stats"]["kills"]
            deaths += match["stats"]["deaths"]
            if deaths == 0:
                deaths += 1
        kd = kills / deaths

        legshots = 0
        bodyshots = 0
        headshots = 0
        for round in hs_list:
            legshots += round["legshots"]
            bodyshots += round["bodyshots"]
            headshots += round["headshots"]
        hs = (headshots / (legshots + bodyshots + headshots)) * 100

        if self.handler.player_info:
            for player in self.handler.player_info["Players"]:
                if player["Subject"] == puuid:
                    bor = player["TeamID"]
        elif self.handler.player_info_pre:
            bor = self.handler.player_info_pre["Teams"][0]["TeamID"]

        if self.mmr[puuid]["current_data"]["currenttierpatched"] == "Unrated":
            self.mmr[puuid]["current_data"]["currenttierpatched"] = "Unranked"
        self.frontend_data[puuid] = {
            "name": f"{stats_list[0]['name']}#{stats_list[0]['tag']}",
            "agent": self.uuid_handler.agent_converter(self.ca[puuid]),
            "level": stats_list[0]['level'],
            "matches": match_count_kd,
            "wl": str(wl),
            "acs": str(acs)[:5],
            "kd": str(kd)[:4],
            "hs": str(hs)[:4],
            "rank": self.mmr[puuid]["current_data"]["currenttierpatched"],
            "rr": self.mmr[puuid]["current_data"]["ranking_in_tier"],
            "peak_rank": self.mmr[puuid]["highest_rank"]["patched_tier"],
            "peak_act": self.mmr[puuid]["highest_rank"]["season"].upper(),
            "team": bor
        }
        await self.updater_func(on_update)

        print(
            f"{stats_list[0]['name']}#{stats_list[0]['tag']}'s ({self.uuid_handler.agent_converter(self.ca[puuid])}) level is {stats_list[0]['level']} | W/L % in last {match_count_kd} matches: {wl} | ACS in the last {match_count_kd} matches: {str(acs)[:5]} | KD in last {match_count_kd} matches: {str(kd)[0:4]} | HS in last {match_count_kd} matches: hs is: {str(hs)[:4]}% | current rank is: {self.mmr[puuid]['current_data']['currenttierpatched']} | current rr is: {self.mmr[puuid]['current_data']['ranking_in_tier']} | highest rank was: {self.mmr[puuid]['highest_rank']['patched_tier']} | peak act was: {self.mmr[puuid]['highest_rank']['season']}")

    async def load_more_matches(self, on_update=None):
        for puuid in self.cmp:
            if self.zero_check[puuid] <= self.start:
                continue
            else:
                self.riot_matches_new = requests.get(
                    f"https://pd.eu.a.pvp.net/match-history/v1/history/{puuid}?startIndex={self.start}&endIndex={self.end}&queue=competitive",
                    headers=self.handler.match_id_header
                ).json()

                if self.riot_matches_new["Total"] == 0:
                    continue

                riot_match_ids_new = []
                for match in self.riot_matches_new["History"]:
                    riot_match_ids_new.append(match["MatchID"])

                match_urls_new = []
                for matchID in riot_match_ids_new:
                    match_urls_new.append(f"https://pd.eu.a.pvp.net/match-details/v1/matches/{matchID}")

                async def gather_matches():
                    async with aiohttp.ClientSession(headers=self.handler.match_id_header) as session:
                        tasks = [self.fetch(session, match_url) for match_url in match_urls_new]
                        self.match_stats[puuid].extend(await asyncio.gather(*tasks))

                await gather_matches()

                await self.calc_stats(puuid)

                await self.updater_func(on_update)

                print("load more matches finished")

        self.start += 10
        self.end += 10

    async def fetch(self, session, url, retries=3):
        for attempt in range(retries):
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        print(f"⚠️ Unexpected response type at {url}:\n{text[:200]}...")
                        return None
                elif response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", "2"))
                    print(f"🚫 Rate limited (429). Retrying in {retry_after}s... ({attempt + 1}/{retries})")
                    await asyncio.sleep(retry_after)
                else:
                    print(f"❌ Error {response.status} fetching {url}")
                    return None

        print(f"❌ Failed to fetch {url} after {retries} retries.")
        return None














        
        







