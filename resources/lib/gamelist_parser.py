import os
import xml.etree.ElementTree as ET
import xbmc
from datetime import datetime

def load_xml(file_path):
    try:
        tree = ET.parse(file_path)
        return tree
    except ET.ParseError as e:
        xbmc.log(f"Error parsing XML file {file_path}: {e}", level=xbmc.LOGERROR)
        return None

def search_favorite_games(root):
    result = []
    for game in root.findall(".//game"):
        if game.find("favorite") is not None:
            game_info = get_game_info(game)
            result.append(game_info)
    return result

def search_last_20_added(root):
    result = []
    games = []
    for game in root.findall(".//game"):
        added_date_elem = game.find("added_date")
        if added_date_elem is not None:
            try:
                added_date = datetime.strptime(added_date_elem.text, "%Y-%m-%dT%H:%M:%S")
                game_info = get_game_info(game)
                game_info["added_date"] = added_date
                games.append(game_info)
            except ValueError:
                xbmc.log(f"Invalid date format in game: {game}", level=xbmc.LOGWARNING)

    # Sort by date and take the last 20
    games_sorted = sorted(games, key=lambda x: x["added_date"], reverse=True)[:20]
    result.extend(games_sorted)
    return result

def get_game_info(game):
    game_info = {}
    name_elem = game.find("name")
    if name_elem is not None:
        game_info["name"] = name_elem.text
    thumbnail_elem = game.find("thumbnail")
    if thumbnail_elem is not None:
        game_info["thumbnail"] = thumbnail_elem.text
    return game_info

def find_gamelist_files(directory):
    gamelist_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file == "gamelist.xml":
                gamelist_files.append(os.path.join(root, file))
    return gamelist_files

def process_gamelist_files(directory, search_type):
    games = []
    gamelist_files = find_gamelist_files(directory)
    for file_path in gamelist_files:
        tree = load_xml(file_path)
        if tree:
            root = tree.getroot()
            if search_type == "0":  # Favorites
                games.extend(search_favorite_games(root))
            elif search_type == "1":  # Last 20 Added
                games.extend(search_last_20_added(root))
    return games
