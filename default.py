import sys
import xbmc
import xbmcplugin
import xbmcgui
from resources.lib.gamelist_parser import process_gamelist_files

# Hardcoded path to ROM directory and setting search type to look for favorites
ROM_DIRECTORY = "/home/praest76/Games/roms"
SEARCH_TYPE = "0"  # Fixed to '0' to only search for favorites

HANDLE = int(sys.argv[1])

def main():
    games = process_gamelist_files(ROM_DIRECTORY, SEARCH_TYPE)

    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({"thumb": game["thumbnail"], "fanart": game["fanart"]})

        # Add info for both "video" and "music" to improve display chances
        info_labels = {
            "title": game["name"],
            "plot": game["description"],
            "year": int(game["year"]) if game["year"].isdigit() else 0,
            "rating": float(game["rating"]) if game["rating"].replace('.', '', 1).isdigit() else 0.0
        }
        list_item.setInfo("video", info_labels)
        list_item.setInfo("music", info_labels)  # Add as "music" for broader compatibility

        # Add each game to the Kodi directory for the widget
        xbmcplugin.addDirectoryItem(handle=HANDLE, url="", listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    main()
