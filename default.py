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

        # Use InfoTagVideo to set year and rating specifically for video-type info
        info_tag = list_item.getVideoInfoTag()
        info_tag.setTitle(game["name"])
        info_tag.setPlot(game["description"])
        
        # Set year and rating, making sure they are converted to appropriate types
        if game["year"].isdigit():
            info_tag.setYear(int(game["year"]))
        if game["rating"].replace('.', '', 1).isdigit():
            info_tag.setRating(float(game["rating"]))

        # Add each game to the Kodi directory for the widget
        xbmcplugin.addDirectoryItem(handle=HANDLE, url="", listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    main()
