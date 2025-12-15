import json
import os
from tqdm import tqdm
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

# --- DB Config & Tabellen (wie bisher) ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 30432,
    "dbname": "lol",
    "user": "loluser",
    "password": "secret",
}

TABLES = {
    "matches": """
        CREATE TABLE matches (
            game_id BIGINT PRIMARY KEY,
            game_creation TIMESTAMPTZ,
            game_start TIMESTAMPTZ,
            game_end TIMESTAMPTZ,
            game_duration INTEGER,
            game_mode TEXT,
            game_type TEXT,
            game_version TEXT,
            map_id INTEGER,
            raw_info JSONB NOT NULL
        );
    """,
    "participants": """
        CREATE TABLE participants (
            id BIGSERIAL PRIMARY KEY,
            game_id BIGINT REFERENCES matches(game_id),
            participant_id INTEGER,
            puuid TEXT,
            summoner_name TEXT,
            champion_id INTEGER,
            champion_name TEXT,
            team_id INTEGER,
            team_position TEXT,
            individual_position TEXT,
            win BOOLEAN,
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            gold_earned INTEGER,
            champ_level INTEGER,
            total_damage_dealt INTEGER,
            total_damage_taken INTEGER,
            challenges JSONB,
            perks JSONB,
            raw_participant JSONB NOT NULL
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
            for table_name, ddl in TABLES.items():
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

def import_games_to_db(games: list, conn):
    """Import games and participants into PostgreSQL."""
    with conn.cursor() as cur:
        for game in tqdm(games, desc="Importing games"):
            info = game.get("info", {})
            metadata = game.get("metadata", {})

            match_id = metadata.get("matchId")
            if not match_id:
                continue

            game_id = int(match_id.split("_")[1])

            # --- MATCH INSERT ---
            cur.execute(
                """
                INSERT INTO matches (
                    game_id,
                    game_creation,
                    game_start,
                    game_end,
                    game_duration,
                    game_mode,
                    game_type,
                    game_version,
                    map_id,
                    raw_info
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (game_id) DO NOTHING;
                """,
                (
                    game_id,
                    ms_to_ts(info.get("gameCreation")),
                    ms_to_ts(info.get("gameStartTimestamp")),
                    ms_to_ts(info.get("gameEndTimestamp")),
                    info.get("gameDuration"),
                    info.get("gameMode"),
                    info.get("gameType"),
                    info.get("gameVersion"),
                    info.get("mapId"),
                    json.dumps(game),
                ),
            )

            # --- PARTICIPANTS ---
            participants = info.get("participants", [])
            rows = []

            for p in participants:
                rows.append(
                    (
                        game_id,
                        p.get("participantId"),
                        p.get("puuid"),
                        p.get("summonerName"),
                        p.get("championId"),
                        p.get("championName"),
                        p.get("teamId"),
                        p.get("teamPosition"),
                        p.get("individualPosition"),
                        p.get("win"),
                        p.get("kills"),
                        p.get("deaths"),
                        p.get("assists"),
                        p.get("goldEarned"),
                        p.get("champLevel"),
                        p.get("totalDamageDealtToChampions"),
                        p.get("totalDamageTaken"),
                        json.dumps(p.get("challenges")),
                        json.dumps(p.get("perks")),
                        json.dumps(p),
                    )
                )

            if rows:
                execute_values(
                    cur,
                    """
                    INSERT INTO participants (
                        game_id,
                        participant_id,
                        puuid,
                        summoner_name,
                        champion_id,
                        champion_name,
                        team_id,
                        team_position,
                        individual_position,
                        win,
                        kills,
                        deaths,
                        assists,
                        gold_earned,
                        champ_level,
                        total_damage_dealt,
                        total_damage_taken,
                        challenges,
                        perks,
                        raw_participant
                    )
                    VALUES %s
                    ON CONFLICT DO NOTHING;
                    """,
                    rows,
                    page_size=50,
                )

    conn.commit()

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

def process_game_batch(json_files: list, conn, batch_size: int = 50):
    """Process games in small batches to minimize memory usage."""
    with conn.cursor() as cur:
        for json_file in json_files:
            # Load one game at a time
            try:
                game = load_game(json_file)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                continue
            
            info = game.get("info", {})
            metadata = game.get("metadata", {})

            match_id = metadata.get("matchId")
            if not match_id:
                continue

            game_id = int(match_id.split("_")[1])

            # --- MATCH INSERT ---
            cur.execute(
                """
                INSERT INTO matches (
                    game_id,
                    game_creation,
                    game_start,
                    game_end,
                    game_duration,
                    game_mode,
                    game_type,
                    game_version,
                    map_id,
                    raw_info
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (game_id) DO NOTHING;
                """,
                (
                    game_id,
                    ms_to_ts(info.get("gameCreation")),
                    ms_to_ts(info.get("gameStartTimestamp")),
                    ms_to_ts(info.get("gameEndTimestamp")),
                    info.get("gameDuration"),
                    info.get("gameMode"),
                    info.get("gameType"),
                    info.get("gameVersion"),
                    info.get("mapId"),
                    json.dumps(game),
                ),
            )

            # --- PARTICIPANTS ---
            participants = info.get("participants", [])
            rows = []

            for p in participants:
                rows.append(
                    (
                        game_id,
                        p.get("participantId"),
                        p.get("puuid"),
                        p.get("summonerName"),
                        p.get("championId"),
                        p.get("championName"),
                        p.get("teamId"),
                        p.get("teamPosition"),
                        p.get("individualPosition"),
                        p.get("win"),
                        p.get("kills"),
                        p.get("deaths"),
                        p.get("assists"),
                        p.get("goldEarned"),
                        p.get("champLevel"),
                        p.get("totalDamageDealtToChampions"),
                        p.get("totalDamageTaken"),
                        json.dumps(p.get("challenges")),
                        json.dumps(p.get("perks")),
                        json.dumps(p),
                    )
                )

            if rows:
                execute_values(
                    cur,
                    """
                    INSERT INTO participants (
                        game_id,
                        participant_id,
                        puuid,
                        summoner_name,
                        champion_id,
                        champion_name,
                        team_id,
                        team_position,
                        individual_position,
                        win,
                        kills,
                        deaths,
                        assists,
                        gold_earned,
                        champ_level,
                        total_damage_dealt,
                        total_damage_taken,
                        challenges,
                        perks,
                        raw_participant
                    )
                    VALUES %s
                    ON CONFLICT DO NOTHING;
                    """,
                    rows,
                    page_size=50,
                )
            
            # Free memory immediately
            del game, info, metadata, participants, rows
    
    conn.commit()

def import_games_streaming(folder_path: str, conn, batch_size: int = 100):
    """Import games in small batches without loading all into memory."""
    json_files = get_json_files(folder_path)
    total_files = len(json_files)
    
    print(f"Found {total_files} games to import (streaming mode)...")
    
    # Process in small batches
    for i in tqdm(range(0, total_files, batch_size), desc="Processing batches"):
        batch = json_files[i:i + batch_size]
        process_game_batch(batch, conn, batch_size)
    
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
