import os

from core.player_display import PlayerDisplayFormatter


SPECIAL_BUDDY_UUID = "a57aa3d0-4ad0-b06a-6c54-338cb3ea6b41"


def _default_resource_path(relative_path):
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def _existing_asset_path(relative_path, resource_path_resolver):
    path = resource_path_resolver(relative_path)
    return path if os.path.exists(path) else ""


def _agent_icon_path(agent_name, resource_path_resolver):
    filename = str(agent_name or "").replace("/", "_")
    if not filename:
        return ""
    return _existing_asset_path(os.path.join("assets", "agents", f"{filename}.png"), resource_path_resolver)


def _rank_icon_path(rank_name, resource_path_resolver):
    rank_name = str(rank_name or "").strip()
    if not rank_name:
        return ""
    return _existing_asset_path(os.path.join("assets", "ranks", f"{rank_name}.png"), resource_path_resolver)


def _normalize_asset_id(asset_id):
    return str(asset_id or "").strip().lower()


def _skin_asset_path(asset_id, resource_path_resolver):
    normalized_id = _normalize_asset_id(asset_id)
    if not normalized_id:
        return ""
    return _existing_asset_path(os.path.join("assets", "skins", f"{normalized_id}.png"), resource_path_resolver)


def _skin_id_from_skin_data(skin_data):
    if isinstance(skin_data, list):
        return skin_data[0] if skin_data else None
    return skin_data


def _weapon_icon_displays(player, resource_path_resolver):
    skins = player.get("skins") or {}
    if not isinstance(skins, dict):
        skins = {}

    weapon_icons = []
    for weapon_name in ("Vandal", "Phantom"):
        skin_id = _skin_id_from_skin_data(skins.get(weapon_name))
        weapon_icons.append(
            {
                "weaponName": weapon_name,
                "iconPath": _skin_asset_path(skin_id, resource_path_resolver),
            }
        )
    return weapon_icons


def _first_rating_change(player):
    changes = player.get("rating_change", []) if isinstance(player, dict) else []
    if isinstance(changes, (list, tuple)) and changes:
        return changes[0]
    return 0


def _rating_change_displays(player, formatter):
    changes = player.get("rating_change", []) if isinstance(player, dict) else []
    if not isinstance(changes, (list, tuple)):
        changes = []

    displays = [
        formatter.rating_change_display(change)
        for change in list(changes)[:3]
    ]
    if not displays:
        displays = [formatter.rating_change_display(0)]

    return [
        {
            "valueText": display.text,
            "text": display.text,
            "numericValue": int(change) if isinstance(change, int) else _coerce_int(change),
            "tone": display.tone,
            "tooltip": display.tooltip if hasattr(display, "tooltip") else display.text,
        }
        for change, display in zip(list(changes)[:3] or [0], displays)
    ]


def _coerce_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _party_group_id(player):
    for key in ("partyGroupId", "party_group_id", "party_id", "partyId"):
        value = player.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _player_key(player, formatter):
    puuid = str(player.get("puuid", "") or "").strip()
    if puuid:
        return puuid
    return formatter.build_player_clipboard_name(player)


def _rr_text_and_progress(player):
    rr_value = player.get("rr", "N/A") if isinstance(player, dict) else "N/A"
    rr_text = str(rr_value if rr_value not in (None, "") else "N/A")
    if rr_text == "N/A":
        return "RR N/A", 0

    try:
        progress = max(0, min(int(float(rr_text)), 100))
    except (TypeError, ValueError):
        progress = 0
    return f"{rr_text} RR", progress


def build_player_card_display(
    player,
    *,
    formatter=None,
    flagged_players=None,
    resource_path_resolver=None,
    buddy_uuid=SPECIAL_BUDDY_UUID,
):
    player = player if isinstance(player, dict) else {}
    formatter = formatter or PlayerDisplayFormatter(flagged_players)
    resource_path_resolver = resource_path_resolver or _default_resource_path

    display_name = (
        str(player.get("name", "") or player.get("display_name", "") or player.get("game_name", "") or "Unknown")
        .strip()
        or "Unknown"
    )
    game_tag = str(player.get("tag", "") or player.get("game_tag", "") or "").strip()
    tag_line = f"#{game_tag}" if game_tag else ""
    clipboard_name = formatter.build_player_clipboard_name(player)

    agent_name = str(player.get("agent", "Unknown") or "Unknown")
    rank_text = formatter.current_rank_display(player)
    rank_key = str(player.get("rank", "Unknown") or "Unknown")
    peak_rank_text = formatter.peak_rank_display(player)
    peak_rank_key = formatter.peak_rank_icon_key(player)

    kd_text = formatter.stat_display_value(player, "kd")
    hs_raw = player.get("hs", "N/A")
    hs_text = formatter.stat_display_value(player, "hs")
    win_rate_text = formatter.stat_display_value(player, "wl")
    acs_text = formatter.stat_display_value(player, "acs")
    games_text = formatter.stat_display_value(player, "matches")
    rating_change = formatter.rating_change_display(_first_rating_change(player))
    rating_changes = _rating_change_displays(player, formatter)
    rr_text, rr_progress = _rr_text_and_progress(player)

    return {
        "displayName": display_name,
        "playerKey": _player_key(player, formatter),
        "tagLine": tag_line,
        "clipboardName": clipboard_name,
        "trackerUrl": formatter.build_tracker_url(clipboard_name),
        "vtlUrl": f"https://vtl.lol/id/{str(player.get('puuid', '') or '').strip()}",
        "puuid": str(player.get("puuid", "") or "").strip(),
        "copyIconPath": _existing_asset_path(os.path.join("assets", "copy-regular.png"), resource_path_resolver),
        "vtlIconPath": _existing_asset_path(os.path.join("assets", "vtl.png"), resource_path_resolver),
        "flagIconPath": _existing_asset_path(os.path.join("assets", "flag-solid.png"), resource_path_resolver),
        "levelText": str(player.get("level", "N/A") if player.get("level", "N/A") not in (None, "") else "N/A"),
        "agentName": agent_name,
        "agentIconPath": _agent_icon_path(agent_name, resource_path_resolver),
        "weaponIcons": _weapon_icon_displays(player, resource_path_resolver),
        "rankText": rank_text,
        "rankIconPath": _rank_icon_path(rank_key, resource_path_resolver),
        "peakRankText": peak_rank_text,
        "peakActText": formatter.peak_act_display(player.get("peak_act", "N/A")),
        "peakRankIconPath": _rank_icon_path(peak_rank_key, resource_path_resolver),
        "rrText": rr_text,
        "rrProgress": rr_progress,
        "gamesText": games_text,
        "kdText": kd_text,
        "kdTone": formatter.stat_colour_category(kd_text, "kd") or "neutral",
        "hsText": hs_text,
        "hsTone": formatter.stat_colour_category(hs_raw, "hs") or "neutral",
        "winRateText": win_rate_text,
        "winRateTone": formatter.stat_colour_category(win_rate_text, "wl") or "neutral",
        "acsText": acs_text,
        "acsTone": formatter.stat_colour_category(acs_text, "acs") or "neutral",
        "ratingChangeText": rating_change.text,
        "ratingChangeTone": rating_change.tone,
        "ratingChanges": rating_changes,
        "isFlagged": formatter.player_is_flagged(player),
        "flagTooltip": formatter.get_flag_tooltip_for_player(player),
        "hasBuddyEquipped": formatter.player_has_buddy_equipped(player, buddy_uuid),
        "partyGroupId": _party_group_id(player),
    }


def build_player_card_displays(
    players,
    *,
    formatter=None,
    flagged_players=None,
    resource_path_resolver=None,
    buddy_uuid=SPECIAL_BUDDY_UUID,
):
    formatter = formatter or PlayerDisplayFormatter(flagged_players)
    if isinstance(players, dict):
        players = players.values()
    return [
        build_player_card_display(
            player,
            formatter=formatter,
            resource_path_resolver=resource_path_resolver,
            buddy_uuid=buddy_uuid,
        )
        for player in (players or [])
    ]
