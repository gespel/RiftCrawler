import json
import os
from tqdm import tqdm
import psycopg2
from psycopg2.extras import execute_values, Json
from datetime import datetime, timezone

# --- DB Config & Tabellen ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 30432,
    "dbname": "lol",
    "user": "loluser",
    "password": "secret",
}

TABLES = {
    "summoners": """
        CREATE TABLE summoners (
            puuid TEXT PRIMARY KEY,
            summoner_id TEXT,
            summoner_name TEXT,
            riot_id_game_name TEXT,
            riot_id_tagline TEXT,
            summoner_level INTEGER,
            profile_icon INTEGER,
            last_seen TIMESTAMPTZ
        );
    """,
    "matches": """
        CREATE TABLE matches (
            game_id BIGINT PRIMARY KEY,
            match_id TEXT UNIQUE NOT NULL,
            data_version TEXT,
            game_creation TIMESTAMPTZ,
            game_start TIMESTAMPTZ,
            game_end TIMESTAMPTZ,
            game_duration INTEGER,
            game_mode TEXT,
            game_name TEXT,
            game_type TEXT,
            game_version TEXT,
            map_id INTEGER,
            platform_id TEXT,
            queue_id INTEGER,
            tournament_code TEXT,
            end_of_game_result TEXT,
            raw_info JSONB NOT NULL
        );
    """,
    "teams": """
        CREATE TABLE teams (
            id BIGSERIAL PRIMARY KEY,
            game_id BIGINT REFERENCES matches(game_id) ON DELETE CASCADE,
            team_id INTEGER,
            win BOOLEAN,
            bans JSONB,
            objectives JSONB,
            feats JSONB,
            UNIQUE (game_id, team_id)
        );
    """,
    "participants": """
        CREATE TABLE participants (
            id BIGSERIAL PRIMARY KEY,
            game_id BIGINT REFERENCES matches(game_id) ON DELETE CASCADE,
            participant_id INTEGER,
            puuid TEXT REFERENCES summoners(puuid),
            summoner_id TEXT,
            summoner_name TEXT,
            summoner_level INTEGER,
            riot_id_game_name TEXT,
            riot_id_tagline TEXT,
            profile_icon INTEGER,

            champion_id INTEGER,
            champion_name TEXT,
            champ_level INTEGER,
            champ_experience INTEGER,

            team_id INTEGER,
            team_position TEXT,
            individual_position TEXT,
            role TEXT,
            lane TEXT,
            win BOOLEAN,

            -- combat
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            killing_sprees INTEGER,
            largest_killing_spree INTEGER,
            largest_multi_kill INTEGER,
            double_kills INTEGER,
            triple_kills INTEGER,
            quadra_kills INTEGER,
            penta_kills INTEGER,
            first_blood_kill BOOLEAN,
            first_blood_assist BOOLEAN,

            -- damage
            total_damage_dealt INTEGER,
            total_damage_dealt_to_champions INTEGER,
            physical_damage_dealt_to_champions INTEGER,
            magic_damage_dealt_to_champions INTEGER,
            true_damage_dealt_to_champions INTEGER,
            total_damage_taken INTEGER,
            damage_self_mitigated INTEGER,
            damage_dealt_to_objectives INTEGER,
            damage_dealt_to_buildings INTEGER,
            damage_dealt_to_turrets INTEGER,
            largest_critical_strike INTEGER,

            -- economy
            gold_earned INTEGER,
            gold_spent INTEGER,
            total_minions_killed INTEGER,
            neutral_minions_killed INTEGER,
            items_purchased INTEGER,
            item0 INTEGER,
            item1 INTEGER,
            item2 INTEGER,
            item3 INTEGER,
            item4 INTEGER,
            item5 INTEGER,
            item6 INTEGER,

            -- objectives
            turret_kills INTEGER,
            turret_takedowns INTEGER,
            turrets_lost INTEGER,
            inhibitor_kills INTEGER,
            inhibitor_takedowns INTEGER,
            inhibitors_lost INTEGER,
            dragon_kills INTEGER,
            baron_kills INTEGER,
            objectives_stolen INTEGER,
            objectives_stolen_assists INTEGER,

            -- vision
            vision_score INTEGER,
            wards_placed INTEGER,
            wards_killed INTEGER,
            detector_wards_placed INTEGER,
            vision_wards_bought_in_game INTEGER,

            -- misc
            total_heal INTEGER,
            total_heals_on_teammates INTEGER,
            time_ccing_others INTEGER,
            total_time_cc_dealt INTEGER,
            longest_time_spent_living INTEGER,
            total_time_spent_dead INTEGER,
            time_played INTEGER,
            summoner1_id INTEGER,
            summoner2_id INTEGER,
            game_ended_in_surrender BOOLEAN,
            game_ended_in_early_surrender BOOLEAN,

            challenges JSONB,
            perks JSONB,
            raw_participant JSONB NOT NULL,

            UNIQUE (game_id, participant_id)
        );
    """,
}

def table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        );
        """,
        (table_name,),
    )
    return cursor.fetchone()[0]

def create_tables():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # Reihenfolge wegen Foreign Keys: summoners/matches -> teams/participants
            for table_name in ("summoners", "matches", "teams", "participants"):
                ddl = TABLES[table_name]
                if table_exists(cur, table_name):
                    print(f"Table '{table_name}' already exists – skipping.")
                else:
                    print(f"Creating table '{table_name}'...")
                    cur.execute(ddl)
    print("Done.")

# --- Hilfsfunktionen ---
def ms_to_ts(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

def insert_match(cur, game: dict) -> int | None:
    info = game.get("info", {})
    metadata = game.get("metadata", {})

    match_id = metadata.get("matchId")
    if not match_id:
        return None

    game_id = int(match_id.split("_")[1])

    cur.execute(
        """
        INSERT INTO matches (
            game_id, match_id, data_version,
            game_creation, game_start, game_end, game_duration,
            game_mode, game_name, game_type, game_version,
            map_id, platform_id, queue_id, tournament_code,
            end_of_game_result, raw_info
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (game_id) DO NOTHING;
        """,
        (
            game_id,
            match_id,
            metadata.get("dataVersion"),
            ms_to_ts(info.get("gameCreation")),
            ms_to_ts(info.get("gameStartTimestamp")),
            ms_to_ts(info.get("gameEndTimestamp")),
            info.get("gameDuration"),
            info.get("gameMode"),
            info.get("gameName"),
            info.get("gameType"),
            info.get("gameVersion"),
            info.get("mapId"),
            info.get("platformId"),
            info.get("queueId"),
            info.get("tournamentCode"),
            info.get("endOfGameResult"),
            Json(game),
        ),
    )
    return game_id

def insert_teams(cur, game_id: int, info: dict):
    teams = info.get("teams", [])
    rows = [
        (
            game_id,
            team.get("teamId"),
            team.get("win"),
            Json(team.get("bans")),
            Json(team.get("objectives")),
            Json(team.get("feats")),
        )
        for team in teams
    ]
    if rows:
        execute_values(
            cur,
            """
            INSERT INTO teams (game_id, team_id, win, bans, objectives, feats)
            VALUES %s
            ON CONFLICT (game_id, team_id) DO NOTHING;
            """,
            rows,
            page_size=50,
        )

def insert_summoners(cur, info: dict):
    participants = info.get("participants", [])
    game_creation = ms_to_ts(info.get("gameCreation"))
    rows = [
        (
            p.get("puuid"),
            p.get("summonerId"),
            p.get("summonerName"),
            p.get("riotIdGameName"),
            p.get("riotIdTagline"),
            p.get("summonerLevel"),
            p.get("profileIcon"),
            game_creation,
        )
        for p in participants
        if p.get("puuid")
    ]
    if rows:
        execute_values(
            cur,
            """
            INSERT INTO summoners (
                puuid, summoner_id, summoner_name, riot_id_game_name,
                riot_id_tagline, summoner_level, profile_icon, last_seen
            )
            VALUES %s
            ON CONFLICT (puuid) DO UPDATE SET
                summoner_id = EXCLUDED.summoner_id,
                summoner_name = EXCLUDED.summoner_name,
                riot_id_game_name = EXCLUDED.riot_id_game_name,
                riot_id_tagline = EXCLUDED.riot_id_tagline,
                summoner_level = EXCLUDED.summoner_level,
                profile_icon = EXCLUDED.profile_icon,
                last_seen = EXCLUDED.last_seen
            WHERE summoners.last_seen IS NULL
               OR EXCLUDED.last_seen IS NULL
               OR EXCLUDED.last_seen >= summoners.last_seen;
            """,
            rows,
            page_size=50,
        )

def insert_participants(cur, game_id: int, info: dict):
    participants = info.get("participants", [])
    rows = []

    for p in participants:
        rows.append(
            (
                game_id,
                p.get("participantId"),
                p.get("puuid"),
                p.get("summonerId"),
                p.get("summonerName"),
                p.get("summonerLevel"),
                p.get("riotIdGameName"),
                p.get("riotIdTagline"),
                p.get("profileIcon"),

                p.get("championId"),
                p.get("championName"),
                p.get("champLevel"),
                p.get("champExperience"),

                p.get("teamId"),
                p.get("teamPosition"),
                p.get("individualPosition"),
                p.get("role"),
                p.get("lane"),
                p.get("win"),

                p.get("kills"),
                p.get("deaths"),
                p.get("assists"),
                p.get("killingSprees"),
                p.get("largestKillingSpree"),
                p.get("largestMultiKill"),
                p.get("doubleKills"),
                p.get("tripleKills"),
                p.get("quadraKills"),
                p.get("pentaKills"),
                p.get("firstBloodKill"),
                p.get("firstBloodAssist"),

                p.get("totalDamageDealt"),
                p.get("totalDamageDealtToChampions"),
                p.get("physicalDamageDealtToChampions"),
                p.get("magicDamageDealtToChampions"),
                p.get("trueDamageDealtToChampions"),
                p.get("totalDamageTaken"),
                p.get("damageSelfMitigated"),
                p.get("damageDealtToObjectives"),
                p.get("damageDealtToBuildings"),
                p.get("damageDealtToTurrets"),
                p.get("largestCriticalStrike"),

                p.get("goldEarned"),
                p.get("goldSpent"),
                p.get("totalMinionsKilled"),
                p.get("neutralMinionsKilled"),
                p.get("itemsPurchased"),
                p.get("item0"),
                p.get("item1"),
                p.get("item2"),
                p.get("item3"),
                p.get("item4"),
                p.get("item5"),
                p.get("item6"),

                p.get("turretKills"),
                p.get("turretTakedowns"),
                p.get("turretsLost"),
                p.get("inhibitorKills"),
                p.get("inhibitorTakedowns"),
                p.get("inhibitorsLost"),
                p.get("dragonKills"),
                p.get("baronKills"),
                p.get("objectivesStolen"),
                p.get("objectivesStolenAssists"),

                p.get("visionScore"),
                p.get("wardsPlaced"),
                p.get("wardsKilled"),
                p.get("detectorWardsPlaced"),
                p.get("visionWardsBoughtInGame"),

                p.get("totalHeal"),
                p.get("totalHealsOnTeammates"),
                p.get("timeCCingOthers"),
                p.get("totalTimeCCDealt"),
                p.get("longestTimeSpentLiving"),
                p.get("totalTimeSpentDead"),
                p.get("timePlayed"),
                p.get("summoner1Id"),
                p.get("summoner2Id"),
                p.get("gameEndedInSurrender"),
                p.get("gameEndedInEarlySurrender"),

                Json(p.get("challenges")),
                Json(p.get("perks")),
                Json(p),
            )
        )

    if rows:
        execute_values(
            cur,
            """
            INSERT INTO participants (
                game_id, participant_id, puuid, summoner_id, summoner_name,
                summoner_level, riot_id_game_name, riot_id_tagline, profile_icon,
                champion_id, champion_name, champ_level, champ_experience,
                team_id, team_position, individual_position, role, lane, win,
                kills, deaths, assists, killing_sprees, largest_killing_spree,
                largest_multi_kill, double_kills, triple_kills, quadra_kills,
                penta_kills, first_blood_kill, first_blood_assist,
                total_damage_dealt, total_damage_dealt_to_champions,
                physical_damage_dealt_to_champions, magic_damage_dealt_to_champions,
                true_damage_dealt_to_champions, total_damage_taken,
                damage_self_mitigated, damage_dealt_to_objectives,
                damage_dealt_to_buildings, damage_dealt_to_turrets,
                largest_critical_strike,
                gold_earned, gold_spent, total_minions_killed, neutral_minions_killed,
                items_purchased, item0, item1, item2, item3, item4, item5, item6,
                turret_kills, turret_takedowns, turrets_lost,
                inhibitor_kills, inhibitor_takedowns, inhibitors_lost,
                dragon_kills, baron_kills, objectives_stolen, objectives_stolen_assists,
                vision_score, wards_placed, wards_killed, detector_wards_placed,
                vision_wards_bought_in_game,
                total_heal, total_heals_on_teammates, time_ccing_others,
                total_time_cc_dealt, longest_time_spent_living, total_time_spent_dead,
                time_played, summoner1_id, summoner2_id,
                game_ended_in_surrender, game_ended_in_early_surrender,
                challenges, perks, raw_participant
            )
            VALUES %s
            ON CONFLICT (game_id, participant_id) DO NOTHING;
            """,
            rows,
            page_size=50,
        )

def import_game(cur, game: dict):
    game_id = insert_match(cur, game)
    if game_id is None:
        return
    info = game.get("info", {})
    insert_summoners(cur, info)
    insert_teams(cur, game_id, info)
    insert_participants(cur, game_id, info)

# --- JSON Loader ---
def load_game(filename: str) -> dict:
    with open(filename, 'r') as f:
        return json.load(f)

def get_json_files(folder_path: str) -> list:
    """Get list of JSON files without loading them."""
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".json")
    ]

def process_game_batch(json_files: list, conn):
    """Process games in small batches to minimize memory usage."""
    with conn.cursor() as cur:
        for json_file in json_files:
            try:
                game = load_game(json_file)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                continue

            import_game(cur, game)
            del game

    conn.commit()

def import_games_to_db(games: list, conn):
    """Import a list of already-loaded games into PostgreSQL."""
    with conn.cursor() as cur:
        for game in tqdm(games, desc="Importing games"):
            import_game(cur, game)
    conn.commit()

def import_games_streaming(folder_path: str, conn, batch_size: int = 100):
    """Import games in small batches without loading all into memory."""
    json_files = get_json_files(folder_path)
    total_files = len(json_files)

    print(f"Found {total_files} games to import (streaming mode)...")

    for i in tqdm(range(0, total_files, batch_size), desc="Processing batches"):
        batch = json_files[i:i + batch_size]
        process_game_batch(batch, conn)

    print(f"Import complete.")

# --- MAIN ---
if __name__ == "__main__":
    create_tables()

    # Pfad zu deinen JSONs
    game_path = os.path.join(".", "crawler", "games", "classic")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        import_games_streaming(game_path, conn, batch_size=100)
    finally:
        conn.close()

    print("Import finished.")
