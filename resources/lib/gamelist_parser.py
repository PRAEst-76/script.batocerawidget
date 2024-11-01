import os
import xml.etree.ElementTree as ET
import xbmc  # type: ignore # For logging

def process_gamelist_files(search_directory, search_type, platform_map):
    games = []

    for root, dirs, files in os.walk(search_directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        if 'gamelist.xml' in files:
            file_path = os.path.join(root, 'gamelist.xml')
            xbmc.log(f"Gamelist Parser: Parsing {file_path}", xbmc.LOGDEBUG)

            # Skip empty files
            if os.path.getsize(file_path) == 0:
                xbmc.log(f"Gamelist Parser: {file_path} is empty. Skipping.", xbmc.LOGWARNING)
                continue

            # Parse the XML file
            try:
                tree = ET.parse(file_path)
            except ET.ParseError as e:
                xbmc.log(f"Gamelist Parser: Error parsing {file_path} - {e}", xbmc.LOGERROR)
                continue

            gamelist_root = tree.getroot()

            # Determine platform from the folder name
            platform_folder = os.path.basename(os.path.dirname(file_path))
            platform_name = platform_map.get(platform_folder, "Unknown Platform")

            # Process each game entry in the XML
            for game in gamelist_root.findall("game"):
                # Include only favorites if search_type is "favorites"
                if search_type == "0" and game.find("favorite") is None:
                    continue

                # Game metadata
                game_data = {
                    "name": game.findtext("name", "Unknown Game"),
                    "description": game.findtext("desc", "No description available"),
                    "rating": game.findtext("rating", "Unrated"),
                    "year": game.findtext("releasedate", "Unknown")[:4] if game.find("releasedate") is not None else "Unknown",
                    "platform": platform_name
                }

                # Resolve thumbnail path
                thumbnail_tag = game.find("thumbnail")
                if thumbnail_tag is not None and thumbnail_tag.text:
                    thumbnail_path = thumbnail_tag.text
                    if not os.path.isabs(thumbnail_path):
                        thumbnail_path = os.path.join(root, thumbnail_path)
                    game_data["thumbnail"] = thumbnail_path
                else:
                    game_data["thumbnail"] = None

                # Resolve fanart path, falling back to <image> if <fanart> is missing
                fanart_tag = game.find("fanart")
                image_tag = game.find("image")
                fanart_path = fanart_tag.text if fanart_tag is not None else image_tag.text if image_tag is not None else None
                if fanart_path and not os.path.isabs(fanart_path):
                    fanart_path = os.path.join(root, fanart_path)
                game_data["fanart"] = fanart_path

                # Resolve ROM path
                rom_path_tag = game.find("path")
                if rom_path_tag is not None and rom_path_tag.text:
                    rom_path = os.path.join(root, rom_path_tag.text)
                    if os.path.isfile(rom_path):
                        game_data["path"] = rom_path
                        # Add the modification date if search_type is "latest"
                        if search_type == "1":
                            game_data["date_added"] = os.path.getmtime(rom_path)
                    else:
                        continue  # Skip if ROM file is missing

                games.append(game_data)

    # If search_type is "latest," sort by modification date and limit to 25 games
    if search_type == "1":
        games = sorted(games, key=lambda x: x.get("date_added", 0), reverse=True)[:25]

    return games
