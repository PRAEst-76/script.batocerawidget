import os
import sys
import json
import subprocess
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from resources.lib.gamelist_parser import process_gamelist_files

# Initialize add-on and settings
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

def display_games(search_type):
    """Displays games based on the search type (favorites or latest)."""
    rom_directory = ADDON.getSetting("rom_directory")
    platform_map = load_platform_map()
    games = process_gamelist_files(rom_directory, search_type, platform_map)

    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({"thumb": game.get("thumbnail", ""), "fanart": game.get("fanart", "")})

        # Ensure rating is a valid float and platform is set correctly
        rating = str(game.get("rating", "0.0"))
        rating_value = float(rating) if rating.replace('.', '', 1).isdigit() else 0.0

        # Set video information, including genre, director, and platform
        video_info = {
            "title": game.get("name", "Unknown Game"),
            "plot": game.get("description", "No description available"),
            "year": int(game["year"]) if game.get("year", "").isdigit() else None,
            "rating": rating_value,
            "genre": game.get("genre", "Unknown Genre"),
            "director": game.get("developer", "Unknown Developer"),
            "tagline": game.get("platform", "Unknown Platform")
        }
        list_item.setInfo("video", video_info)

        # Generate URL only if 'path' exists
        url = f"plugin://script.batocera?action=run&rom_path={game['path']}" if "path" in game else ""
        if not url:
            xbmc.log(f"Missing ROM path for game: {game.get('name', 'Unknown')}", xbmc.LOGWARNING)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

def main():
    """Main menu to choose between Favorites and Latest 25 Games."""
    xbmcplugin.setPluginCategory(HANDLE, "Batocera Games")
    xbmcplugin.setContent(HANDLE, "videos")

    # Add menu items for Favorites and Latest 25 Games
    favorites_item = xbmcgui.ListItem(label="Favorites")
    favorites_url = f"plugin://script.batocera/?action=favorites"
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=favorites_url, listitem=favorites_item, isFolder=True)

    latest_item = xbmcgui.ListItem(label="Latest 25 Games")
    latest_url = f"plugin://script.batocera/?action=latest"
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=latest_url, listitem=latest_item, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)

def router(paramstring):
    params = dict(arg.split("=") for arg in paramstring.split("&") if "=" in arg)
    action = params.get("action")

    if action == "favorites":
        display_games("0")  # Show favorites
    elif action == "latest":
        display_games("1")  # Show latest 25 games
    elif action == "run" and "rom_path" in params:
        launch_game(params["rom_path"])
    else:
        main()

def launch_game(rom_path):
    """Launch the selected game using the specified command, then quit Kodi."""
    run_command_type = ADDON.getSetting("run_command_type")
    if run_command_type == "0":  # None
        xbmcgui.Dialog().notification("Game Selected", "No run command set. Showing metadata only.")
        return

    # Determine the command based on the selected run type
    if run_command_type == "1":  # Batocera
        run_command = "batocera run"
    elif run_command_type == "2":  # RetroPie
        run_command = "emulationstation --run"
    elif run_command_type == "3":  # Custom
        run_command = ADDON.getSetting("custom_run_command")
    else:
        xbmc.log("No valid run command specified.", xbmc.LOGERROR)
        return

    # Construct the full command to run the game
    try:
        command = f"{run_command} {rom_path}"
        subprocess.run(command, shell=True, check=True)
        xbmc.executebuiltin("Quit")  # Quit Kodi after launching the game
    except Exception as e:
        xbmc.log(f"Failed to launch game: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Error", "Failed to launch game.", xbmcgui.NOTIFICATION_ERROR)

if __name__ == "__main__":
    paramstring = sys.argv[2][1:] if len(sys.argv) > 2 else ""
    router(paramstring)
