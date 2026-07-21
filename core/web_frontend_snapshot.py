import os
from pathlib import Path

from core.player_card_display import build_player_card_display


def _widget_text(window, widget_name, default=""):
    widget = getattr(window, widget_name, None)
    if widget is None or not hasattr(widget, "text"):
        return default
    return str(widget.text() or default)


def _widget_checked(window, widget_name):
    widget = getattr(window, widget_name, None)
    return bool(widget is not None and hasattr(widget, "isChecked") and widget.isChecked())


def _widget_enabled(window, widget_name):
    widget = getattr(window, widget_name, None)
    return bool(widget is not None and hasattr(widget, "isEnabled") and widget.isEnabled())


def _button_enabled(window, widget_name):
    return _widget_enabled(window, widget_name)


def _asset_url(path):
    path = str(path or "").strip()
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    if normalized.startswith(("file:/", "qrc:/", "http://", "https://", "data:")):
        return normalized
    try:
        return Path(os.path.abspath(path)).as_uri()
    except ValueError:
        return ""


def _coerce_rr_value(card):
    rr_text = str(card.get("rrText", "") or "").strip()
    rr_text = rr_text.replace("RR", "").strip()
    try:
        return max(0, min(int(float(rr_text)), 100))
    except (TypeError, ValueError):
        return 0


def _web_player_card(card):
    card = dict(card or {})

    for key in (
        "agentIconPath",
        "rankIconPath",
        "peakRankIconPath",
        "playerIconPath",
        "buddyIconPath",
        "copyIconPath",
        "vtlIconPath",
        "flagIconPath",
    ):
        card[key] = _asset_url(card.get(key))

    weapon_icons = []
    for weapon in card.get("weaponIcons") or []:
        if not isinstance(weapon, dict):
            continue
        next_weapon = dict(weapon)
        icon_url = _asset_url(next_weapon.get("iconPath"))
        next_weapon["iconPath"] = icon_url
        next_weapon["icon"] = icon_url
        weapon_icons.append(next_weapon)

    tag_line = str(card.get("tagLine", "") or "")
    rr_value = _coerce_rr_value(card)
    recent_rr_changes = list(card.get("ratingChanges") or [])

    card.update(
        {
            "name": card.get("displayName", ""),
            "tag": tag_line[1:] if tag_line.startswith("#") else tag_line,
            "agentIcon": card.get("agentIconPath", ""),
            "rankIcon": card.get("rankIconPath", ""),
            "rrValue": rr_value,
            "rrMax": 100,
            "peakRankIcon": card.get("peakRankIconPath", ""),
            "recentRrChanges": recent_rr_changes,
            "weapons": weapon_icons,
            "stats": {
                "games": {"label": "Games", "value": card.get("gamesText", "0"), "tone": "neutral"},
                "winRate": {"label": "Win %", "value": card.get("winRateText", "N/A"), "tone": card.get("winRateTone", "neutral")},
                "acs": {"label": "ACS", "value": card.get("acsText", "N/A"), "tone": card.get("acsTone", "neutral")},
                "kd": {"label": "K/D", "value": card.get("kdText", "N/A"), "tone": card.get("kdTone", "neutral")},
                "hs": {"label": "HS %", "value": card.get("hsText", "N/A"), "tone": card.get("hsTone", "neutral")},
            },
        }
    )
    if not card.get("puuid"):
        card["vtlUrl"] = ""
    return card


def _build_web_player_cards(players, *, formatter, flagged_players, resource_path_resolver, player_icon_resolver):
    if isinstance(players, dict):
        players = players.values()

    cards = []
    for player in players or []:
        try:
            cards.append(
                _web_player_card(
                    build_player_card_display(
                        player,
                        formatter=formatter,
                        flagged_players=flagged_players,
                        resource_path_resolver=resource_path_resolver,
                        player_icon_resolver=player_icon_resolver,
                    )
                )
            )
        except Exception as exc:
            print(f"[React Frontend] Skipping invalid player snapshot entry: {exc}")
    return cards


def _theme_options(window):
    definitions = getattr(window, "THEME_DEFINITIONS", None)
    order = getattr(window, "THEME_ORDER", None)
    if definitions is None:
        definitions = getattr(window.__class__, "THEME_DEFINITIONS", None)
    if not isinstance(definitions, dict):
        definitions = {}
    if order is None:
        order = tuple(definitions.keys())
    options = []
    for theme_name in order:
        definition = definitions.get(theme_name, {})
        options.append(
            {
                "name": theme_name,
                "label": definition.get("label", theme_name),
                "swatchA": definition.get("swatch_a", definition.get("accent", "")),
                "swatchB": definition.get("swatch_b", definition.get("panel", "")),
            }
        )
    return options


def _agent_options(window):
    owned_handler = getattr(window, "owned_agent_handler", None)
    agents = list(getattr(owned_handler, "combo", None) or getattr(owned_handler, "agents", None) or [])
    if not agents:
        agents = ["Random"]
    if "Random" not in agents:
        agents.insert(0, "Random")
    role_tokens = sorted(getattr(window, "MAP_SPECIFIC_ROLE_TOKENS", []) or [])
    options = []
    seen = set()
    for name in agents + role_tokens:
        if name in seen:
            continue
        seen.add(name)
        icon = ""
        try:
            resolver = getattr(window, "agent_asset_url", None)
            if callable(resolver):
                icon = resolver(name)
        except Exception:
            icon = ""
        options.append({"name": name, "icon": icon})
    return options


def _map_options(window):
    display_names = getattr(window, "MAP_DISPLAY_NAMES", None)
    if not isinstance(display_names, dict):
        display_names = {}
    map_selection = getattr(getattr(window, "window_state", None), "map_agent_selection", {}) or {}
    maps = sorted(set(display_names.keys()) | set(map_selection.keys()), key=lambda value: display_names.get(value, value))
    return [{"uuid": map_uuid, "name": display_names.get(map_uuid, map_uuid)} for map_uuid in maps]


def _loadout_editor_snapshot(window_state):
    editor = getattr(window_state, "loadout_editor", None)
    if isinstance(editor, dict):
        return editor
    return {"loading": False, "weapons": [], "presets": [], "selectedPreset": ""}


def build_web_frontend_snapshot(
    window,
    *,
    theme_palette,
    formatter=None,
    resource_path_resolver=None,
    player_icon_resolver=None,
):
    window_state = getattr(window, "window_state", None)
    flagged_players = getattr(window_state, "flagged_players", {}) if window_state is not None else {}
    left_players = getattr(window_state, "left_players", []) if window_state is not None else []
    right_players = getattr(window_state, "right_players", []) if window_state is not None else []

    return {
        "appTitle": "ValScanner",
        "status": {
            "message": getattr(window_state, "status_message", _widget_text(window, "status_value", "Initializing...")),
            "loading": bool(getattr(window_state, "loading_visible", False)),
            "progress": dict(getattr(window_state, "loading_progress", {}) or {}),
            "bridge": "web",
        },
        "theme": {
            "name": str(getattr(window, "current_theme_name", "") or ""),
            "surfaceMode": str(getattr(window, "current_theme_surface_mode", "") or ""),
            "palette": dict(theme_palette or {}),
            "options": _theme_options(window),
            "surfaceModes": ["transparent", "opaque"],
        },
        "themeName": str(getattr(window, "current_theme_name", "") or ""),
        "themeSurfaceMode": str(getattr(window, "current_theme_surface_mode", "") or ""),
        "themePalette": dict(theme_palette or {}),
        "header": {
            "gamemode": _widget_text(window, "gamemode_value", "Unknown"),
            "server": _widget_text(window, "server_value", "Unknown"),
            "startingSideText": _widget_text(window, "starting_side_label", ""),
            "canRefresh": _button_enabled(window, "refresh_button"),
            "canDodge": _button_enabled(window, "dodge_button"),
            "canLoadMore": _button_enabled(window, "load_more_matches_button"),
        },
        "gamemode": _widget_text(window, "gamemode_value", "Unknown"),
        "server": _widget_text(window, "server_value", "Unknown"),
        "startingSideText": _widget_text(window, "starting_side_label", ""),
        "agentLock": {
            "selectedAgent": _widget_text(window, "agent_select_btn", "Random"),
            "standardAgent": str(getattr(window, "last_standard_agent_text", "") or "Random"),
            "autoLockEnabled": _widget_checked(window, "auto_lock_switch"),
            "mapSpecificEnabled": _widget_checked(window, "map_lock_switch"),
            "mapSpecificAvailable": _widget_enabled(window, "map_lock_switch"),
            "options": _agent_options(window),
        },
        "selectedAgent": _widget_text(window, "agent_select_btn", "Random"),
        "autoLockEnabled": _widget_checked(window, "auto_lock_switch"),
        "mapSpecificEnabled": _widget_checked(window, "map_lock_switch"),
        "mapSpecificAvailable": _widget_enabled(window, "map_lock_switch"),
        "mapAgents": {
            "maps": _map_options(window),
            "selection": dict(getattr(window_state, "map_agent_selection", {}) or {}),
            "agentOptions": _agent_options(window),
        },
        "mapAgentSelection": dict(getattr(window_state, "map_agent_selection", {}) or {}),
        "queueSnipe": {
            "enabled": _widget_checked(window, "queue_snipe_switch"),
            "available": _widget_enabled(window, "queue_snipe_switch"),
            "selectedFriend": getattr(window_state, "queue_snipe_selected_friend", None),
            "friends": list(getattr(window_state, "queue_snipe_friends", []) or []),
            "loading": bool(getattr(window_state, "queue_snipe_loading", False)),
            "error": str(getattr(window_state, "queue_snipe_error", "") or ""),
        },
        "presence": {
            "mode": str(getattr(window_state, "presence_mode", "") or ""),
            "available": _widget_enabled(window, "presence_mode_switch"),
        },
        "tools": {
            "partyDetectionEnabled": bool(getattr(window, "party_detection_enabled", False)),
            "queueSnipeEnabled": _widget_checked(window, "queue_snipe_switch"),
            "presenceMode": str(getattr(window_state, "presence_mode", "") or ""),
        },
        "leftPlayers": _build_web_player_cards(
            left_players,
            formatter=formatter,
            flagged_players=flagged_players,
            resource_path_resolver=resource_path_resolver,
            player_icon_resolver=player_icon_resolver,
        ),
        "rightPlayers": _build_web_player_cards(
            right_players,
            formatter=formatter,
            flagged_players=flagged_players,
            resource_path_resolver=resource_path_resolver,
            player_icon_resolver=player_icon_resolver,
        ),
        "playerLoadouts": getattr(window_state, "player_loadout_modal", None),
        "ownedLoadoutEditor": _loadout_editor_snapshot(window_state),
        "activeModal": getattr(window_state, "active_modal", None),
        "modalData": dict(getattr(window_state, "modal_data", {}) or {}),
        "validationErrors": list(getattr(window_state, "validation_errors", []) or []),
        "toast": getattr(window_state, "toast", None),
        "prompts": {
            "update": getattr(window_state, "update_prompt", None),
            "restart": getattr(window_state, "restart_prompt", None),
        },
    }
