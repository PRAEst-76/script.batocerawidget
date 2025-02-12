import os
import sys
import json
import sqlite3
import subprocess
import xbmc  # type: ignore
import xbmcplugin  # type: ignore
import xbmcgui  # type: ignore
import xbmcaddon  # type: ignore
from urllib.parse import quote, parse_qs
from resources.lib.gamelist_parser import process_gamelist_files

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
DB_PATH = os.path.join(ADDON.getAddonInfo("path"), "batocera_cache.db")

def init_db():
    """Initialize SQLite database and ensure the 'games' table exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                        name TEXT, path TEXT PRIMARY KEY, thumbnail TEXT, wheel TEXT, fanart TEXT,
                        rating REAL, description TEXT, year INTEGER, genre TEXT, developer TEXT, platform TEXT,
                        last_modified INTEGER, search_type TEXT)''')
    conn.commit()
    conn.close()

def load_platform_map():
    """Load platform mappings from platform_map.json."""
    platform_map_path = os.path.join(ADDON.getAddonInfo("path"), "resources", "platform_map.json")
    try:
        with open(platform_map_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        xbmc.log(f"Error loading platform map: {e}", xbmc.LOGERROR)
        return {}

def get_rom_directory():
    """Get the ROM directory based on the selected data directory type."""
    data_directory_type = ADDON.getSetting("data_directory_type")
    
    if data_directory_type == "0":  # Batocera
        return "/userdata/roms"
    elif data_directory_type == "1":  # RetroPie
        return "/home/pi/RetroPie/roms"
    elif data_directory_type == "2":  # Custom
        custom_path = ADDON.getSetting("custom_rom_directory")
        if not custom_path:
            custom_path = xbmcgui.Dialog().browse(0, "Select Custom ROM Directory", "files")
            ADDON.setSetting("custom_rom_directory", custom_path)
        return custom_path
    return None

def update_rom_directory():
    """Ensure the ROM directory updates when changing the gamelist source."""
    data_directory_type = ADDON.getSetting("data_directory_type")
    if data_directory_type == "0":  # Batocera
        ADDON.setSetting("custom_rom_directory", "/userdata/roms")
    elif data_directory_type == "1":  # RetroPie
        ADDON.setSetting("custom_rom_directory", "/home/pi/RetroPie/roms")

def display_games(search_type):
    """Displays games based on the search type (favorites or latest)."""
    rom_directory = get_rom_directory()
    if not rom_directory:
        xbmc.log("Batocera Widget: ROM directory is not set.", xbmc.LOGERROR)
        return
    xbmc.log(f"Batocera Widget: Using ROM directory {rom_directory}", xbmc.LOGINFO)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_type == "1":  # Latest games should be sorted by last modified timestamp
        cursor.execute("SELECT name, path, last_modified FROM games ORDER BY last_modified DESC LIMIT 25")
        xbmc.log(f"Batocera Widget: Latest 25 Games (by last_modified): {cursor.fetchall()}", xbmc.LOGINFO)
    elif search_type == "0":  # Favorites should be filtered
        cursor.execute("SELECT name, path FROM games WHERE search_type = ?", (search_type,))
        xbmc.log(f"Batocera Widget: Favorite Games: {cursor.fetchall()}", xbmc.LOGINFO)
    
    games = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    
    xbmc.log(f"Batocera Widget: Retrieved {len(games)} games from database for search_type {search_type}", xbmc.LOGINFO)
    
    if not games:
        platform_map = load_platform_map()
        games = process_gamelist_files(rom_directory, search_type, platform_map)
        xbmc.log(f"Batocera Widget: Retrieved {len(games)} games from XML after processing", xbmc.LOGINFO)
    
    if games:
        xbmc.log(f"Batocera Widget: First game entry -> {games[0]}", xbmc.LOGINFO)
    
    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({
            "poster": game.get("thumbnail", ""),
            "clearart": game.get("wheel", ""),
            "fanart": game.get("fanart", ""),
            "thumb": game.get("thumbnail", "")
        })
        info_tag = list_item.getVideoInfoTag()
        info_tag.setTitle(game["name"])
        info_tag.setPlot(game.get("description", "No description available"))
        info_tag.setYear(int(game.get("year", "0")) if str(game.get("year", "0")).isdigit() else 0)
        info_tag.setRating(float(game.get("rating", 0.0)) if str(game.get("rating", "0.0")).replace('.', '', 1).isdigit() else 0.0)
        info_tag.setGenres([game.get("genre", "Unknown Genre")])
        info_tag.setDirectors([game.get("developer", "Unknown Developer")])
        info_tag.setTagLine(game.get("platform", "Unknown Platform"))
        
        url = f"plugin://script.batocera?action=run&rom_path={quote(game['path'])}"
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def router(paramstring):
    """Route plugin actions based on URL parameters."""
    params = parse_qs(paramstring)
    action = params.get("action", [None])[0]
    
    if action == "favorites":
        display_games("0")
    elif action == "latest":
        display_games("1")
    elif action == "run" and "rom_path" in params:
        launch_game(params["rom_path"][0])
    else:
        main()

def main():
    """Main menu to choose between Favorites and Latest 25 Games."""
    xbmcplugin.setPluginCategory(HANDLE, "Batocera Games")
    xbmcplugin.setContent(HANDLE, "videos")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url="plugin://script.batocera/?action=favorites", listitem=xbmcgui.ListItem(label="Favorites"), isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url="plugin://script.batocera/?action=latest", listitem=xbmcgui.ListItem(label="Latest 25 Games"), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    update_rom_directory()
    init_db()
    router(sys.argv[2][1:] if len(sys.argv) > 2 else "")
