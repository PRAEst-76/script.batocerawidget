import os
import xml.etree.ElementTree as ET
import xbmc  # type: ignore # Logging

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
                # Only include games with a <favorite> tag if search_type is for favorites
                if search_type == "0" and game.find("favorite") is None:
                    continue

                game_data = {}

                # Extract game details
                name_tag = game.find("name")
                thumbnail_tag = game.find("thumbnail")
                fanart_tag = game.find("fanart")  # Check for <fanart> tag
                image_tag = game.find("image")  # Fallback to <image> if <fanart> not found
                desc_tag = game.find("desc")
                rating_tag = game.find("rating")
                releasedate_tag = game.find("releasedate")

                game_data["name"] = name_tag.text if name_tag is not None else "Unknown Game"
                game_data["description"] = desc_tag.text if desc_tag is not None else "No description available"
                game_data["rating"] = rating_tag.text if rating_tag is not None else "Unrated"

                # Extract only the year from <releasedate> (first 4 characters)
                if releasedate_tag is not None and len(releasedate_tag.text) >= 4:
                    game_data["year"] = releasedate_tag.text[:4]
                else:
                    game_data["year"] = "Unknown"

                # Resolve thumbnail path to an absolute path based on the gamelist.xml location
                if thumbnail_tag is not None:
                    thumbnail_path = thumbnail_tag.text
                    if not os.path.isabs(thumbnail_path):
                        thumbnail_path = os.path.join(root, thumbnail_path)
                    game_data["thumbnail"] = thumbnail_path

                # Set fanart path based on <fanart> or fallback to <image>
                if fanart_tag is not None:
                    fanart_path = fanart_tag.text
                elif image_tag is not None:
                    fanart_path = image_tag.text
                else:
                    fanart_path = None  # No fanart available

                if fanart_path and not os.path.isabs(fanart_path):
                    fanart_path = os.path.join(root, fanart_path)
                game_data["fanart"] = fanart_path

                games.append(game_data)

                # If we're only interested in the last 20 added games, stop after 20 entries
                if search_type == "1" and len(games) >= 20:
                    break

    return games
