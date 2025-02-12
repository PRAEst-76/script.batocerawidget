import os
import xml.etree.ElementTree as ET
import xbmc  # type: ignore  # For logging

def process_gamelist_files(search_directory, search_type, platform_map):
    """Parses gamelist.xml files efficiently and updates the database."""
    games = []
    xbmc.log(f"Gamelist Parser: Scanning directory {search_directory}", xbmc.LOGINFO)
    
    for root, dirs, files in os.walk(search_directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        if 'gamelist.xml' in files:
            file_path = os.path.join(root, 'gamelist.xml')
            xbmc.log(f"Gamelist Parser: Parsing {file_path}", xbmc.LOGINFO)

            if os.path.getsize(file_path) == 0:
                xbmc.log(f"Gamelist Parser: {file_path} is empty. Skipping.", xbmc.LOGWARNING)
                continue

            try:
                for event, elem in ET.iterparse(file_path, events=("end",)):
                    if elem.tag == "game":
                        game_data = parse_game_entry(elem, root, search_type, platform_map)
                        if game_data:
                            games.append(game_data)
                        elem.clear()
                xbmc.log(f"Gamelist Parser: Found {len(games)} games in {file_path}", xbmc.LOGINFO)
            except ET.ParseError as e:
                xbmc.log(f"Gamelist Parser: Error parsing {file_path} - {e}", xbmc.LOGERROR)
                continue
    
    games = sorted(games, key=lambda x: x.get("last_modified", 0), reverse=True)[:25]
    return games

def parse_game_entry(game, root, search_type, platform_map):
    """Parses a single <game> entry from gamelist.xml."""
    if search_type == "0":  # Favorites
        favorite_tag = game.find("favorite")
        if favorite_tag is None or favorite_tag.text.lower() != "true":
            xbmc.log(f"Skipping non-favorite game: {game.findtext('name', 'Unknown Game')}", xbmc.LOGINFO)
            return None
    
    game_data = {
        "name": game.findtext("name", "Unknown Game"),
        "description": game.findtext("desc", "No description available"),
        "rating": game.findtext("rating", "0.0"),
        "year": game.findtext("releasedate", "0000")[:4],
        "platform": get_platform_name(root, platform_map)
    }
    
    game_data["thumbnail"] = resolve_media_path(game.find("thumbnail"), root)
    game_data["fanart"] = resolve_media_path(game.find("fanart"), root) or resolve_media_path(game.find("image"), root)
    
    rom_path_tag = game.find("path")
    if rom_path_tag is not None and rom_path_tag.text:
        rom_path = os.path.join(root, rom_path_tag.text)
        if os.path.isfile(rom_path):
            game_data["path"] = rom_path
            game_data["last_modified"] = os.path.getmtime(rom_path)
        else:
            return None
    
    xbmc.log(f"Gamelist Parser: Added game {game_data['name']} ({game_data['path']})", xbmc.LOGINFO)
    return game_data

def get_platform_name(root, platform_map):
    """Determines platform name based on the folder name."""
    platform_folder = os.path.basename(root)
    return platform_map.get(platform_folder, "Unknown Platform")

def resolve_media_path(tag, root):
    """Resolves absolute media paths from gamelist.xml."""
    if tag is not None and tag.text:
        return os.path.join(root, tag.text) if not os.path.isabs(tag.text) else tag.text
    return None
