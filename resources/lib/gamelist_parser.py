import os
import xml.etree.ElementTree as ET
import xbmc  # Import xbmc for logging

def process_gamelist_files(search_directory, search_type):
    games = []

    for root, dirs, files in os.walk(search_directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]  # Modify dirs in place to skip hidden ones

        if 'gamelist.xml' in files:
            file_path = os.path.join(root, 'gamelist.xml')
            xbmc.log(f"Gamelist Parser: Parsing {file_path}", xbmc.LOGDEBUG)

            # Check if the file is empty
            if os.path.getsize(file_path) == 0:
                xbmc.log(f"Gamelist Parser: {file_path} is empty. Skipping.", xbmc.LOGWARNING)
                continue

            try:
                tree = ET.parse(file_path)
            except ET.ParseError as e:
                xbmc.log(f"Gamelist Parser: Error parsing {file_path} - {e}", xbmc.LOGERROR)
                continue  # Skip this file and move on

            gamelist_root = tree.getroot()

            for game in gamelist_root.findall("game"):
                # Only include games with a <favourite> tag if search_type is for favorites
                if search_type == "0" and game.find("favourite") is None:
                    continue

                game_data = {}

                # Extract name, thumbnail, and fanart path (if present)
                name_tag = game.find("name")
                thumbnail_tag = game.find("thumbnail")
                image_tag = game.find("image")

                game_data["name"] = name_tag.text if name_tag is not None else "Unknown Game"
                
                # Resolve thumbnail path to an absolute path based on the gamelist.xml location
                if thumbnail_tag is not None:
                    thumbnail_path = thumbnail_tag.text
                    if not os.path.isabs(thumbnail_path):
                        thumbnail_path = os.path.join(root, thumbnail_path)
                    game_data["thumbnail"] = thumbnail_path

                # Resolve fanart path based on the <image> tag if present
                if image_tag is not None:
                    fanart_path = image_tag.text
                    if not os.path.isabs(fanart_path):
                        fanart_path = os.path.join(root, fanart_path)
                    game_data["fanart"] = fanart_path

                games.append(game_data)

                # If we're only interested in the last 20 added games, stop after 20 entries
                if search_type == "1" and len(games) >= 20:
                    break

    return games
