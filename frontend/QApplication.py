from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton
)
from PySide6.QtCore import (Qt, QTimer, Slot, QUrl)
from PySide6.QtGui import (QPixmap, QIcon, QColor, QBrush, QDesktopServices)
import sys
import os
import aiohttp
import requests
import asyncio
import qasync
from core.api_client import ValoRank
from core.dodge_button import dodge
from core.lock_clove import LockClove

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    try:
        # When running from the .exe, PyInstaller stores files in a temp folder
        base_path = sys._MEIPASS
    except Exception:
        # When running in normal dev mode (not compiled)
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

valo_rank = ValoRank()
dodge_game = dodge()
il_clove = LockClove()


class ValorantStatsWindow(QMainWindow):
    def __init__(self, players=None):
        super().__init__()

        self.setWindowTitle("Who Will They Be")
        self.setMinimumSize(1500, 350)

        self.setWindowIcon(QIcon(resource_path("assets/logoone.png")))

        # Refresh Button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.run_valo_stats)

        # Load More Matches Button (10)
        self.load_more_matches_button = QPushButton("Load More Matches (10)")
        self.load_more_matches_button.clicked.connect(self.run_load_more_matches_button)

        # Lock Clove Button
        self.lock_clove = QPushButton("Lock Clove")
        self.lock_clove.clicked.connect(self.run_lock_clove)

        # Dodge Button
        self.dodge_button = QPushButton("Dodge Game")
        self.dodge_button.clicked.connect(self.run_dodge_button)

        # Two tables (left and right)
        self.table_left = self.create_table()
        self.table_right = self.create_table()

        # Synchronize scrolling between tables
        self.table_left.verticalScrollBar().valueChanged.connect(
            self.table_right.verticalScrollBar().setValue
        )
        self.table_right.verticalScrollBar().valueChanged.connect(
            self.table_left.verticalScrollBar().setValue
        )

        # Preload agent icons
        from core.asset_loader import download_and_cache_agent_icons
        self.agent_icons = download_and_cache_agent_icons()

        # Split players by team

        # Populate tables if data provided
        if players:
            self.load_players(players)

        # Layout
        layout = QVBoxLayout()
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(self.table_left)
        tables_layout.addWidget(self.table_right)
        layout.addWidget(self.lock_clove)
        layout.addWidget(self.dodge_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.load_more_matches_button)
        layout.addLayout(tables_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ---------------------------------------------------------
    # Utility setup methods
    # ---------------------------------------------------------
    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels(["Name", "Agent", "Level", "Matches", "W/L", "KD", "HS", "Rank", "RR", "Peak Rank", "Peak Act"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.cellClicked.connect(self.on_cell_clicked)
        return table

    def on_cell_clicked(self, row, column):
        if column == 0:  # only make column 1 clickable
            sender_table = self.sender()  # figure out which table sent the signal
            item = sender_table.item(row, column)
            if item:
                text = item.text()
                safe_text = text.replace("#", "%23")
                QDesktopServices.openUrl(QUrl(
                    f"https://tracker.gg/valorant/profile/riot/{safe_text}/overview?platform=pc&playlist=competitive&season=4c4b8cff-43eb-13d3-8f14-96b783c90cd2"
                ))

    def safe_load_players(self, data):
        QTimer.singleShot(0, lambda: self.load_players(data))

    def run_lock_clove(self):
        asyncio.create_task(il_clove.lock_clove_func())

    def run_dodge_button(self):
        asyncio.create_task(dodge_game.dodge_func())

    def run_valo_stats(self):
        """Run the async refresh task without blocking UI"""
        asyncio.create_task(self.refresh_data())

    def run_load_more_matches_button(self):
        asyncio.create_task(self.run_load_more_matches())

    async def run_load_more_matches(self):
        await valo_rank.load_more_matches(on_update=self.safe_load_players)


    async def refresh_data(self):
        """Actually run valo_stats() and update the table"""
        print("Fetching latest Valorant stats...")
        await valo_rank.valo_stats(on_update=self.safe_load_players)  # await your async API call
        print("✅ Data fetched. Refreshing table...")
        self.load_players(valo_rank.frontend_data)

    def fetch_agent_icons(self):
        """Fetch agent display icons and return a dict: {'Jett': QPixmap(...), ...}"""
        icons = {}
        try:
            response = requests.get("https://valorant-api.com/v1/agents")
            agents = response.json()["data"]
            for agent in agents:
                if not agent.get("isPlayableCharacter", False):
                    continue
                name = agent["displayName"]
                icon_url = agent.get("displayIconSmall") or agent.get("displayIcon")
                if not icon_url:
                    continue
                img_data = requests.get(icon_url).content
                pixmap = QPixmap(resource_path(f"assets/agents/{agent_name}.png"))
                pixmap.loadFromData(img_data)
                icons[name] = pixmap
        except Exception as e:
            print(f"⚠️ Failed to fetch agent icons: {e}")
        return icons

    # ---------------------------------------------------------
    # Main data-loading logic (two-column layout)
    # ---------------------------------------------------------
    def load_players(self, players):
        """Display up to 12 player entries, split into two tables if >5."""
        if not players:
            return

        self.left_players = []
        self.right_players = []
        for x in players:
            if x.get("team") == "Red":
                self.left_players.append(x)
            elif x.get("team") == "Blue":
                self.right_players.append(x)

        self.fill_table(self.table_left, self.left_players)
        self.fill_table(self.table_right, self.right_players)

    def fill_table(self, table, players):
        """Helper to fill a single table with player data."""
        table.setRowCount(len(players))

        RANK_COLOURS = {
            "Unranked": "#9e9e9e",
            "Iron": "#8d8d8d",
            "Bronze": "#cd7f32",
            "Silver": "#c0c0c0",
            "Gold": "#ffcc33",
            "Platinum": "#00bfff",
            "Diamond": "#b366ff",
            "Ascendant": "#4cff8f",
            "Immortal": "#fa2a55",
            "Radiant": "#ffff66",
        }

        for row, player in enumerate(players):
            name = QTableWidgetItem(str(player.get("name", "Unknown")))
            level = QTableWidgetItem(str(player.get("level", "N/A")))
            matches = QTableWidgetItem(str(player.get("matches", 0)))
            wl_value = player.get("wl", "N/A")
            wl = QTableWidgetItem(str(wl_value))
            kd_value = player.get("kd", "N/A")
            kd = QTableWidgetItem(str(kd_value))
            hs_value = player.get("hs", "N/A")
            if str(hs_value) == "N/A":
                hs = QTableWidgetItem(f"{str(hs_value)}")
            else:
                hs = QTableWidgetItem(f"{str(hs_value)}%")
            rank_value = str(player.get("rank", "Unranked"))
            rank = QTableWidgetItem(rank_value)
            rr = QTableWidgetItem(str(player.get("rr", "N/A")))
            peak_value = str(player.get("peak_rank", "Unranked"))
            peak = QTableWidgetItem(peak_value)
            peak_act = QTableWidgetItem(str(player.get("peak_act", "N/A")))

            agent_name = str(player.get("agent", "Unknown"))
            agent_icon = self.agent_icons.get(agent_name)
            agent_label = QLabel()
            if agent_icon:
                agent_label.setPixmap(agent_icon.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                agent_label.setAlignment(Qt.AlignCenter)
            elif agent_name == "[]":
                agent_label.setText("N/A")
                agent_label.setAlignment(Qt.AlignCenter)
            else:
                agent_label.setText(agent_name)
                agent_label.setAlignment(Qt.AlignCenter)

            # --- WL color coding ---
            try:
                wl_float = float(wl_value[:-1])
                if wl_float < 45:
                    wl.setForeground(QBrush(QColor("red")))
                elif wl_float < 55:
                    wl.setForeground(QBrush(QColor("gold")))
                else:
                    wl.setForeground(QBrush(QColor("limegreen")))
            except ValueError:
                pass  # e.g. "N/A"

            # --- KD color coding ---
            try:
                kd_float = float(kd_value)
                if kd_float < 0.9:
                    kd.setForeground(QBrush(QColor("red")))
                elif kd_float < 1.2:
                    kd.setForeground(QBrush(QColor("gold")))
                else:
                    kd.setForeground(QBrush(QColor("limegreen")))
            except ValueError:
                pass  # e.g. "N/A"

            # --- HS color coding ---
            try:
                hs_float = float(hs_value)
                if hs_float < 20:
                    hs.setForeground(QBrush(QColor("red")))
                elif hs_float < 30:
                    hs.setForeground(QBrush(QColor("gold")))
                else:
                    hs.setForeground(QBrush(QColor("limegreen")))
            except ValueError:
                pass # e.g. "N/A"


            # --- Rank colour coding ---
            for key, color in RANK_COLOURS.items():
                if key.lower() in rank_value.lower():
                    rank.setForeground(QBrush(QColor(color)))
                    break

            # --- Peak rank colour coding ---
            for key, color in RANK_COLOURS.items():
                if key.lower() in peak_value.lower():
                    peak.setForeground(QBrush(QColor(color)))
                    break

            for col, item in enumerate([name, None, level, matches, wl, kd, hs, rank, rr, peak, peak_act]):
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row, col, item)

            table.setCellWidget(row, 1, agent_label)

        table.resizeColumnsToContents()


# ---------------------------------------------------------
# Async entry point for qasync
# ---------------------------------------------------------
async def main():
    # Create window immediately — no waiting
    window = ValorantStatsWindow([])
    window.show()

    # Start fetching data asynchronously
    asyncio.create_task(window.refresh_data())

    return window  # Keep a reference so it doesn't get garbage-collected


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logoone.png")))
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Start async app
    window = loop.run_until_complete(main())
    with loop:
        loop.run_forever()