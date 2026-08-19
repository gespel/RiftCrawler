import math
import psycopg2

from database.importer import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def plot_level_distribution(conn):
    import matplotlib.pyplot as plt

    with conn.cursor() as cur:
        cur.execute("SELECT summoner_level FROM participants WHERE summoner_level IS NOT NULL;")
        levels = [row[0] for row in cur.fetchall()]

    plt.figure(figsize=(16, 10))
    plt.hist(
        levels,
        bins=range(1, max(levels) + 2),
        edgecolor="green",
        alpha=0.75,
        linewidth=1.0
    )
    plt.locator_params(axis="x", nbins=40)
    plt.title("Distribution of Account Levels", fontsize=20, pad=15)
    plt.xlabel("Level", fontsize=16)
    plt.ylabel("Number of Accounts", fontsize=16)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.show()

def get_team_levels(conn, game_id: int) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT team_id, AVG(summoner_level)
            FROM participants
            WHERE game_id = %s AND team_id IN (100, 200)
            GROUP BY team_id;
            """,
            (game_id,),
        )
        levels = dict(cur.fetchall())
    return levels.get(100, 0), levels.get(200, 0)

def get_percentage_of_surrendered_games(conn) -> float:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(DISTINCT game_id) FILTER (
                    WHERE game_ended_in_surrender OR game_ended_in_early_surrender
                ),
                COUNT(DISTINCT game_id)
            FROM participants;
            """
        )
        surrendered, total = cur.fetchone()
    return surrendered / total if total else 0.0

def get_team_champion_levels(conn, game_id: int) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT team_id, AVG(champ_experience)
            FROM participants
            WHERE game_id = %s AND team_id IN (100, 200)
            GROUP BY team_id;
            """,
            (game_id,),
        )
        levels = dict(cur.fetchall())
    return levels.get(100, 0), levels.get(200, 0)

def get_team_min_max_level(conn, game_id: int) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT team_id, MIN(summoner_level), MAX(summoner_level)
            FROM participants
            WHERE game_id = %s AND team_id IN (100, 200)
            GROUP BY team_id;
            """,
            (game_id,),
        )
        rows = {team_id: (min_l, max_l) for team_id, min_l, max_l in cur.fetchall()}
    return rows.get(100, (math.inf, 0)), rows.get(200, (math.inf, 0))

def _team_metric_winrate(conn, metric_sql: str, difference: float, want_lower: bool = False) -> float:
    query = f"""
        WITH team_stats AS (
            SELECT game_id, team_id, {metric_sql} AS metric, bool_or(win) AS team_win
            FROM participants
            WHERE team_id IN (100, 200)
            GROUP BY game_id, team_id
        ),
        paired AS (
            SELECT a.metric AS metric_a, a.team_win AS win_a,
                   b.metric AS metric_b, b.team_win AS win_b
            FROM team_stats a
            JOIN team_stats b ON a.game_id = b.game_id
            WHERE a.team_id = 100 AND b.team_id = 200
        )
        SELECT
            COUNT(*) FILTER (WHERE ABS(metric_a - metric_b) > %s) AS all_games,
            COUNT(*) FILTER (
                WHERE ABS(metric_a - metric_b) > %s
                  AND ((metric_a > metric_b AND win_a) OR (metric_b > metric_a AND win_b))
            ) AS won_higher,
            COUNT(*) FILTER (
                WHERE ABS(metric_a - metric_b) > %s
                  AND ((metric_a > metric_b AND win_b) OR (metric_b > metric_a AND win_a))
            ) AS won_lower
        FROM paired;
    """
    with conn.cursor() as cur:
        cur.execute(query, (difference, difference, difference))
        all_games, won_higher, won_lower = cur.fetchone()
    if not all_games:
        return 0.0
    return (won_lower if want_lower else won_higher) / all_games

def higher_absolute_level_winrate(conn, difference: float = 0.0) -> float:
    return _team_metric_winrate(conn, "MAX(summoner_level)", difference)

def higher_level_winrate(conn, difference: float = 0.0) -> float:
    return _team_metric_winrate(conn, "AVG(summoner_level)", difference)

def higher_champion_level_winrate(conn, difference: float = 0.0) -> float:
    return _team_metric_winrate(conn, "AVG(champ_experience)", difference)

def lower_level_winrate(conn, difference: float = 0.0) -> float:
    return _team_metric_winrate(conn, "AVG(summoner_level)", difference, want_lower=True)

def get_highest_level_player(conn) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT riot_id_game_name || ' #' || riot_id_tagline, summoner_level
            FROM participants
            WHERE summoner_level IS NOT NULL
            ORDER BY summoner_level DESC
            LIMIT 1;
            """
        )
        row = cur.fetchone()
    return row if row else ("", -1)

def get_all_participants(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT puuid, summoner_id, summoner_name, riot_id_game_name,
                   riot_id_tagline, summoner_level, profile_icon
            FROM summoners;
            """
        )
        columns = [desc[0] for desc in cur.description]
        puuids = {row[0]: dict(zip(columns, row)) for row in cur.fetchall()}
    print(f"{len(puuids)} total number of players.")
    return puuids

def get_winratio_for_nr_kills(conn, kills: int) -> float:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE win) AS wins,
                COUNT(*) FILTER (WHERE NOT win) AS losses
            FROM participants
            WHERE kills = %s;
            """,
            (kills,),
        )
        wins, losses = cur.fetchone()
    return wins / (wins + losses) if (wins + losses) > 0 else 0.0

def get_winratio_for_nr_kills_and_role(conn, kills: int, role: str, lane: str) -> float:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE win) AS wins,
                COUNT(*) FILTER (WHERE NOT win) AS losses
            FROM participants
            WHERE kills = %s AND role = %s AND lane = %s;
            """,
            (kills, role, lane),
        )
        wins, losses = cur.fetchone()
    return wins / (wins + losses) if (wins + losses) > 0 else 0.0

def get_all_gametypes(conn) -> list:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT game_type FROM matches;")
        return [row[0] for row in cur.fetchall()]

def get_champion_winrates(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                champion_name,
                COUNT(*) FILTER (WHERE win) AS wins,
                COUNT(*) FILTER (WHERE NOT win) AS losses
            FROM participants
            GROUP BY champion_name;
            """
        )
        return {champion_name: (wins, losses) for champion_name, wins, losses in cur.fetchall()}
