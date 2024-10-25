import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import sys
from resources.lib.gamelist_parser import process_gamelist_files

ADDON = xbmcaddon.Addon()

# Check if handle is provided, otherwise default to a safe value
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else None

def main():
    directory = ADDON.getSetting("search_directory")
    search_type = ADDON.getSetting("search_type")  # 0 for Favorites, 1 for Last 20 Added

    if not directory:
        xbmcgui.Dialog().ok("Gamelist Parser", "Please set the directory to search in the addon settings.")
        return
    
    # Process files based on search type
    games = process_gamelist_files(directory, search_type)

    # If no handle is available, display as a dialog for testing purposes
    if HANDLE is None:
        xbmc.log("Gamelist Parser: Running without a handle; displaying as a dialog", xbmc.LOGINFO)
        game_names = [f"{game.get('name', 'Unknown Game')}" for game in games]
        dialog = xbmcgui.Dialog()
        dialog.select("Select a Game", game_names)
    else:
        # Generate and add items to Kodi widget
        for game in games:
            list_item = xbmcgui.ListItem(label=game.get("name", "Unknown Game"))
            thumbnail = game.get("thumbnail", "")

            list_item.setArt({"thumb": thumbnail, "icon": thumbnail})
            list_item.setInfo("video", {"title": game.get("name", "Unknown Game")})

            # Adding item to directory, last argument indicates it's not a folder
            xbmcplugin.addDirectoryItem(handle=HANDLE, url="", listitem=list_item, isFolder=False)

        # Signal end of directory items
        xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    main()
