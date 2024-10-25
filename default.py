import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import sys
from resources.lib.gamelist_parser import process_gamelist_files

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1

def main():
    directory = ADDON.getSetting("search_directory")
    search_type = ADDON.getSetting("search_type")  # 0 for Favorites, 1 for Last 20 Added

    if not directory:
        xbmcgui.Dialog().ok("Gamelist Parser", "Please set the directory to search in the addon settings.")
        return

    # Process files based on search type
    games = process_gamelist_files(directory, search_type)

    if HANDLE == -1:
        xbmc.log("Gamelist Parser: Running without a valid handle; cannot add items to Kodi directory.", xbmc.LOGERROR)
        return

    # Generate and add items to Kodi directory for widget display
    for game in games:
        name = game.get("name", "Unknown Game")
        thumbnail = game.get("thumbnail", "")
        fanart = game.get("fanart", "")

        # Create ListItem for each game
        list_item = xbmcgui.ListItem(label=name)
        
        # Set artwork for thumbnail, icon, and fanart
        list_item.setArt({
            "thumb": thumbnail,
            "icon": thumbnail,
            "fanart": fanart
        })
        
        list_item.setInfo("program", {"title": name})

        # Use an empty URL (you could use a link to a file or details page if available)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url="", listitem=list_item, isFolder=False)

    # End directory items
    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    main()
