import os
import sys
import json
import subprocess
import xbmc  # type: ignore
import xbmcplugin  # type: ignore
import xbmcgui  # type: ignore
import xbmcaddon  # type: ignore
from urllib.parse import quote
from resources.lib.gamelist_parser import process_gamelist_files

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])

def load_platform_map():
    """Load platform mappings from platform_map.json with UTF-8 encoding."""
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
    if data_directory_type == "0":
        rom_dir = "/userdata/roms"
    elif data_directory_type == "1":
        rom_dir = "/home/pi/RetroPie/roms"
    elif data_directory_type == "2":
        rom_dir = ADDON.getSetting("custom_rom_directory")
        if not rom_dir:
            rom_dir = xbmcgui.Dialog().browse(0, "Select Custom ROM Directory", "files")
            ADDON.setSetting("custom_rom_directory", rom_dir)
        if not rom_dir or not os.path.isdir(rom_dir):
            xbmcgui.Dialog().notification("Batocera Widget", "Invalid Custom ROM Directory", xbmcgui.NOTIFICATION_ERROR)
            return None
    else:
        return None
    return rom_dir

def get_wheel_image(rom_path):
    """Retrieve the wheel image path for a given ROM."""
    wheel_path = os.path.join(os.path.dirname(rom_path), "wheel", os.path.basename(rom_path) + ".png")
    return wheel_path if os.path.exists(wheel_path) else ""

def display_games(search_type):
    """Displays games based on the search type (favorites or latest)."""
    if search_type not in ["0", "1"]:
        return
    rom_directory = get_rom_directory()
    if not rom_directory:
        return
    platform_map = load_platform_map()
    games = process_gamelist_files(rom_directory, search_type, platform_map)
    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        cover_image = game.get("thumbnail", "")
        wheel_image = get_wheel_image(game["path"])
        list_item.setArt({
            "poster": cover_image,
            "clearart": wheel_image,
            "fanart": game.get("fanart", ""),
            "thumb": cover_image
        })
        rating_str = game.get("rating", "0.0").strip()
        rating_value = float(rating_str) if rating_str.replace('.', '', 1).isdigit() else 0.0
        list_item.setInfo("video", {
            "title": game.get("name", "Unknown Game"),
            "plot": game.get("description", "No description available"),
            "year": int(game["year"]) if game.get("year", "").isdigit() else None,
            "rating": rating_value,
            "genre": game.get("genre", "Unknown Genre"),
            "director": game.get("developer", "Unknown Developer"),
            "tagline": game.get("platform", "Unknown Platform")
        })
        url = f"plugin://script.batocera?action=run&rom_path={quote(game['path'])}" if "path" in game else ""
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def launch_game(rom_path):
    """Launch the selected game and exit Kodi."""
    run_command_type = ADDON.getSetting("run_command_type")
    run_command = "batocera-run" if run_command_type == "1" else "emulationstation --run" if run_command_type == "2" else ADDON.getSetting("custom_run_command")
    try:
        subprocess.run(f"{run_command} {rom_path}", shell=True, check=True)
        xbmc.executebuiltin("Quit")
    except subprocess.CalledProcessError as e:
        xbmcgui.Dialog().notification("Error", f"Failed to launch game: {e}", xbmcgui.NOTIFICATION_ERROR)

def router(paramstring):
    params = dict(arg.split("=") for arg in paramstring.split("&") if "=" in arg)
    action = params.get("action")
    if action == "favorites":
        display_games("0")
    elif action == "latest":
        display_games("1")
    elif action == "run" and "rom_path" in params:
        launch_game(params["rom_path"])
    else:
        main()

def main():
    """Main menu for selecting game categories."""
    xbmcplugin.setPluginCategory(HANDLE, "Batocera Games")
    xbmcplugin.setContent(HANDLE, "video games")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url="plugin://script.batocera/?action=favorites", listitem=xbmcgui.ListItem(label="Favorites"), isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url="plugin://script.batocera/?action=latest", listitem=xbmcgui.ListItem(label="Latest 25 Games"), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    router(sys.argv[2][1:] if len(sys.argv) > 2 else "")
