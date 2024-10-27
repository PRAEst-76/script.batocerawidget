import sys
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import os
from resources.lib.gamelist_parser import process_gamelist_files

ADDON = xbmcaddon.Addon()

# Settings from settings.xml
data_directory_type = ADDON.getSetting("data_directory_type")
rom_directory = ADDON.getSetting("rom_directory")

# Determine the ROM directory based on user selection
if data_directory_type == "0":  # Batocera
    rom_directory = "/userdata/roms"
elif data_directory_type == "1":  # RetroPie
    rom_directory = "/home/pi/RetroPie/roms"
elif data_directory_type == "2" and not rom_directory:  # Custom but unset
    xbmc.log("No ROM directory set; opening settings.", xbmc.LOGWARNING)
    ADDON.openSettings()  # Open settings to prompt the user for a path
    rom_directory = ADDON.getSetting("rom_directory")

# Validate that rom_directory has been set after settings prompt
if not rom_directory:
    xbmcgui.Dialog().ok("Batocera Widget", "Please set the ROM directory in the add-on settings.")
    sys.exit()

HANDLE = int(sys.argv[1])

def main():
    games = process_gamelist_files(rom_directory, "0")  # Only search for favorites

    for game in games:
        list_item = xbmcgui.ListItem(label=game["name"])
        list_item.setArt({"thumb": game["thumbnail"], "fanart": game["fanart"]})

        # Set metadata
        info_tag = list_item.getVideoInfoTag()
        info_tag.setTitle(game["name"])
        info_tag.setPlot(game["description"])
        if game["year"].isdigit():
            info_tag.setYear(int(game["year"]))
        if game["rating"].replace('.', '', 1).isdigit():
            info_tag.setRating(float(game["rating"]))

        xbmcplugin.addDirectoryItem(handle=HANDLE, url="", listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == "__main__":
    main()
