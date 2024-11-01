import os
import sys
import json
import subprocess
import xbmc # type: ignore
import xbmcplugin # type: ignore
import xbmcgui # type: ignore
import xbmcaddon # type: ignore
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
    xbmc.log(f"Batocera Widget: Selected data directory type is {data_directory_type}", xbmc.LOGINFO)

    if data_directory_type == "0":  # Batocera
        rom_dir = "/userdata/roms"
    elif data_directory_type == "1":  # RetroPie
        rom_dir = "/home/pi/RetroPie/roms"
    elif data_directory_type == "2":  # Custom
        rom_dir = ADDON.getSetting("custom_rom_directory")
        xbmc.log(f"Batocera Widget: Retrieved custom ROM directory: {rom_dir}", xbmc.LOGINFO)

        # Prompt if custom ROM directory is empty
        if not rom_dir:
            rom_dir = xbmcgui.Dialog().browse(0, "Select Custom ROM Directory", "files")
            ADDON.setSetting("custom_rom_directory", rom_dir)  # Save the directory if selected

        # Verify if the selected directory is valid
        if not rom_dir or not os.path.isdir(rom_dir):
            xbmc.log("Batocera Widget: Custom ROM directory is invalid or not set.", xbmc.LOGERROR)
            xbmcgui.Dialog().notification("Batocera Widget", "Invalid Custom ROM Directory", xbmcgui.NOTIFICATION_ERROR)
            return None
    else:
        xbmc.log("Batocera Widget: Invalid ROM directory type selected.", xbmc.LOGERROR)
        return None

    xbmc.log(f"Batocera Widget: Using ROM directory: {rom_dir}", xbmc.LOGINFO)
    return rom_dir

def display_games(search_type):
    """Displays games based on the search type (favorites or latest)."""
    rom_directory = get_rom_directory()
    if not rom_directory:
        xbmc.log("Batocera Widget: ROM directory not set, exiting display_games function.", xbmc.LOGERROR)
        return

    platform_map = load_platform_map()
    games = process_gamelist_files(rom_directory, search_type, platform_map)
    xbmc.log(f"Batocera Widget: Found {len(games)} games to display.", xbmc.LOGINFO)

    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({"thumb": game.get("thumbnail", ""), "fanart": game.get("fanart", "")})

        rating = str(game.get("rating", "0.0"))
        rating_value = float(rating) if rating.replace('.', '', 1).isdigit() else 0.0

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

        url = f"plugin://script.batocera?action=run&rom_path={game['path']}" if "path" in game else ""
        if not url:
            xbmc.log(f"Batocera Widget: Missing ROM path for game: {game.get('name', 'Unknown')}", xbmc.LOGWARNING)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

def force_rescan_roms():
    """Forces a rescan of the ROMs directory."""
    xbmc.log("Batocera Widget: Forced rescan of ROMs directory initiated.", xbmc.LOGNOTICE)
    xbmcgui.Dialog().notification("Batocera Widget", "Rescanning ROMs directory...", xbmcgui.NOTIFICATION_INFO, 3000)

    display_games("0")  # Rescan and display favorites

    xbmc.log("Batocera Widget: ROMs rescan completed.", xbmc.LOGNOTICE)
    xbmcgui.Dialog().notification("Batocera Widget", "ROMs rescan completed.", xbmcgui.NOTIFICATION_INFO, 3000)

def main():
    """Main menu to choose between Favorites and Latest 25 Games."""
    # Directly initiate a rescan whenever force_rescan is clicked
    if ADDON.getSetting("force_rescan"):
        xbmc.log("Batocera Widget: Force rescan action triggered, initiating rescan.", xbmc.LOGINFO)
        force_rescan_roms()
        # Reset the force_rescan action
        ADDON.setSetting("force_rescan", "")

    # Main menu structure follows
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

    # Clean up the ROM path if needed
    rom_path = rom_path.replace("./", "")

    # Determine the command based on the selected run type
    if run_command_type == "1":  # Batocera
        run_command = "batocera-run"
    elif run_command_type == "2":  # RetroPie
        run_command = "emulationstation --run"
    elif run_command_type == "3":  # Custom
        run_command = ADDON.getSetting("custom_run_command")
    else:
        xbmc.log("No valid run command specified.", xbmc.LOGERROR)
        return

    # Construct and execute the full command
    try:
        command = f"{run_command} {rom_path}"
        xbmc.log(f"Launching game with command: {command}", xbmc.LOGINFO)
        subprocess.run(command, shell=True, check=True)
        xbmc.executebuiltin("Quit")  # Quit Kodi after launching the game
    except subprocess.CalledProcessError as e:
        xbmc.log(f"Failed to launch game: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Error", f"Failed to launch game: {e}", xbmcgui.NOTIFICATION_ERROR)

if __name__ == "__main__":
    paramstring = sys.argv[2][1:] if len(sys.argv) > 2 else ""
    router(paramstring)
