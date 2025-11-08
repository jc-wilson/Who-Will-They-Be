from core.detection import MatchDetectionHandler
import asyncio
import aiohttp
import requests

class LockClove:
    async def lock_clove_func(self):
        handler = MatchDetectionHandler()
        await asyncio.to_thread(handler.detect_match_handler)

        if handler.in_match:
            dodge_game = requests.post(
                f"https://glz-eu-1.eu.a.pvp.net/pregame/v1/matches/{handler.in_match}/select/1dbf2edd-4729-0984-3115-daa5eed44993",
                headers=handler.match_id_header
            )

        await asyncio.sleep(1)

        if handler.in_match:
            dodge_game = requests.post(
                f"https://glz-eu-1.eu.a.pvp.net/pregame/v1/matches/{handler.in_match}/lock/1dbf2edd-4729-0984-3115-daa5eed44993",
                headers=handler.match_id_header
            )
        else:
            print("not in match")