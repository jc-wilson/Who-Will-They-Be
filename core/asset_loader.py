import os
import re
import requests
from PySide6.QtGui import QPixmap

def download_and_cache_agent_icons(cache_dir="assets/agents"):
    """Download agent icons once and save them locally (if not already cached)."""
    os.makedirs(cache_dir, exist_ok=True)

    print("🖼️ Fetching agent list from Valorant API...")
    response = requests.get("https://valorant-api.com/v1/agents")
    response.raise_for_status()
    agents = response.json()["data"]

    icons = {}

    for agent in agents:
        if not agent.get("isPlayableCharacter", False):
            continue

        name = agent["displayName"]
        icon_url = agent.get("displayIconSmall") or agent.get("displayIcon")
        if not icon_url:
            continue

        # 🔧 sanitize filename (replace /, \, :, ?, etc.)
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", name)
        file_path = os.path.join(cache_dir, f"{safe_name}.png")

        # Download only if not already cached
        if not os.path.exists(file_path):
            print(f"⬇️ Downloading {name} icon...")
            img_data = requests.get(icon_url).content
            with open(file_path, "wb") as f:
                f.write(img_data)

        # Load QPixmap from local file
        pixmap = QPixmap(file_path)
        icons[name] = pixmap

    print(f"✅ Loaded {len(icons)} agent icons (cached in {cache_dir})")
    return icons