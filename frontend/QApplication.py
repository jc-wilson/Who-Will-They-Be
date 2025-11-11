from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QGridLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QComboBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import (Qt, QTimer, Slot, QUrl, QSize)
from PySide6.QtGui import (QPixmap, QIcon, QColor, QBrush, QDesktopServices, QFontDatabase, QFont)
import sys
import os
import aiohttp
import requests
import asyncio
import qasync
from core.api_client import ValoRank
from core.dodge_button import dodge
from core.instalock_agent import instalock_agent
from core.valorant_uuid import UUIDHandler

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
uuid_handler = UUIDHandler()
uuid_handler.agent_uuid_function()

class ValorantStatsWindow(QMainWindow):
    def __init__(self, players=None):
        super().__init__()

        font_path = resource_path("assets/fonts/proximanova_regular.ttf")
        print("🔍 Loading font from:", font_path)

        font_id = QFontDatabase.addApplicationFont(font_path)
        font_families = QFontDatabase.applicationFontFamilies(font_id)

        if font_families:
            app_font = QFont(font_families[0], 11)  # Optional size
            QApplication.setFont(app_font)
            print(f"✅ Loaded font: {font_families[0]}")
        else:
            print("⚠️ Failed to load custom font, falling back to default.")

        self.setWindowTitle("Who Will They Be")
        self.setMinimumSize(1500, 350)
        self.setWindowIcon(QIcon(resource_path("assets/logoone.png")))

        # Instalock agent list
        self.agent_label = QLabel("Choose your agent:")
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.on_selection_changed)
        self.combo.addItems([
            "Astra", "Breach", "Brimstone", "Chamber", "Clove", "Cypher",
            "Deadlock", "Fade", "Gekko", "Harbor", "Iso", "Jett", "KAY/O",
            "Killjoy", "Neon", "Omen", "Phoenix", "Raze", "Reyna", "Sage",
            "Skye", "Sova", "Tejo", "Veto", "Viper", "Vyse", "Waylay", "Yoru"
        ])
        self.combo.setCurrentIndex(4)

        # Lock Agent Button
        self.lock_agent_button = QPushButton("Lock Agent")
        self.lock_agent_button.clicked.connect(self.instalock_agent)

        # Current Gamemode
        self.gamemode_label = QLabel("Gamemode:")
        self.gamemode_label.setStyleSheet("color: #aaa;")
        self.gamemode_value = QLabel("Unknown")  # dynamic value
        self.gamemode_value.setStyleSheet("font-weight: 600; color: white;")

        gamemode_row = QHBoxLayout()
        gamemode_row.addWidget(self.gamemode_label)
        gamemode_row.addWidget(self.gamemode_value)
        gamemode_row.addStretch(1)  # optional, pushes text left

        # Current Server
        self.server_label = QLabel("Server:")
        self.server_label.setStyleSheet("color: #aaa;")
        self.server_value = QLabel("Unknown")  # dynamic value
        self.server_value.setStyleSheet("font-weight: 600; color: white;")

        server_row = QHBoxLayout()
        server_row.addWidget(self.server_label)
        server_row.addWidget(self.server_value)
        server_row.addStretch(1)

        # Refresh Button
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon(resource_path("assets/refresh.png")))
        self.refresh_button.setIconSize(QtCore.QSize(48, 48))
        self.refresh_button.setFlat(True)
        self.refresh_button.clicked.connect(self.run_valo_stats)

        # Load More Matches Button (10)
        self.load_more_matches_button = QPushButton("Load More Matches (10)")
        self.load_more_matches_button.clicked.connect(self.run_load_more_matches_button)

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

        # Preload rank icons
        from core.asset_loader import download_and_cache_rank_icons
        self.rank_icons = download_and_cache_rank_icons()

        # Split players by team
        # Populate tables if data provided
        if players:
            self.load_players(players)

        # ─────────────── Layout ───────────────

        # Grid layout for the center section (2 lines)
        center_grid = QGridLayout()
        center_grid.setHorizontalSpacing(8)
        center_grid.setVerticalSpacing(6)

        # Line 1 → "Choose your agent" + dropdown (centered)
        agent_row = QHBoxLayout()
        agent_row.setSpacing(8)
        agent_row.setAlignment(Qt.AlignCenter)
        agent_row.addWidget(self.agent_label)
        agent_row.addWidget(self.combo)
        center_grid.addLayout(agent_row, 0, 0, 1, 1)

        # Line 2 → 3 buttons centered
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.setAlignment(Qt.AlignCenter)
        button_row.addWidget(self.dodge_button)
        button_row.addWidget(self.load_more_matches_button)
        button_row.addWidget(self.lock_agent_button)
        center_grid.addLayout(button_row, 1, 0, 1, 1)

        # 🆕 Top-left vertical layout for the labels
        left_labels = QVBoxLayout()
        left_labels.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        left_labels.setSpacing(2)
        left_labels.addLayout(gamemode_row)
        left_labels.addLayout(server_row)

        # Parent horizontal layout to center everything and keep refresh button aligned right
        top_section = QHBoxLayout()
        top_section.setContentsMargins(10, 10, 10, 0)

        # 🆕 Add the stacked labels on the left
        top_section.addLayout(left_labels)

        # Center section
        top_section.addStretch(1)
        top_section.addLayout(center_grid)
        top_section.addStretch(1)

        # Refresh button on the right
        top_section.addWidget(self.refresh_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        # Tables layout
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(self.table_left)
        tables_layout.addWidget(self.table_right)

        # Combine everything
        layout = QVBoxLayout()
        layout.addLayout(top_section)
        layout.addLayout(tables_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ---------------------------------------------------------
    # Utility setup methods
    # ---------------------------------------------------------
    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(12)
        table.setHorizontalHeaderLabels(["Name", "Agent", "Level", "Matches", "W/L", "ACS", "KD", "HS", "Rank", "RR", "Peak Rank", "Peak Act"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.cellClicked.connect(self.on_cell_clicked)
        return table

    def on_cell_clicked(self, row, column):
        if column == 0:
            sender_table = self.sender()
            item = sender_table.item(row, column)
            if item:
                text = item.text()
                safe_text = text.replace("#", "%23")
                QDesktopServices.openUrl(QUrl(
                    f"https://tracker.gg/valorant/profile/riot/{safe_text}/overview?platform=pc&playlist=competitive&season=4c4b8cff-43eb-13d3-8f14-96b783c90cd2"
                ))

    def on_selection_changed(self, text):
        self.agent = uuid_handler.agent_converter_reversed(text)

    def instalock_agent(self):
        self.lock_agent_button.setEnabled(False)
        instalock_agent(self.agent)
        self.lock_agent_button.setEnabled(True)

    def safe_load_players(self, data):
        QTimer.singleShot(0, lambda: self.load_players(data))

    def run_dodge_button(self):
        self.dodge_button.setEnabled(False)
        asyncio.create_task(dodge_game.dodge_func())
        self.dodge_button.setEnabled(True)

    def run_valo_stats(self):
        """Run the async refresh task without blocking UI"""
        asyncio.create_task(self.refresh_data())

    def run_load_more_matches_button(self):
        self.load_more_matches_button.setEnabled(False)
        asyncio.create_task(self.run_load_more_matches())
        self.load_more_matches_button.setEnabled(True)

    async def run_load_more_matches(self):
        self.refresh_button.setEnabled(False)
        await valo_rank.load_more_matches(on_update=self.safe_load_players)
        self.refresh_button.setEnabled(True)


    async def refresh_data(self):
        self.refresh_button.setEnabled(False)  # disable the button
        """Actually run valo_stats() and update the table"""
        print("Fetching latest Valorant stats...")
        await valo_rank.valo_stats(on_update=self.safe_load_players)  # await your async API call
        print("✅ Data fetched. Refreshing table...")
        self.safe_load_players(valo_rank.frontend_data)
        try:
            self.gamemode_value.setText(valo_rank.gs[0])
            self.server_value.setText(valo_rank.gs[1])
        except IndexError:
            pass
        self.refresh_button.setEnabled(True)

    # ---------------------------------------------------------
    # Main data-loading logic (two-column layout)
    # ---------------------------------------------------------
    def load_players(self, players):
        """Display up to 12 player entries, split into two tables if >5."""
        if not players:
            return

        self.left_players = []
        self.right_players = []
        print(players)
        for x in players:
            if players[x].get("team") == "Red":
                self.left_players.append(players[x])
            elif players[x].get("team") == "Blue":
                self.right_players.append(players[x])

        self.fill_table(self.table_left, self.left_players)
        self.fill_table(self.table_right, self.right_players)

    def fill_table(self, table, players):
        """Helper to fill a single table with player data."""
        table.setRowCount(len(players))

        RANK_COLOURS = {
            "Unranked": "#6e7176",
            "Iron": "#4f514f",
            "Bronze": "#a5855d",
            "Silver": "#bbc2c2",
            "Gold": "#eccf56",
            "Platinum": "#59a9b6",
            "Diamond": "#b489c4",
            "Ascendant": "#6ae2af",
            "Immortal": "#bb3d65",
            "Radiant": "#ffffaa",
        }

        for row, player in enumerate(players):
            name = QTableWidgetItem(str(player.get("name", "Unknown")))
            level = QTableWidgetItem(str(player.get("level", "N/A")))
            matches = QTableWidgetItem(str(player.get("matches", 0)))
            wl_value = player.get("wl", "N/A")
            wl = QTableWidgetItem(str(wl_value))
            acs_value = player.get("acs", "N/A")
            acs = QTableWidgetItem(str(acs_value))
            kd_value = player.get("kd", "N/A")
            kd = QTableWidgetItem(str(kd_value))
            hs_value = player.get("hs", "N/A")
            if str(hs_value) == "N/A":
                hs = QTableWidgetItem(f"{str(hs_value)}")
            else:
                hs = QTableWidgetItem(f"{str(hs_value)}%")
#            rank_value = str(player.get("rank", "Unranked"))
#            rank = QTableWidgetItem(rank_value)
            rr = QTableWidgetItem(str(player.get("rr", "N/A")))
#            peak_value = str(player.get("peak_rank", "Unranked"))
#            peak = QTableWidgetItem(peak_value)
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

            rank_name = str(player.get("rank", "Unknown"))
            rank_icon = self.rank_icons.get(rank_name)
            rank_label = QLabel()
            if rank_icon:
                rank_label.setPixmap(rank_icon.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                rank_label.setAlignment(Qt.AlignCenter)
            elif rank_name == "N/A":
                rank_label.setText("N/A")
                rank_label.setAlignment(Qt.AlignCenter)
            else:
                rank_label.setText(rank_name)
                rank_label.setAlignment(Qt.AlignCenter)

            peak_name = str(player.get("peak_rank", "Unknown"))
            peak_icon = self.rank_icons.get(peak_name)
            peak_label = QLabel()
            if peak_icon:
                peak_label.setPixmap(peak_icon.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                peak_label.setAlignment(Qt.AlignCenter)
            elif peak_name == "[]":
                peak_label.setText("N/A")
                peak_label.setAlignment(Qt.AlignCenter)
            else:
                peak_label.setText(peak_name)
                peak_label.setAlignment(Qt.AlignCenter)

            # --- WL color coding ---
            try:
                wl_float = float(wl_value[:-1])
                if wl_float < 47:
                    wl.setForeground(QBrush(QColor("red")))
                elif wl_float < 53:
                    wl.setForeground(QBrush(QColor("gold")))
                elif wl_float < 60:
                    wl.setForeground(QBrush(QColor("limegreen")))
                else:
                    wl.setForeground(QBrush(QColor("cyan")))
            except ValueError:
                pass  # e.g. "N/A"

            # --- ACS color coding ---
            try:
                acs_float = float(acs_value)
                if acs_float < 200:
                    acs.setForeground(QBrush(QColor("red")))
                elif acs_float < 225:
                    acs.setForeground(QBrush(QColor("gold")))
                elif acs_float < 250:
                    acs.setForeground(QBrush(QColor("limegreen")))
                else:
                    acs.setForeground(QBrush(QColor("cyan")))
            except ValueError:
                pass  # e.g. "N/A"

            # --- KD color coding ---
            try:
                kd_float = float(kd_value)
                if kd_float < 0.9:
                    kd.setForeground(QBrush(QColor("red")))
                elif kd_float < 1.1:
                    kd.setForeground(QBrush(QColor("gold")))
                elif kd_float < 1.25:
                    kd.setForeground(QBrush(QColor("limegreen")))
                else:
                    kd.setForeground(QBrush(QColor("cyan")))
            except ValueError:
                pass  # e.g. "N/A"

            # --- HS color coding ---
            try:
                hs_float = float(hs_value)
                if hs_float < 20:
                    hs.setForeground(QBrush(QColor("red")))
                elif hs_float < 30:
                    hs.setForeground(QBrush(QColor("gold")))
                elif hs_float < 40:
                    hs.setForeground(QBrush(QColor("limegreen")))
                else:
                    hs.setForeground(QBrush(QColor("cyan")))
            except ValueError:
                pass # e.g. "N/A"


            # --- Rank colour coding ---
#            for key, color in RANK_COLOURS.items():
#                 if key.lower() in rank_value.lower():
#                    rank.setForeground(QBrush(QColor(color)))
#                    break

            # --- Peak rank colour coding ---
#            for key, color in RANK_COLOURS.items():
#                if key.lower() in peak_value.lower():
#                    peak.setForeground(QBrush(QColor(color)))
#                    break

            for col, item in enumerate([name, None, level, matches, wl, acs, kd, hs, None, rr, None, peak_act]):
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row, col, item)

            table.setCellWidget(row, 1, agent_label)
            table.setCellWidget(row, 8, rank_label)
            table.setCellWidget(row, 10, peak_label)

        table.resizeColumnsToContents()


# ---------------------------------------------------------
# Async entry point for qasync
# ---------------------------------------------------------
async def main():
    window = ValorantStatsWindow([])
    window.show()

    # Start fetching data asynchronously
    asyncio.create_task(window.refresh_data())

    return window  # Keep a reference so it doesn't get garbage-collected


if __name__ == "__main__":
    from PySide6 import QtCore
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logoone.png")))
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Start async app
    window = loop.run_until_complete(main())
    with loop:
        loop.run_forever()