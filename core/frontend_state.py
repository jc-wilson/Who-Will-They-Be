from core.app_state import APP_STATE_VERSION, normalize_theme_surface_mode
from core.presence_mode import normalize_presence_mode


def normalize_queue_snipe_friend(friend_data):
    if not isinstance(friend_data, dict):
        return None

    puuid = str(friend_data.get("puuid", "") or "").strip()
    if not puuid:
        return None

    game_name = str(friend_data.get("game_name", "") or friend_data.get("gameName", "") or "").strip()
    game_tag = str(friend_data.get("game_tag", "") or friend_data.get("gameTag", "") or "").strip()
    display_name = str(friend_data.get("display_name", "") or friend_data.get("displayName", "") or "").strip()
    if not display_name:
        if game_name and game_tag:
            display_name = f"{game_name}#{game_tag}"
        else:
            display_name = game_name or puuid

    return {
        "puuid": puuid,
        "game_name": game_name,
        "game_tag": game_tag,
        "display_name": display_name,
        "pid": str(friend_data.get("pid", "") or friend_data.get("PID", "") or "").strip(),
    }


class FrontendWindowState:
    def __init__(self, persisted_state=None):
        persisted_state = persisted_state if isinstance(persisted_state, dict) else {}

        self.current_theme_name = str(persisted_state.get("selected_theme", "midnight") or "midnight")
        self.current_theme_surface_mode = normalize_theme_surface_mode(
            persisted_state.get("theme_surface_mode")
        )
        self.presence_mode = normalize_presence_mode(persisted_state.get("presence_mode"))
        self.map_agent_selection = dict(persisted_state.get("map_agent_selection", {}))
        self.flagged_players = dict(persisted_state.get("flagged_players", {}))
        self.co_play_history = dict(persisted_state.get("co_play_history", {"by_user": {}}))
        self.queue_snipe_selected_friend = normalize_queue_snipe_friend(
            persisted_state.get("queue_snipe_selected_friend")
        )

        self.left_players = []
        self.right_players = []
        self.seen_prematch_ids = set()
        self.seen_match_ids = set()
        self.last_seen = None
        self.refreshed_pregame = None
        self.refreshed_game = None
        self.instalocked_match_id = None
        self.last_update = None
        self.hydration_match_id = None
        self.hydrated_match_ids = set()

    @staticmethod
    def normalize_players(players):
        if isinstance(players, dict):
            return list(players.values())
        return list(players or [])

    def split_players(self, players, gamemode=None):
        player_iterable = self.normalize_players(players)
        left_players = []
        right_players = []
        is_deathmatch = gamemode == "Deathmatch"

        for index, player in enumerate(player_iterable):
            if is_deathmatch:
                if str(index / 2)[2] == "0":
                    left_players.append(player)
                else:
                    right_players.append(player)
                continue

            team = player.get("team") if isinstance(player, dict) else None
            if team == "Red":
                left_players.append(player)
            elif team == "Blue":
                right_players.append(player)

        self.left_players = left_players
        self.right_players = right_players
        return player_iterable, left_players, right_players

    @staticmethod
    def starting_side_label_text(players, local_puuid):
        side_by_team = {
            "Red": "DEFENSE",
            "Blue": "ATTACK",
        }
        local_puuid = str(local_puuid or "").strip()
        side = None
        if local_puuid:
            for player in FrontendWindowState.normalize_players(players):
                if not isinstance(player, dict):
                    continue
                if str(player.get("puuid", "")).strip() == local_puuid:
                    side = side_by_team.get(player.get("team"))
                    break

        if side:
            return f"STARTING SIDE: {side}"
        return ""

    def build_saved_payload(
        self,
        *,
        selected_theme,
        theme_surface_mode,
        presence_mode,
        selected_standard_agent,
        auto_lock_enabled,
        map_lock_enabled,
        queue_snipe_enabled,
        queue_snipe_selected_friend,
        flagged_players=None,
        co_play_history=None,
        map_agent_selection=None,
    ):
        self.current_theme_name = str(selected_theme or "midnight")
        self.current_theme_surface_mode = normalize_theme_surface_mode(theme_surface_mode)
        self.presence_mode = normalize_presence_mode(presence_mode)
        self.queue_snipe_selected_friend = normalize_queue_snipe_friend(queue_snipe_selected_friend)
        self.flagged_players = dict(flagged_players if flagged_players is not None else self.flagged_players)
        self.co_play_history = dict(co_play_history if co_play_history is not None else self.co_play_history)
        self.map_agent_selection = dict(map_agent_selection if map_agent_selection is not None else self.map_agent_selection)

        return {
            "version": APP_STATE_VERSION,
            "selected_theme": self.current_theme_name,
            "theme_surface_mode": self.current_theme_surface_mode,
            "presence_mode": self.presence_mode,
            "selected_standard_agent": selected_standard_agent or "Random",
            "auto_lock_enabled": bool(auto_lock_enabled),
            "map_lock_enabled": bool(map_lock_enabled),
            "queue_snipe_enabled": bool(queue_snipe_enabled) and self.queue_snipe_selected_friend is not None,
            "queue_snipe_selected_friend": dict(self.queue_snipe_selected_friend) if self.queue_snipe_selected_friend else None,
            "flagged_players": {
                str(puuid): dict(details) if isinstance(details, dict) else details
                for puuid, details in self.flagged_players.items()
            },
            "co_play_history": dict(self.co_play_history or {"by_user": {}}),
            "map_agent_selection": dict(self.map_agent_selection or {}),
        }

    def apply_normalized_saved_state(self, normalized_state):
        normalized_state = normalized_state if isinstance(normalized_state, dict) else {}
        self.current_theme_name = str(normalized_state.get("selected_theme", self.current_theme_name) or self.current_theme_name)
        self.current_theme_surface_mode = normalize_theme_surface_mode(
            normalized_state.get("theme_surface_mode", self.current_theme_surface_mode)
        )
        self.presence_mode = normalize_presence_mode(normalized_state.get("presence_mode", self.presence_mode))
        self.map_agent_selection = dict(normalized_state.get("map_agent_selection", {}))
        self.flagged_players = dict(normalized_state.get("flagged_players", {}))
        self.co_play_history = dict(normalized_state.get("co_play_history", {"by_user": {}}))
        self.queue_snipe_selected_friend = normalize_queue_snipe_friend(
            normalized_state.get("queue_snipe_selected_friend")
        )
        return self

    def update_queue_snipe_friend(self, friend_data):
        self.queue_snipe_selected_friend = normalize_queue_snipe_friend(friend_data)
        return self.queue_snipe_selected_friend

    def update_presence_mode(self, presence_mode):
        self.presence_mode = normalize_presence_mode(presence_mode)
        return self.presence_mode

    def update_theme_surface_mode(self, surface_mode):
        self.current_theme_surface_mode = normalize_theme_surface_mode(surface_mode)
        return self.current_theme_surface_mode

    def update_standard_agent_selection(self, agent_name, resolver):
        agent_text = str(agent_name or "Random")
        agent_value = resolver(agent_text)
        return agent_text, agent_value
