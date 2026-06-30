from core.detection import MatchDetectionHandler
from core.local_api import LockfileHandler
from core.valorant_uuid import UUIDHandler
from core.skins import SkinHandler
from concurrent.futures import ThreadPoolExecutor
from core.http_session import SharedSession
from core.party_tracker import PartyTracker
from core.map_instalock_agent import map_instalock_agent
import requests
import sys
import os
import re
import math
import time
import asyncio
import json


class ValoRank:
    def __init__(self):
        self.used_puuids = []
        self.last_match_id = None
        self.frontend_data = {}  # Dictionary of stats for each player
        self.cmp = []  # Current Match PUUIDs
        self.ca = {}  # Current Agent
        self.zero_check = {}  # Total amount of competitive matches a player has that can be loaded
        self.mmr = {}
        self.rating_changes = {}
        self.match_stats = {}
        self.pip = {}  # Duplicate of player_info_pre so that it doesn't get lost when you load into a match
        self.handler = MatchDetectionHandler()
        self.start = 5
        self.end = 10
        self.gs = []  # Gamemode and Server
        self.skins = {}
        self.done = 0
        self.uuid_handler = UUIDHandler()
        self.uuid_handler.agent_uuid_function()
        self.uuid_handler.season_uuid_function()
        self.skin_handler = SkinHandler()
        self.party_tracker = PartyTracker.get()
        self.party_detection_enabled = True
        self.version_data = self.get_version_from_log()
        self.current_act = self.uuid_handler.current_season()
        self.e1_to_e4 = [
            "3f61c772-4560-cd3f-5d3f-a7ab5abda6b3",
            "0530b9c4-4980-f2ee-df5d-09864cd00542",
            "46ea6166-4573-1128-9cea-60a15640059b",
            "97b6e739-44cc-ffa7-49ad-398ba502ceb0",
            "ab57ef51-4e59-da91-cc8d-51a5a2b9b8ff",
            "52e9749a-429b-7060-99fe-4595426a0cf7",
            "2a27e5d2-4d30-c9e2-b15a-93b8909a442c",
            "4cb622e1-4244-6da3-7276-8daaf1c01be2",
            "a16955a5-4ad0-f761-5e9e-389df1c892fb",
            "573f53ac-41a5-3a7d-d9ce-d6a6298e5704",
            "d929bc38-4ab6-7da4-94f0-ee84f8ac141e",
            "3e47230a-463c-a301-eb7d-67bb60357d4f"
        ]
        self.gamemode_list = {
            "Swiftplay": "Swiftplay",
            "Deathmatch": "Deathmatch",
            "HURM": "Team Deathmatch",
            "Quickbomb": "Spike Rush",
            "Bomb": "Competitive",
        }
        self.ttr = {
            0: "Unranked",
            3: "Iron 1",
            4: "Iron 2",
            5: "Iron 3",
            6: "Bronze 1",
            7: "Bronze 2",
            8: "Bronze 3",
            9: "Silver 1",
            10: "Silver 2",
            11: "Silver 3",
            12: "Gold 1",
            13: "Gold 2",
            14: "Gold 3",
            15: "Platinum 1",
            16: "Platinum 2",
            17: "Platinum 3",
            18: "Diamond 1",
            19: "Diamond 2",
            20: "Diamond 3",
            21: "Ascendant 1",
            22: "Ascendant 2",
            23: "Ascendant 3",
            24: "Immortal 1",
            25: "Immortal 2",
            26: "Immortal 3",
            27: "Radiant"
        }

    # Refreshes frontend
    async def updater_func(self, on_update):
        if on_update:
            on_update(self.frontend_data)
        await asyncio.sleep(0.05)

    def _format_response_preview(self, body, limit=180):
        preview = " ".join(str(body or "").split())
        if len(preview) > limit:
            return f"{preview[:limit]}..."
        return preview or "<empty>"

    def _get_retry_after_seconds(self, resp, default_seconds=2):
        retry_after = resp.headers.get("Retry-After")
        if retry_after is None:
            return default_seconds

        try:
            return max(1, math.ceil(float(retry_after)))
        except (TypeError, ValueError):
            return default_seconds

    async def _read_json_response(self, resp, context):
        body = await resp.text()

        if resp.status >= 400:
            preview = self._format_response_preview(body)
            raise RuntimeError(f"{context} failed with HTTP {resp.status}: {preview}")

        if not body.strip():
            raise RuntimeError(f"{context} returned an empty response.")

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            preview = self._format_response_preview(body)
            raise RuntimeError(f"{context} returned invalid JSON: {preview}")

    async def request_json(self, session, method, url, context, headers=None, json_body=None, retries=5):
        for attempt in range(retries):
            async with session.request(method, url, headers=headers, json=json_body) as resp:
                if resp.status == 429:
                    retry_after = self._get_retry_after_seconds(resp)
                    print(
                        f"Rate limited for {context}. Waiting {retry_after}s before retry "
                        f"({attempt + 1}/{retries})."
                    )
                    if attempt == retries - 1:
                        preview = self._format_response_preview(await resp.text())
                        raise RuntimeError(
                            f"{context} is still rate limited after {retries} attempts: {preview}"
                        )
                    await asyncio.sleep(retry_after)
                    continue

                return await self._read_json_response(resp, context)

    def get_version_from_log(self):
        log_path = os.path.expandvars(r"%LOCALAPPDATA%\VALORANT\Saved\Logs\ShooterGame.log")

        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = re.search(r"(release-\d+\.\d+)(?:-shipping)?-(\d+-\d+)", line)
                    if match:
                        print("found version data")
                        return f"{match.group(1)}-shipping-{match.group(2)}"

        print("didnt find version data")
        return None

    async def lobby_load(self, party_id=None):
        self.frontend_data = {}
        self.handler = MatchDetectionHandler()
        if not await self.handler.detect_match_handler():
            return False
        if not self.handler.match_id_header or not self.handler.region or not self.handler.shard:
            return False

        session = SharedSession.get()
        party_info = await self.request_json(
            session,
            "GET",
            f"https://glz-{self.handler.region}-1.{self.handler.shard}.a.pvp.net/parties/v1/parties/{party_id}",
            "Party info request",
            headers=self.handler.match_id_header,
        )

        pmi = []
        for player in party_info.get("Members", []):
            pmi.append({
                "puuid": player.get("Subject"),
                "rank_up": self.ttr.get(player.get("CompetitiveTier", 0), "Unranked"),
                "level": player.get("PlayerIdentity", {}).get("AccountLevel", 0),
                "name": None,
                "tag": None
            })

        for player in pmi:
            self.frontend_data[player["puuid"]] = {
                **self._name_fields_for_puuid(player["puuid"], "N/A"),
                "agent": "N/A",
                "level": player.get("level"),
                "matches": "N/A",
                "wl": "N/A",
                "acs": "N/A",
                "kd": "N/A",
                "hs": "N/A",
                "rank": player.get("rank_up"),
                "rr": "N/A",
                "peak_rank": "Unranked",
                "peak_act": "N/A",
                "team": "Red",
                "puuid": player["puuid"]
            }
        self.apply_party_metadata()
        return True

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

            if self.gs[0] == "Competitive":
                if self.handler.player_info_pre:
                    if self.handler.player_info_pre["IsRanked"] == 0:
                        self.gs[0] = "Unrated"


    def set_party_detection_enabled(self, enabled):
        self.party_detection_enabled = bool(enabled)
        if not self.party_detection_enabled:
            self.party_tracker.clear_party_metadata(self.frontend_data)

    def apply_party_metadata(self):
        if not self.party_detection_enabled:
            return self.party_tracker.clear_party_metadata(self.frontend_data)
        return self.party_tracker.enrich_frontend_data(self.frontend_data)

    def _agent_name_for_puuid(self, puuid):
        character_id = self.ca.get(puuid)
        if not character_id:
            return "N/A"
        return self.uuid_handler.agent_converter(character_id) or "N/A"

    def _placeholder_name_fields(self, agent_name):
        placeholder = str(agent_name or "N/A")
        return {
            "name": placeholder,
            "game_name": placeholder,
            "tag": "",
            "name_source": "agent_placeholder",
            "xmpp_name_resolved": False,
        }

    def _name_fields_for_puuid(self, puuid, agent_name):
        existing = self.frontend_data.get(puuid) if isinstance(self.frontend_data, dict) else None
        if isinstance(existing, dict) and existing.get("xmpp_name_resolved"):
            return {
                "name": existing.get("name") or existing.get("display_name") or str(agent_name or "N/A"),
                "game_name": existing.get("game_name") or existing.get("name") or str(agent_name or "N/A"),
                "tag": existing.get("tag", ""),
                "name_source": existing.get("name_source") or "xmpp",
                "xmpp_name_resolved": True,
            }
        return self._placeholder_name_fields(agent_name)

    def _reset_match_state(self, current_match_id):
        self.used_puuids = []
        self.last_match_id = current_match_id
        self.frontend_data = {}
        self.cmp = []
        self.ca = {}
        self.zero_check = {}
        self.mmr = {}
        self.rating_changes = {}
        self.match_stats = {}
        self.pip = {}
        self.start = 5
        self.end = 10
        self.gs = []
        self.gs_func()
        self.done = 0
        self.skin_handler.skins = None
        self.skin_handler.skins_pre = None
        self.mmr_failures = {}
        self.full_stats_hydrated = False

    def _prepare_modified_header(self):
        self.modified_header = dict(self.handler.match_id_header or {})
        if self.version_data:
            self.modified_header["X-Riot-ClientVersion"] = self.version_data
        return bool(self.modified_header)

    def _team_for_enemy(self, ally_team):
        return "Blue" if ally_team == "Red" else "Red"

    def _fallback_name_fields(self, puuid, agent_name, team, slot_index):
        agent_name = str(agent_name or "N/A")
        if agent_name != "N/A":
            return self._name_fields_for_puuid(puuid, agent_name)
        label = "Ally" if team == self.pip.get("AllyTeam", {}).get("TeamID") else "Enemy"
        return self._placeholder_name_fields(f"{label} {slot_index}")

    def _rank_fields_for_puuid(self, puuid):
        mmr = self.mmr.get(puuid) or {}
        current = mmr.get("current_data") or {}
        highest = mmr.get("highest_rank") or {}
        return {
            "rank": current.get("currenttierpatched", "N/A"),
            "rr": current.get("ranking_in_tier", "N/A"),
            "peak_rank": highest.get("patched_tier", "N/A"),
            "peak_act": str(highest.get("season", "N/A")).upper(),
        }

    def _padded_rating_changes(self, changes, length=3):
        changes = list(changes or [])[:length]
        if len(changes) < length:
            changes.extend([0] * (length - len(changes)))
        return changes

    async def fetch_recent_rating_changes(self, puuid, session, end_index=3):
        try:
            rating_change = await self.request_json(
                session,
                "GET",
                f"https://pd.{self.handler.shard}.a.pvp.net/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex={end_index}&queue=competitive",
                f"Competitive updates request for {puuid}",
                headers=self.handler.match_id_header,
            )
        except RuntimeError as exc:
            print(exc)
            self.rating_changes[puuid] = self._padded_rating_changes([])
            return self.rating_changes[puuid]

        self.rating_changes[puuid] = self._padded_rating_changes(
            [match.get("RankedRatingEarned", 0) for match in rating_change.get("Matches", [])]
        )
        return self.rating_changes[puuid]

    async def fetch_level_from_latest_match(self, puuid, session):
        try:
            riot_name = await self.request_json(
                session,
                "GET",
                f"https://pd.{self.handler.shard}.a.pvp.net/match-history/v1/history/{puuid}?startIndex=0&endIndex=1",
                f"Fallback level match history request for {puuid}",
                headers=self.handler.match_id_header,
            )
            history = riot_name.get("History") or []
            if not history:
                return "N/A"

            match_id_name = history[0].get("MatchID")
            if not match_id_name:
                return "N/A"

            match_stats_name = await self.request_json(
                session,
                "GET",
                f"https://pd.{self.handler.shard}.a.pvp.net/match-details/v1/matches/{match_id_name}",
                f"Fallback level match details request for {puuid}",
                headers=self.handler.match_id_header,
            )
        except RuntimeError as exc:
            print(exc)
            return "N/A"

        for player in match_stats_name.get("players", []):
            if player.get("subject") == puuid:
                return player.get("accountLevel", "N/A")
        return "N/A"

    def _merge_player_row(self, puuid, stat_fields):
        existing = self.frontend_data.get(puuid, {})
        merged = dict(existing) if isinstance(existing, dict) else {}
        merged.update(stat_fields)
        self.frontend_data[puuid] = merged
        return merged

    def _apply_name_service_result(self, names_by_puuid):
        for puuid, name_data in names_by_puuid.items():
            player = self.frontend_data.get(puuid)
            if not player or player.get("xmpp_name_resolved"):
                continue
            game_name = str(name_data.get("GameName") or name_data.get("gameName") or "").strip()
            tag = str(name_data.get("TagLine") or name_data.get("tagLine") or "").strip()
            if not game_name:
                continue
            display = f"{game_name}#{tag}" if tag else game_name
            player.update({
                "name": display,
                "game_name": game_name,
                "tag": tag,
                "name_source": "name_service",
                "xmpp_name_resolved": False,
            })

    async def fetch_name_service_batch(self, puuids, session):
        if not puuids:
            return {}
        try:
            response = await self.request_json(
                session,
                "PUT",
                f"https://pd.{self.handler.shard}.a.pvp.net/name-service/v2/players",
                "Name service request",
                headers=self.modified_header,
                json_body=list(puuids),
                retries=1,
            )
        except RuntimeError as exc:
            print(exc)
            return {}
        if not isinstance(response, list):
            return {}
        result = {}
        for player in response:
            subject = str(player.get("Subject") or player.get("subject") or "").strip()
            if subject:
                result[subject] = player
        return result

    async def fetch_mmr_for_puuid(self, puuid, session, retry_rate_limited=True):
        retries = 5 if retry_rate_limited else 1
        try:
            valorant_mmr = await self.request_json(
                session,
                "GET",
                f"https://pd.{self.handler.shard}.a.pvp.net/mmr/v1/players/{puuid}",
                f"MMR request for {puuid}",
                headers=self.modified_header,
                retries=retries,
            )
        except RuntimeError as exc:
            self.mmr_failures[puuid] = "rate_limit" if "429" in str(exc).lower() or "rate limited" in str(exc).lower() else "error"
            print(exc)
            return False

        self.mmr_failures.pop(puuid, None)
        if valorant_mmr["LatestCompetitiveUpdate"]:
            peak_rank = 0
            peak_act = None
            for season in valorant_mmr["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"]:
                try:
                    for tier in valorant_mmr["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][season]["WinsByTier"]:
                        tier = int(tier)
                        if season in self.e1_to_e4 and tier > 20:
                            tier += 3
                        if tier >= peak_rank:
                            peak_rank = tier
                            peak_act = season
                except TypeError:
                    continue

            peak_act_final = self.uuid_handler.season_converter(peak_act)
            if len(peak_act_final) > 6:
                peak_act_final = "N/A"
            latest = valorant_mmr["LatestCompetitiveUpdate"]
            if latest["SeasonID"] == self.current_act:
                current_rank = self.ttr[latest["TierAfterUpdate"]]
                current_rr = latest["RankedRatingAfterUpdate"]
            else:
                current_rank = "Unranked"
                current_rr = 50
            self.mmr[puuid] = {
                "current_data": {
                    "currenttierpatched": current_rank,
                    "ranking_in_tier": current_rr,
                },
                "highest_rank": {
                    "patched_tier": self.ttr[peak_rank],
                    "peak_act": peak_act_final,
                    "season": peak_act_final,
                }
            }
        else:
            self.mmr[puuid] = {
                "current_data": {"currenttierpatched": "Unranked", "ranking_in_tier": 0},
                "highest_rank": {"patched_tier": "Unranked", "peak_act": "N/A", "season": "N/A"},
            }

        self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e10", "v25")
        self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e11", "v26")
        self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e12", "v27")
        self.mmr[puuid]["highest_rank"]["patched_tier"] = self.mmr[puuid]["highest_rank"]["patched_tier"].replace("Unset", "Unranked").replace("Unrated", "Unranked")
        self.mmr[puuid]["current_data"]["currenttierpatched"] = self.mmr[puuid]["current_data"]["currenttierpatched"].replace("Unset", "Unranked").replace("Unrated", "Unranked")
        return True

    async def pregame_roster(self, prematch_id=None, map_instalock=None):
        self.handler = MatchDetectionHandler(prematch_id=prematch_id) if prematch_id else MatchDetectionHandler()
        if not await self.handler.player_info_retrieval() or not self.handler.player_info_pre:
            return False
        current_match_id = self.handler.in_match
        if not current_match_id or not self.handler.match_id_header:
            return False
        if self.last_match_id != current_match_id:
            self._reset_match_state(current_match_id)
        self.pip = self.handler.player_info_pre
        if map_instalock and prematch_id and self.pip.get("MapID"):
            asyncio.create_task(map_instalock_agent(self.pip["MapID"], self.handler))
        if not self._prepare_modified_header():
            return False

        session = SharedSession.get()
        loadouts = await self.request_json(
            session,
            "GET",
            f"https://glz-{self.handler.region}-1.{self.handler.shard}.a.pvp.net/pregame/v1/matches/{current_match_id}/loadouts",
            "Pregame loadouts request",
            headers=self.modified_header,
        )
        self.skin_handler.skins = None
        self.skin_handler.skins_pre = loadouts

        ally_team = self.pip.get("AllyTeam", {}).get("TeamID", "Blue")
        enemy_team = self._team_for_enemy(ally_team)
        ally_players = self.pip.get("AllyTeam", {}).get("Players", [])
        ally_subjects = [p.get("Subject") for p in ally_players if p.get("Subject")]
        loadout_subjects = [p.get("Subject") for p in loadouts.get("Loadouts", []) if p.get("Subject")]
        enemy_subjects = [puuid for puuid in loadout_subjects if puuid not in set(ally_subjects)]
        self.cmp = ally_subjects + enemy_subjects
        self.ca = {p.get("Subject"): p.get("CharacterID") for p in ally_players if p.get("Subject")}
        for player in loadouts.get("Loadouts", []):
            subject = player.get("Subject")
            if subject and player.get("CharacterID"):
                self.ca[subject] = player.get("CharacterID")

        for index, puuid in enumerate(self.cmp):
            team = ally_team if puuid in ally_subjects else enemy_team
            team_index = (ally_subjects if team == ally_team else enemy_subjects).index(puuid) + 1
            agent_name = self._agent_name_for_puuid(puuid)
            self.frontend_data[puuid] = {
                **self._fallback_name_fields(puuid, agent_name, team, team_index),
                "agent": agent_name,
                "level": "N/A",
                "matches": "N/A",
                "wl": "N/A",
                "acs": "N/A",
                "kd": "N/A",
                "hs": "N/A",
                **self._rank_fields_for_puuid(puuid),
                "team": team,
                "rating_change": ["N/A", "N/A", "N/A"],
                "puuid": puuid,
            }

        self._apply_name_service_result(await self.fetch_name_service_batch(self.cmp, session))
        mmr_tasks = [asyncio.create_task(self.fetch_mmr_for_puuid(puuid, session)) for puuid in self.cmp]
        await asyncio.gather(*mmr_tasks)
        for puuid in self.cmp:
            if puuid in self.frontend_data:
                self.frontend_data[puuid].update(self._rank_fields_for_puuid(puuid))

        rating_tasks = [asyncio.create_task(self.fetch_recent_rating_changes(puuid, session, end_index=3)) for puuid in self.cmp]
        await asyncio.gather(*rating_tasks)
        for puuid in self.cmp:
            if puuid in self.frontend_data:
                self.frontend_data[puuid]["rating_change"] = self.rating_changes.get(puuid, [0, 0, 0])

        level_puuids = [
            puuid for puuid in self.cmp
            if self.frontend_data.get(puuid, {}).get("level") == "N/A"
        ]
        level_tasks = [
            asyncio.create_task(self.fetch_level_from_latest_match(puuid, session))
            for puuid in level_puuids
        ]
        if level_tasks:
            levels = await asyncio.gather(*level_tasks)
            for puuid, level in zip(level_puuids, levels):
                if puuid in self.frontend_data and level != "N/A":
                    self.frontend_data[puuid]["level"] = level

        self.used_puuids = list(self.cmp)
        await self.assign_skins()
        self.apply_party_metadata()
        self.full_stats_hydrated = False
        return True

    async def hydrate_match_stats(self):
        if not self.cmp or not getattr(self, "modified_header", None) or not self.handler.shard:
            return False
        session = SharedSession.get()
        retry_puuids = [puuid for puuid, reason in getattr(self, "mmr_failures", {}).items() if reason == "rate_limit"]
        if retry_puuids:
            await asyncio.gather(*[asyncio.create_task(self.fetch_mmr_for_puuid(puuid, session)) for puuid in retry_puuids])

        async def history_collector(puuid):
            try:
                if puuid not in self.mmr:
                    self.mmr[puuid] = {
                        "current_data": {"currenttierpatched": "N/A", "ranking_in_tier": "N/A"},
                        "highest_rank": {"patched_tier": "N/A", "peak_act": "N/A", "season": "N/A"},
                    }
                riot_matches = await self.request_json(
                    session,
                    "GET",
                    f"https://pd.{self.handler.shard}.a.pvp.net/match-history/v1/history/{puuid}?startIndex=0&endIndex=5&queue=competitive",
                    f"Competitive match history request for {puuid}",
                    headers=self.handler.match_id_header,
                )
                self.zero_check[puuid] = riot_matches["Total"]
                if riot_matches["Total"] == 0:
                    player = self.frontend_data.get(puuid, {})
                    player.update({
                        "matches": 0,
                        "wl": "N/A",
                        "acs": "N/A",
                        "kd": "N/A",
                        "hs": "N/A",
                        "rating_change": [0, 0, 0],
                        **self._rank_fields_for_puuid(puuid),
                    })
                    self.frontend_data[puuid] = player
                    return
                end_index = 3 if self.zero_check[puuid] >= 4 else self.zero_check[puuid]
                await self.fetch_recent_rating_changes(puuid, session, end_index=end_index)
                match_urls = [
                    f"https://pd.{self.handler.shard}.a.pvp.net/match-details/v1/matches/{match['MatchID']}"
                    for match in riot_matches["History"]
                ]
                self.match_stats[puuid] = await asyncio.gather(*[
                    self.fetch(session, match_url, headers=self.modified_header) for match_url in match_urls
                ])
                await self.calc_stats(puuid, session)
            except Exception as exc:
                print(f"Hydration skipped for {puuid}: {exc}")

        await asyncio.gather(*[asyncio.create_task(history_collector(puuid)) for puuid in self.cmp])
        self.apply_party_metadata()
        self.full_stats_hydrated = True
        return True

    async def core_game_basics(self, match_id=None):
        self.handler = MatchDetectionHandler(match_id=match_id) if match_id else MatchDetectionHandler()
        if not await self.handler.player_info_retrieval() or not self.handler.player_info:
            return False
        current_match_id = self.handler.in_match
        if self.last_match_id != current_match_id:
            self._reset_match_state(current_match_id)
        if not self._prepare_modified_header():
            return False
        self.cmp = [player.get("Subject") for player in self.handler.player_info.get("Players", []) if player.get("Subject")]
        self.ca = {
            player.get("Subject"): player.get("CharacterID")
            for player in self.handler.player_info.get("Players", [])
            if player.get("Subject")
        }
        for player in self.handler.player_info.get("Players", []):
            puuid = player.get("Subject")
            if not puuid:
                continue
            agent_name = self._agent_name_for_puuid(puuid)
            existing = self.frontend_data.get(puuid, {})
            existing.update({
                "agent": agent_name,
                "team": player.get("TeamID"),
                "puuid": puuid,
            })
            if not existing.get("name"):
                existing.update(self._name_fields_for_puuid(puuid, agent_name))
            self.frontend_data[puuid] = existing
        self.apply_party_metadata()
        return True

    async def valo_stats(self, prematch_id=None, match_id=None, map_instalock=None):
        if prematch_id:
            self.handler = MatchDetectionHandler(prematch_id=prematch_id)
        elif match_id:
            self.handler = MatchDetectionHandler(match_id=match_id)
        else:
            self.handler = MatchDetectionHandler()

        if not await self.handler.player_info_retrieval():
            return False

        current_match_id = self.handler.in_match
        if not current_match_id or not self.handler.match_id_header:
            return False

        if self.last_match_id != current_match_id:
            self._reset_match_state(current_match_id)

        if self.handler.player_info_pre:
            self.pip = self.handler.player_info_pre

            if map_instalock and prematch_id and self.pip.get("MapID"):
                asyncio.create_task(map_instalock_agent(self.pip["MapID"], self.handler))

        if self.handler.player_info:
            if not self.cmp:
                for player in self.handler.player_info["Players"]:
                    self.cmp.append(player.get("Subject"))
            elif len(self.cmp) < 10:
                for player in self.handler.player_info["Players"]:
                    try:
                        if player["TeamID"] != self.pip["AllyTeam"]["TeamID"]:
                            self.cmp.append(player.get("Subject"))
                    except:
                        pass
        elif self.pip:
            if not self.cmp:
                for player in self.pip["AllyTeam"]["Players"]:
                    self.cmp.append(player.get("Subject"))

        if self.cmp:
            if len(self.ca) < 10:
                self.ca = {}
                if self.handler.player_info:
                    for player in self.handler.player_info["Players"]:
                        self.ca[player.get("Subject")] = player.get("CharacterID")
                else:
                    for player in self.pip["AllyTeam"]["Players"]:
                        self.ca[player.get("Subject")] = player.get("CharacterID")

        if not self._prepare_modified_header():
            return False

        async def stat_collector(puuid, session):
            if puuid in self.used_puuids:
                return
            else:
                valorant_mmr = None

                valorant_mmr = await self.request_json(
                    session,
                    "GET",
                    f"https://pd.{self.handler.shard}.a.pvp.net/mmr/v1/players/{puuid}",
                    f"MMR request for {puuid}",
                    headers=self.modified_header,
                )

                if valorant_mmr["LatestCompetitiveUpdate"]:
                    peak_rank = 0
                    peak_act = None
                    for season in valorant_mmr["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"]:
                        try:
                            if season in self.e1_to_e4:
                                for tier in valorant_mmr["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][season][
                                    "WinsByTier"]:
                                    if int(tier) > 20:
                                        tier = int(tier) + 3
                                    if int(tier) >= peak_rank:
                                        peak_rank = int(tier)
                                        peak_act = season
                            else:
                                for tier in valorant_mmr["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][season][
                                    "WinsByTier"]:
                                    if int(tier) >= peak_rank:
                                        peak_rank = int(tier)
                                        peak_act = season
                        except TypeError:
                            continue

                    peak_act_final = self.uuid_handler.season_converter(peak_act)
                    if len(peak_act_final) > 6:
                        peak_act_final == "N/A"

                    if valorant_mmr["LatestCompetitiveUpdate"]["SeasonID"] == self.current_act:
                        self.mmr[puuid] = {
                            "current_data": {
                                "currenttierpatched": self.ttr[
                                    valorant_mmr["LatestCompetitiveUpdate"]["TierAfterUpdate"]],
                                "ranking_in_tier": valorant_mmr["LatestCompetitiveUpdate"]["RankedRatingAfterUpdate"]
                            },
                            "highest_rank": {
                                "patched_tier": self.ttr[peak_rank],
                                "peak_act": peak_act_final,
                                "season": peak_act_final
                            }
                        }
                    else:
                        self.mmr[puuid] = {
                            "current_data": {
                                "currenttierpatched": "Unranked",
                                "ranking_in_tier": 50
                            },
                            "highest_rank": {
                                "patched_tier": self.ttr[peak_rank],
                                "peak_act": peak_act_final,
                                "season": peak_act_final
                            }
                        }
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

                self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e10",
                                                                                                              "v25")
                self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e11",
                                                                                                              "v26")
                self.mmr[puuid]["highest_rank"]["season"] = self.mmr[puuid]["highest_rank"]["season"].replace("e12",
                                                                                                              "v27")

                self.mmr[puuid]["highest_rank"]["patched_tier"] = self.mmr[puuid]["highest_rank"][
                    "patched_tier"].replace("Unset", "Unranked")
                self.mmr[puuid]["highest_rank"]["patched_tier"] = self.mmr[puuid]["highest_rank"][
                    "patched_tier"].replace("Unrated", "Unranked")

                self.mmr[puuid]["current_data"]["currenttierpatched"] = self.mmr[puuid]["current_data"][
                    "currenttierpatched"].replace("Unset", "Unranked")
                self.mmr[puuid]["current_data"]["currenttierpatched"] = self.mmr[puuid]["current_data"][
                    "currenttierpatched"].replace("Unrated", "Unranked")

                riot_matches = await self.request_json(
                    session,
                    "GET",
                    f"https://pd.{self.handler.shard}.a.pvp.net/match-history/v1/history/{puuid}?startIndex={0}&endIndex={5}&queue=competitive",
                    f"Competitive match history request for {puuid}",
                    headers=self.handler.match_id_header,
                )

                self.zero_check[puuid] = (riot_matches["Total"])

                if riot_matches["Total"] == 0:
                    riot_name = await self.request_json(
                        session,
                        "GET",
                        f"https://pd.{self.handler.shard}.a.pvp.net/match-history/v1/history/{puuid}?startIndex={0}&endIndex={1}",
                        f"Fallback match history request for {puuid}",
                        headers=self.handler.match_id_header,
                    )

                    if riot_name["Total"] == 0:
                        agent_name = self._agent_name_for_puuid(puuid)
                        print(f"{puuid} ({agent_name}) has not played a game in the last 30 days")

                        if self.handler.player_info:
                            for player in self.handler.player_info["Players"]:
                                if player["Subject"] == puuid:
                                    bor = player["TeamID"]
                        elif self.handler.player_info_pre:
                            bor = self.handler.player_info_pre["AllyTeam"]["TeamID"]

                        self.frontend_data[puuid] = {
                            **self._name_fields_for_puuid(puuid, agent_name),
                            "agent": agent_name,
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
                            "team": bor,
                            "rating_change": [0, 0, 0],
                            "puuid": puuid
                        }
                        self.used_puuids.append(puuid)
                        return

                    match_id_name = riot_name["History"][0]["MatchID"]

                    print(f"session: {session}")
                    match_stats_name = await self.request_json(
                        session,
                        "GET",
                        f"https://pd.{self.handler.shard}.a.pvp.net/match-details/v1/matches/{match_id_name}",
                        f"Fallback match details request for {puuid}",
                        headers=self.handler.match_id_header,
                    )

                    ntl = []  # Name Tag Level
                    for player in match_stats_name["players"]:
                        if player["subject"] == puuid:
                            ntl.append({
                                "level": player.get("accountLevel"),
                            })

                    agent_name = self._agent_name_for_puuid(puuid)
                    print(f"{puuid} ({agent_name}) has not played competitive in the last 30 days/100 matches")

                    if self.handler.player_info:
                        for player in self.handler.player_info["Players"]:
                            if player["Subject"] == puuid:
                                bor = player["TeamID"]
                    elif self.handler.player_info_pre:
                        bor = self.handler.player_info_pre["AllyTeam"]["TeamID"]

                    self.frontend_data[puuid] = {
                        **self._name_fields_for_puuid(puuid, agent_name),
                        "agent": agent_name,
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
                        "team": bor,
                        "rating_change": [0, 0, 0],
                        "puuid": puuid
                    }
                    self.used_puuids.append(puuid)
                    return
                else:
                    if self.zero_check[puuid] >= 4:
                        end_index = 3
                    else:
                        end_index = self.zero_check[puuid]
                    rating_change = await self.request_json(
                        session,
                        "GET",
                        f"https://pd.{self.handler.shard}.a.pvp.net/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex={end_index}&queue=competitive",
                        f"Competitive updates request for {puuid}",
                        headers=self.handler.match_id_header,
                    )

                    self.rating_changes[puuid] = []
                    for match in rating_change["Matches"]:
                        self.rating_changes[puuid].append(match["RankedRatingEarned"])

                riot_match_ids = []
                for match in riot_matches["History"]:
                    riot_match_ids.append(match["MatchID"])

                match_urls = []
                for matchID in riot_match_ids:
                    match_urls.append(f"https://pd.{self.handler.shard}.a.pvp.net/match-details/v1/matches/{matchID}")

                async def gather_matches():
                    tasks = [self.fetch(session, match_url, headers=self.modified_header) for match_url in match_urls]
                    self.match_stats[puuid] = await asyncio.gather(*tasks)

                await gather_matches()
                self.used_puuids.append(puuid)
                await self.calc_stats(puuid, session)

        if not self.cmp:
            return False

        session = SharedSession.get()
        tasks = [asyncio.create_task(stat_collector(puuid, session)) for puuid in self.cmp]
        await asyncio.gather(*tasks)

        for index, puuid in enumerate(self.cmp):
            if puuid in self.frontend_data:
                agent_name = self._agent_name_for_puuid(puuid)
                self.frontend_data[puuid]["agent"] = agent_name
                if not self.frontend_data[puuid].get("xmpp_name_resolved"):
                    self.frontend_data[puuid].update(self._placeholder_name_fields(agent_name))

        await self.assign_skins()
        self.apply_party_metadata()
        self.full_stats_hydrated = True
        return True

    async def calc_stats(self, puuid, session):
        stats_list = []
        wl_list = []  # tracks wins and losses
        hs_list = []
        for match in self.match_stats[puuid]:
            for player in match["players"]:
                if player["subject"] == puuid:
                    stats_list.append({
                        "stats": player.get("stats"),
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
        try:
            hs = (headshots / (legshots + bodyshots + headshots)) * 100
        except ZeroDivisionError:
            hs = 0

        bor = self.frontend_data.get(puuid, {}).get("team")
        if self.handler.player_info:
            for player in self.handler.player_info["Players"]:
                if player["Subject"] == puuid:
                    bor = player["TeamID"]
                    break
        if bor not in ("Red", "Blue"):
            bor = self.frontend_data.get(puuid, {}).get("team", "Red")

        if len(self.rating_changes[puuid]) < 5:
            for i in range(5 - len(self.rating_changes[puuid])):
                self.rating_changes[puuid].append(0)

        if self.mmr[puuid]["current_data"]["currenttierpatched"] == "Unrated":
            self.mmr[puuid]["current_data"]["currenttierpatched"] = "Unranked"

        agent_name = self._agent_name_for_puuid(puuid)
        level = await self.fetch_level_from_latest_match(puuid, session)
        if level == "N/A":
            level = self.frontend_data.get(puuid, {}).get("level", "N/A")
        self._merge_player_row(puuid, {
            **self._name_fields_for_puuid(puuid, agent_name),
            "agent": agent_name,
            "level": level,
            "matches": match_count_kd,
            "wl": str(wl),
            "acs": str(acs)[:5],
            "kd": str(kd)[:4],
            "hs": str(hs)[:4],
            "rank": self.mmr[puuid]["current_data"]["currenttierpatched"],
            "rr": self.mmr[puuid]["current_data"]["ranking_in_tier"],
            "peak_rank": self.mmr[puuid]["highest_rank"]["patched_tier"],
            "peak_act": self.mmr[puuid]["highest_rank"]["season"].upper(),
            "team": bor,
            "rating_change": self.rating_changes[puuid],
            "puuid": puuid
        })

        print(
            f"{puuid} ({agent_name}) level is {level} | W/L % in last {match_count_kd} matches: {wl} | ACS in the last {match_count_kd} matches: {str(acs)[:5]} | KD in last {match_count_kd} matches: {str(kd)[0:4]} | HS in last {match_count_kd} matches: hs is: {str(hs)[:4]}% | current rank is: {self.mmr[puuid]['current_data']['currenttierpatched']} | current rr is: {self.mmr[puuid]['current_data']['ranking_in_tier']} | rr changes in last 5 matches: {self.rating_changes[puuid][0]}, {self.rating_changes[puuid][1]}, {self.rating_changes[puuid][2]}, {self.rating_changes[puuid][3]}, {self.rating_changes[puuid][4]} | highest rank was: {self.mmr[puuid]['highest_rank']['patched_tier']} | peak act was: {self.mmr[puuid]['highest_rank']['season']}")

    async def load_more_matches(self):
        if not getattr(self, "full_stats_hydrated", False):
            return False
        if not self.cmp or not getattr(self, "modified_header", None) or not self.handler.shard:
            return False

        session = SharedSession.get()
        for puuid in self.cmp:
            if self.zero_check[puuid] <= self.start:
                continue


            url = f"https://pd.{self.handler.shard}.a.pvp.net/match-history/v1/history/{puuid}?startIndex={self.start}&endIndex={self.end}&queue=competitive"
            try:
                self.riot_matches_new = await self.request_json(
                    session,
                    "GET",
                    url,
                    f"Load more match history request for {puuid}",
                    headers=self.modified_header,
                )
            except RuntimeError as exc:
                print(exc)
                continue

            riot_match_ids_new = [match["MatchID"] for match in self.riot_matches_new["History"]]
            match_urls_new = [f"https://pd.{self.handler.shard}.a.pvp.net/match-details/v1/matches/{mid}" for mid in
                              riot_match_ids_new]

            tasks = [self.fetch(session, match_url, headers=self.handler.match_id_header) for match_url in
                     match_urls_new]
            new_matches = await asyncio.gather(*tasks)

            self.match_stats[puuid].extend(new_matches)

            await self.calc_stats(puuid, session)

            self.apply_party_metadata()

            print("load more matches finished")

        self.start += 5
        self.end += 5

    async def assign_skins(self, on_update=None):
        if not self.handler.in_match or not self.handler.match_id_header or not self.handler.region or not self.handler.shard:
            return False

        if len(self.used_puuids) == len(self.cmp):
            session = SharedSession.get()
            tasks = [
                self.skin_handler.assign_skins(
                    puuid,
                    self.handler.in_match,
                    self.handler.match_id_header,
                    self.handler.region,
                    self.handler.shard,
                    session
                )
                for puuid in self.used_puuids
            ]

            skin_results = await asyncio.gather(*tasks)

            for puuid, skins in zip(self.used_puuids, skin_results):
                self.frontend_data[puuid]["skins"] = skins

    async def fetch(self, session, url, headers=None, retries=3):
        try:
            return await self.request_json(
                session,
                "GET",
                url,
                f"Match detail fetch for {url}",
                headers=headers,
                retries=retries,
            )
        except RuntimeError as exc:
            print(exc)
            return None
