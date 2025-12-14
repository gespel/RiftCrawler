import json
import os
import math
from tqdm import tqdm

def plot_level_distribution(games: list):
    import matplotlib.pyplot as plt

    # Levels einsammeln
    levels = []
    for game in games:
        for participant in game.get("info", {}).get("participants", []):
            levels.append(participant.get("summonerLevel", 0))

    # Figur
    plt.figure(figsize=(16, 10))

    # Histogramm mit schöneren Styles
    plt.hist(
        levels,
        bins=range(1, max(levels) + 2),
        edgecolor="green",        # dünne Linien für klarere Balken
        alpha=0.75,               # etwas Transparenz
        linewidth=1.0
    )
    plt.locator_params(axis="x", nbins=40)
    # Titel und Achsen
    plt.title("Distribution of Account Levels", fontsize=20, pad=15)
    plt.xlabel("Level", fontsize=16)
    plt.ylabel("Number of Accounts", fontsize=16)

    # Schönes Grid
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    # Ticks lesbarer machen
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # Layout optimieren
    plt.tight_layout()

    plt.show()

def get_team_levels(game: dict) -> tuple:
    team1_levels = []
    team2_levels = []
    for participant in game.get("info").get("participants", []):
        if participant.get("teamId") == 100:
            team1_levels.append(participant.get("summonerLevel", 0))
        else:
            team2_levels.append(participant.get("summonerLevel", 0))
    return sum(team1_levels) / len(team1_levels), sum(team2_levels) / len(team2_levels)

def get_percentage_of_surrendered_games(games: dict) -> float:
    surrendered_games = 0
    for game in games:
        s = game.get("info").get("participants", [])[0]["gameEndedInSurrender"]
        es = game.get("info").get("participants", [])[0]["gameEndedInEarlySurrender"]
        if s == True or es == True:
            surrendered_games += 1
    return surrendered_games/len(games)

def get_team_champion_levels(game: dict) -> tuple:
    team1_levels = []
    team2_levels = []
    for participant in game.get("info").get("participants", []):
        if participant.get("teamId") == 100:
            team1_levels.append(participant.get("champExperience", 0))
        else:
            team2_levels.append(participant.get("champExperience", 0))
    return sum(team1_levels) / len(team1_levels), sum(team2_levels) / len(team2_levels)

def get_team_min_max_level(game: dict) -> tuple:
    team1_max_level = 0
    team1_min_level = math.inf
    team2_max_level = 0
    team2_min_level = math.inf

    for p in game.get("info").get("participants", []):
        if p.get("teamId") == 100:
            if p.get("summonerLevel", 0) > team1_max_level:
                team1_max_level = p.get("summonerLevel", 0)
            if p.get("summonerLevel", 0) < team1_min_level:
                team1_min_level = p.get("summonerLevel", 0)
        if p.get("teamId") == 200:
            if p.get("summonerLevel", 0) > team2_max_level:
                team2_max_level = p.get("summonerLevel", 0)
            if p.get("summonerLevel", 0) < team2_min_level:
                team2_min_level = p.get("summonerLevel", 0)
    return ((team1_min_level, team1_max_level), (team2_min_level, team2_max_level))

def higher_absolute_level_winrate(games:list, difference: float = 0.0) -> float:
    all_games = 0
    won_with_higher_max_level = 0
    won_with_lower_max_level = 0

    for game in games:
        l = get_team_min_max_level(game)
        team1_min_level, team1_max_level = l[0]
        team2_min_level, team2_max_level = l[1]
        team1_win = False
        team2_win = False

        p = game.get("info").get("participants", [])[0]
        if p["teamId"] == 100:
            team1_win = p["win"]
            team2_win = not team1_win
        elif p["teamId"] == 200:
            team2_win = p["win"]
            team1_win = not team2_win

        if team1_max_level > team2_max_level and abs(team1_max_level - team2_max_level) > difference:
            all_games += 1
            if team1_win:
                won_with_higher_max_level += 1
            if team2_win:
                won_with_lower_max_level += 1

        if team2_max_level > team1_max_level and abs(team1_max_level - team2_max_level) > difference:
            all_games += 1
            if team1_win:
                won_with_lower_max_level += 1
            if team2_win:
                won_with_higher_max_level += 1
    return won_with_higher_max_level/all_games

def higher_level_winrate(games: list, difference: float = 0.0) -> float:
    all_games = 0
    won_with_higher_level = 0
    won_with_lower_level = 0
    for game in games:
        team1_level, team2_level = get_team_levels(game)
        team1_win = False
        team2_win = False

        p = game.get("info").get("participants", [])[0]
        if p["teamId"] == 100:
            team1_win = p["win"]
            team2_win = not team1_win
        elif p["teamId"] == 200:
            team2_win = p["win"]
            team1_win = not team2_win

        if team1_level > team2_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team1_win:
                won_with_higher_level += 1
            if team2_win:
                won_with_lower_level += 1
        
        if team2_level > team1_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team2_win:
                won_with_higher_level += 1
            if team1_win:
                won_with_lower_level += 1
    #print(f"{won_with_higher_level} Wins with higher level and {won_with_lower_level} Wins with lower level of {all_games} games")
    if all_games > 0:
        return won_with_higher_level/all_games
    else:
        return 0
    
def higher_champion_level_winrate(games: list, difference: float = 0.0) -> float:
    all_games = 0
    won_with_higher_level = 0
    won_with_lower_level = 0
    for game in games:
        team1_level, team2_level = get_team_champion_levels(game)
        team1_win = False
        team2_win = False

        p = game.get("info").get("participants", [])[0]
        if p["teamId"] == 100:
            team1_win = p["win"]
            team2_win = not team1_win
        elif p["teamId"] == 200:
            team2_win = p["win"]
            team1_win = not team2_win
        if team1_win == team2_win == True:
            print("Error! It is impossible that both teams win")
            #exit(-1)
        if team1_level > team2_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team1_win:
                won_with_higher_level += 1
            if team2_win:
                won_with_lower_level += 1
        
        if team2_level > team1_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team2_win:
                won_with_higher_level += 1
            if team1_win:
                won_with_lower_level += 1
    print(f"{won_with_higher_level} Wins with higher champion level and {won_with_lower_level} Wins with lower champion level of {all_games} games")
    if all_games > 0:
        return won_with_higher_level/all_games
    else:
        return 0
    
def lower_level_winrate(games: list, difference: float = 0.0) -> float:
    all_games = 0
    won_with_higher_level = 0
    won_with_lower_level = 0
    for game in games:
        team1_level, team2_level = get_team_levels(game)
        team1_win = False
        team2_win = False

        p = game.get("info").get("participants", [])[0]
        if p["teamId"] == 100:
            team1_win = p["win"]
            team2_win = not team1_win
        elif p["teamId"] == 200:
            team2_win = p["win"]
            team1_win = not team2_win
        if team1_win == team2_win == True:
            print("Error! It is impossible that both teams win")
            #exit(-1)
        if team1_level > team2_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team1_win:
                won_with_higher_level += 1
            if team2_win:
                won_with_lower_level += 1
        
        if team2_level > team1_level and (abs(team1_level - team2_level) > difference):
            all_games += 1
            if team2_win:
                won_with_higher_level += 1
            if team1_win:
                won_with_lower_level += 1
    #print(f"{won_with_higher_level} Wins with higher level and {won_with_lower_level} Wins with lower level of {all_games} games")
    if all_games > 0:
        return won_with_lower_level/all_games
    else:
        return 0

def get_highest_level_player(games: list) -> tuple:
    highest_level = -1
    player_name = ""
    for game in games:
        for participant in game.get("info").get("participants", []):
            level = participant.get("summonerLevel", 0)
            if level > highest_level:
                highest_level = level
                player_name = participant.get("riotIdGameName") + " #" + participant.get("riotIdTagline")
    return player_name, highest_level

def get_all_participants(games: list) -> list:
    puuids = {}
    for game in tqdm(games):
        for participant in game.get("info").get("participants", []):
            puuids[participant.get("puuid")] = participant
    print(f"{len(puuids)} total number of players.")
    return puuids

def get_winratio_for_nr_kills(games: list, kills: int) -> float:
    wins = 0
    losses = 0
    for game in tqdm(games):
        for participant in game.get("info").get("participants", []):
            if participant.get("kills") == kills:
                if participant.get("win") == True:
                    wins += 1
                if participant.get("win") == False:
                    losses += 1
    return wins / (wins + losses)

def get_winratio_for_nr_kills_and_role(games: list, kills: int, team_position: str) -> float:
    wins = 0
    losses = 0
    for game in tqdm(games):
        for participant in game.get("info").get("participants", []):
            if (participant.get("kills") == kills) and (participant.get("role") == team_position):
                if participant.get("win") == True:
                    wins += 1
                if participant.get("win") == False:
                    losses += 1
    return wins / (wins + losses)
            
def get_all_gametypes(games: list):
    gametypes = []
    for game in tqdm(games): 
        game_type = game.get("info").get("gameType")
        if game_type not in gametypes:
            gametypes.append(game_type)
    return gametypes