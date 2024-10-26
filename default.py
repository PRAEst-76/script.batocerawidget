import sys
import xbmc
import xbmcplugin
import xbmcgui
import subprocess
import os
from resources.lib.gamelist_parser import process_gamelist_files

ROM_DIRECTORY = "/home/praest76/Games/roms"
SEARCH_TYPE = "0"  # Fixed to search only for favorites

HANDLE = int(sys.argv[1])

def launch_game(rom_path):
    """Launch the selected game using Batocera's command-line tools."""
    try:
        # Construct the command to launch the game in Batocera
        command = ["batocera", "run", rom_path]
        subprocess.run(command, check=True)
    except Exception as e:
        xbmc.log(f"Failed to launch game: {e}", xbmc.LOGERROR)

def main():
    games = process_gamelist_files(ROM_DIRECTORY, SEARCH_TYPE)

    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({"thumb": game["thumbnail"], "fanart": game["fanart"]})

        # Set additional metadata
        list_item.setInfo("video", {
            "title": game["name"],
            "plot": game["description"],
            "year": int(game["year"]) if game["year"].isdigit() else 0,
            "rating": float(game["rating"]) if game["rating"].replace('.', '', 1).isdigit() else 0.0,
        })

        # Set the game path as a property for later retrieval
        list_item.setProperty("rom_path", game["path"])

        # Add each game to the Kodi directory for the widget, triggering run when clicked
        url = f"plugin://script.batocera?action=run&rom_path={game['path']}"
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

def router(paramstring):
    """Router function to handle plugin URL."""
    params = dict(arg.split("=") for arg in paramstring.split("&"))
    if params.get("action") == "run" and "rom_path" in params:
        launch_game(params["rom_path"])
    else:
        main()

if __name__ == "__main__":
    router(sys.argv[2][1:])
