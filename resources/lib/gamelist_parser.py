import os
import xml.etree.ElementTree as ET
import xbmc  # type: ignore # Logging

def process_gamelist_files(search_directory, search_type):
    games = []

    for root, dirs, files in os.walk(search_directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

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
                continue

            gamelist_root = tree.getroot()

            for game in gamelist_root.findall("game"):
                if search_type == "0" and game.find("favorite") is None:
                    continue

                game_data = {}

                # Extract basic game details with checks
                name_tag = game.find("name")
                game_data["name"] = name_tag.text if name_tag is not None else "Unknown Game"

                desc_tag = game.find("desc")
                game_data["description"] = desc_tag.text if desc_tag is not None else "No description available"

                rating_tag = game.find("rating")
                game_data["rating"] = rating_tag.text if rating_tag is not None else "Unrated"

                releasedate_tag = game.find("releasedate")
                if releasedate_tag is not None and releasedate_tag.text and len(releasedate_tag.text) >= 4:
                    game_data["year"] = releasedate_tag.text[:4]
                else:
                    game_data["year"] = "Unknown"

                # Extract additional metadata fields
                genre_tag = game.find("genre")
                game_data["genre"] = genre_tag.text if genre_tag is not None else "Unknown Genre"

                developer_tag = game.find("developer")
                game_data["developer"] = developer_tag.text if developer_tag is not None else "Unknown Developer"

                platform_tag = game.find("platform")
                game_data["platform"] = platform_tag.text if platform_tag is not None else "Unknown Platform"

                # Resolve thumbnail path to an absolute path based on the gamelist.xml location
                thumbnail_tag = game.find("thumbnail")
                thumbnail_path = None
                if thumbnail_tag is not None and thumbnail_tag.text:
                    thumbnail_path = thumbnail_tag.text
                    if not os.path.isabs(thumbnail_path):
                        thumbnail_path = os.path.join(root, thumbnail_path)
                game_data["thumbnail"] = thumbnail_path

                # Resolve fanart path based on <fanart> or <image> as a fallback
                fanart_tag = game.find("fanart")
                image_tag = game.find("image")
                fanart_path = None
                if fanart_tag is not None and fanart_tag.text:
                    fanart_path = fanart_tag.text
                elif image_tag is not None and image_tag.text:
                    fanart_path = image_tag.text

                if fanart_path and not os.path.isabs(fanart_path):
                    fanart_path = os.path.join(root, fanart_path)
                game_data["fanart"] = fanart_path

                # Extract ROM path if available
                rom_path_tag = game.find("path")
                if rom_path_tag is not None and rom_path_tag.text:
                    rom_path = os.path.join(root, rom_path_tag.text)
                    if os.path.isfile(rom_path):
                        game_data["path"] = rom_path
                        if search_type == "1":
                            game_data["date_added"] = os.path.getmtime(rom_path)
                    else:
                        continue  # Skip if ROM file is missing

                games.append(game_data)

    if search_type == "1":
        games = sorted(games, key=lambda x: x.get("date_added", 0), reverse=True)[:25]

    return games
