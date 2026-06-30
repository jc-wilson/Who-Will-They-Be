from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class RatingChangeDisplay:
    text: str
    tone: str


class PlayerDisplayFormatter:
    def __init__(self, flagged_players=None):
        self.flagged_players = dict(flagged_players or {})

    def set_flagged_players(self, flagged_players):
        self.flagged_players = dict(flagged_players or {})

    @staticmethod
    def normalize_asset_id(asset_id):
        return str(asset_id or "").strip().lower()

    @staticmethod
    def build_tracker_url(riot_id):
        safe_text = quote(str(riot_id), safe="")
        return "https://tracker.gg/valorant/profile/riot/" f"{safe_text}"

    @staticmethod
    def build_player_clipboard_name(player):
        player = player if isinstance(player, dict) else {}
        game_name = str(player.get("game_name", "") or "").strip()
        game_tag = str(player.get("tag", "") or player.get("game_tag", "") or "").strip()
        display_name = str(player.get("name", "") or player.get("display_name", "") or "Unknown").strip()

        if game_name and game_tag:
            return f"{game_name}#{game_tag}"
        return display_name or "Unknown"

    def player_is_flagged(self, player):
        player = player if isinstance(player, dict) else {}
        player_puuid = str(player.get("puuid", "") or "").strip()
        return bool(player_puuid) and player_puuid in self.flagged_players

    def get_flag_tooltip_for_player(self, player):
        player = player if isinstance(player, dict) else {}
        player_puuid = str(player.get("puuid", "") or "").strip()
        flagged_entry = self.flagged_players.get(player_puuid)
        if isinstance(flagged_entry, dict):
            reason_text = str(flagged_entry.get("reason", "") or "").strip()
            if reason_text:
                return reason_text
            return "Flagged player"
        return "Toggle flagged player"

    @staticmethod
    def stat_colour_category(value, category):
        colour = None
        try:
            if category == "wl":
                val = float(str(value).replace("%", ""))
                if val < 47:
                    colour = "red"
                elif val < 53:
                    colour = "gold"
                elif val < 60:
                    colour = "limegreen"
                else:
                    colour = "cyan"
            elif category == "acs":
                val = float(value)
                if val < 200:
                    colour = "red"
                elif val < 225:
                    colour = "gold"
                elif val < 250:
                    colour = "limegreen"
                else:
                    colour = "cyan"
            elif category == "kd":
                val = float(value)
                if val < 0.9:
                    colour = "red"
                elif val < 1.1:
                    colour = "gold"
                elif val < 1.25:
                    colour = "limegreen"
                else:
                    colour = "cyan"
            elif category == "hs":
                val = float(value)
                if val < 20:
                    colour = "red"
                elif val < 30:
                    colour = "gold"
                elif val < 40:
                    colour = "limegreen"
                else:
                    colour = "cyan"
        except (TypeError, ValueError):
            colour = None
        return colour

    @staticmethod
    def stat_display_value(player, key):
        player = player if isinstance(player, dict) else {}
        if key == "matches":
            return str(player.get("matches", 0))
        if key == "hs":
            hs_raw = player.get("hs", "N/A")
            return f"{hs_raw}%" if str(hs_raw) not in ("N/A", "[]") else str(hs_raw)
        return str(player.get(key, "N/A"))

    @staticmethod
    def rating_change_display(change):
        text = str(change).replace("-", "")
        try:
            val = float(change)
        except (ValueError, TypeError):
            return RatingChangeDisplay(text=text, tone="neutral")

        if val > 0:
            return RatingChangeDisplay(text=text, tone="positive")
        if val < 0:
            return RatingChangeDisplay(text=text, tone="negative")
        return RatingChangeDisplay(text=text, tone="neutral")

    @staticmethod
    def current_rank_display(player):
        player = player if isinstance(player, dict) else {}
        rank_name = str(player.get("rank", "Unknown"))
        return "N/A" if rank_name in ("[]", "") else rank_name

    @staticmethod
    def peak_rank_display(player):
        player = player if isinstance(player, dict) else {}
        peak_name = str(player.get("peak_rank", "Unknown"))
        if peak_name.upper() == "UNRANKED" or peak_name in ("[]", ""):
            return "N/A"
        return peak_name

    @staticmethod
    def peak_rank_icon_key(player):
        player = player if isinstance(player, dict) else {}
        peak_name = str(player.get("peak_rank", "Unknown"))
        return "Unranked" if peak_name.upper() == "UNRANKED" else peak_name

    @staticmethod
    def peak_act_display(value):
        peak_act = str(value or "N/A").strip()
        if peak_act.upper() == "UNRANKED" or peak_act in ("[]", ""):
            return "N/A"
        return peak_act

    @staticmethod
    def extract_buddy_id_from_skin_data(skin_data):
        buddy_id = None
        if isinstance(skin_data, list):
            buddy_id = skin_data[1] if len(skin_data) > 1 else None
        elif isinstance(skin_data, dict):
            buddy_id = skin_data.get("buddy") or skin_data.get("Buddy") or skin_data.get("charm")
            if buddy_id is None:
                buddy_id = skin_data.get("CharmID") or skin_data.get("CharmLevelID")
        else:
            buddy_id = skin_data

        if isinstance(buddy_id, dict):
            return buddy_id.get("CharmID", buddy_id.get("CharmLevelID", ""))
        if isinstance(buddy_id, list):
            return buddy_id[0] if buddy_id else None
        return buddy_id

    def player_has_buddy_equipped(self, player, buddy_uuid):
        player = player if isinstance(player, dict) else {}
        target_buddy_id = self.normalize_asset_id(buddy_uuid)
        if not target_buddy_id:
            return False

        for skin_data in (player.get("skins") or {}).values():
            equipped_buddy_id = self.normalize_asset_id(
                self.extract_buddy_id_from_skin_data(skin_data)
            )
            if equipped_buddy_id == target_buddy_id:
                return True
        return False
