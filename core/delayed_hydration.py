def should_run_delayed_hydration(
    *,
    match_id,
    hydration_match_id,
    last_match_id,
    hydrated_match_ids,
    delay_ready_match_ids,
    coregame_ready_match_ids,
    running_match_ids,
):
    if not match_id:
        return False
    if match_id != hydration_match_id:
        return False
    if last_match_id != match_id:
        return False
    if match_id in hydrated_match_ids:
        return False
    if match_id not in delay_ready_match_ids:
        return False
    if match_id not in coregame_ready_match_ids:
        return False
    if match_id in running_match_ids:
        return False
    return True
