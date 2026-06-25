"""
KMU Campus Football - Database Layer  (v2 — LeagueRepublic Overhaul)
Handles all SQLite operations: teams, matches, players, match_events, news.
"""

import sqlite3
import os
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "kmu_sports.db")


def get_connection() -> sqlite3.Connection:
    """Return a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema migration helpers
# ---------------------------------------------------------------------------

def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True if a column already exists in a table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create/migrate all tables, then seed with mock data."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS teams (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL UNIQUE,
                played        INTEGER DEFAULT 0,
                wins          INTEGER DEFAULT 0,
                draws         INTEGER DEFAULT 0,
                losses        INTEGER DEFAULT 0,
                goals_for     INTEGER DEFAULT 0,
                goals_against INTEGER DEFAULT 0,
                goal_diff     INTEGER DEFAULT 0,
                points        INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS matches (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team_id    INTEGER NOT NULL REFERENCES teams(id),
                away_team_id    INTEGER NOT NULL REFERENCES teams(id),
                home_score      INTEGER DEFAULT 0,
                away_score      INTEGER DEFAULT 0,
                match_date      TEXT NOT NULL,
                status          TEXT DEFAULT 'upcoming',
                matchweek       INTEGER DEFAULT 1,
                venue           TEXT DEFAULT 'KMU Main Pitch',
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS players (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                team_id       INTEGER NOT NULL REFERENCES teams(id),
                position      TEXT DEFAULT 'Forward',
                goals         INTEGER DEFAULT 0,
                assists       INTEGER DEFAULT 0,
                yellow_cards  INTEGER DEFAULT 0,
                red_cards     INTEGER DEFAULT 0,
                appearances   INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS match_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id      INTEGER NOT NULL REFERENCES matches(id),
                player_id     INTEGER NOT NULL REFERENCES players(id),
                event_type    TEXT NOT NULL,
                match_minute  INTEGER NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS news (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                date_posted TEXT DEFAULT (date('now')),
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)

        # Non-destructive migration: add 'venue' to pre-existing matches tables
        if not _column_exists(conn, "matches", "venue"):
            conn.execute("ALTER TABLE matches ADD COLUMN venue TEXT DEFAULT 'KMU Main Pitch'")

    _seed_data()


def _seed_data() -> None:
    """Insert initial data only when the DB is empty."""
    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0] > 0:
            return  # Already seeded

        # ---- Teams ----
        teams = [
            ("Data Science FC",),
            ("Engineering United",),
            ("Business Stars",),
            ("Medical XI",),
            ("Law Rovers",),
            ("Agriculture Athletic",),
        ]
        conn.executemany("INSERT INTO teams (name) VALUES (?)", teams)

        team_id_map = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM teams").fetchall()
        }

        # ---- Players ----
        players = [
            # (name, team_name, position, goals, assists, yellow, red, apps)
            ("Misheck Mwape",     "Data Science FC",      "Forward",    5, 3, 1, 0, 6),
            ("Chanda Tembo",      "Engineering United",   "Forward",    4, 1, 0, 0, 5),
            ("Brian Mulenga",     "Business Stars",       "Midfielder", 3, 4, 2, 0, 6),
            ("Kelvin Phiri",      "Medical XI",           "Forward",    3, 2, 1, 0, 5),
            ("Moses Banda",       "Data Science FC",      "Midfielder", 2, 5, 0, 0, 6),
            ("Francis Lungu",     "Law Rovers",           "Defender",   1, 2, 3, 1, 4),
            ("Patrick Zulu",      "Agriculture Athletic", "Forward",    2, 1, 0, 0, 5),
            ("Emmanuel Chileshe", "Engineering United",   "Goalkeeper", 0, 0, 1, 0, 6),
            ("David Mutale",      "Business Stars",       "Forward",    2, 0, 2, 0, 4),
            ("Joseph Mwanza",     "Medical XI",           "Midfielder", 1, 3, 0, 0, 5),
        ]
        for name, team, pos, g, a, y, r, apps in players:
            conn.execute(
                """INSERT INTO players
                   (name, team_id, position, goals, assists, yellow_cards, red_cards, appearances)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, team_id_map[team], pos, g, a, y, r, apps),
            )

        player_id_map = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM players").fetchall()
        }

        venues = [
            "KMU Main Pitch", "Chinsali Complex", "Faculty Ground A",
            "KMU Main Pitch", "Chinsali Complex", "Faculty Ground B",
            "KMU Main Pitch", "Faculty Ground A",
        ]

        # ---- Finished matches ----
        finished_matches = [
            # (home, away, h_score, a_score, date, week, venue_idx)
            ("Data Science FC",      "Engineering United",   3, 1, "2026-05-01", 1, 0),
            ("Business Stars",       "Medical XI",           2, 2, "2026-05-01", 1, 1),
            ("Law Rovers",           "Agriculture Athletic", 1, 0, "2026-05-01", 1, 2),
            ("Engineering United",   "Business Stars",       0, 1, "2026-05-08", 2, 3),
            ("Medical XI",           "Data Science FC",      1, 2, "2026-05-08", 2, 4),
            ("Agriculture Athletic", "Law Rovers",           3, 3, "2026-05-08", 2, 5),
            ("Data Science FC",      "Business Stars",       2, 0, "2026-05-15", 3, 6),
            ("Engineering United",   "Medical XI",           1, 1, "2026-05-15", 3, 7),
        ]

        match_ids: dict[int, int] = {}   # index → db match_id
        for idx, (h, a, hs, as_, date, week, vi) in enumerate(finished_matches):
            h_id, a_id = team_id_map[h], team_id_map[a]
            cur = conn.execute(
                """INSERT INTO matches
                   (home_team_id, away_team_id, home_score, away_score,
                    match_date, status, matchweek, venue)
                   VALUES (?, ?, ?, ?, ?, 'finished', ?, ?)""",
                (h_id, a_id, hs, as_, date, week, venues[vi]),
            )
            match_ids[idx] = cur.lastrowid
            _apply_match_result_to_teams(conn, h_id, a_id, hs, as_)

        # ---- Seed match_events for first 3 finished matches ----
        seed_events = [
            # match_idx, player_name, event_type, minute
            (0, "Misheck Mwape",   "Goal",   14),
            (0, "Moses Banda",     "Assist", 14),
            (0, "Chanda Tembo",    "Goal",   39),
            (0, "Misheck Mwape",   "Goal",   67),
            (0, "Moses Banda",     "Assist", 67),
            (0, "Misheck Mwape",   "Goal",   78),
            (1, "Brian Mulenga",   "Goal",   22),
            (1, "Joseph Mwanza",   "Goal",   55),
            (1, "David Mutale",    "Goal",   71),
            (1, "Kelvin Phiri",    "Goal",   88),
            (2, "Francis Lungu",   "Goal",   45),
        ]
        for match_idx, pname, etype, minute in seed_events:
            conn.execute(
                """INSERT INTO match_events (match_id, player_id, event_type, match_minute)
                   VALUES (?, ?, ?, ?)""",
                (match_ids[match_idx], player_id_map[pname], etype, minute),
            )

        # ---- Upcoming matches ----
        upcoming_venues = [
            "Chinsali Complex", "KMU Main Pitch", "Faculty Ground A",
            "KMU Main Pitch",   "Faculty Ground B", "Chinsali Complex",
        ]
        upcoming_matches = [
            ("Law Rovers",           "Data Science FC",      "2026-06-28", 4),
            ("Agriculture Athletic", "Engineering United",   "2026-06-28", 4),
            ("Medical XI",           "Business Stars",       "2026-06-28", 4),
            ("Data Science FC",      "Agriculture Athletic", "2026-07-05", 5),
            ("Engineering United",   "Law Rovers",           "2026-07-05", 5),
            ("Business Stars",       "Medical XI",           "2026-07-12", 6),
        ]
        for i, (h, a, date, week) in enumerate(upcoming_matches):
            conn.execute(
                """INSERT INTO matches
                   (home_team_id, away_team_id, home_score, away_score,
                    match_date, status, matchweek, venue)
                   VALUES (?, ?, 0, 0, ?, 'upcoming', ?, ?)""",
                (team_id_map[h], team_id_map[a], date, week, upcoming_venues[i]),
            )

        # ---- Seed news articles ----
        news_articles = [
            (
                "🏆 Season 2025/26 Kicks Off with a Bang!",
                "The KMU Inter-Faculty Football League has officially launched its 2025/26 campaign. "
                "Six faculties will battle it out over six matchweeks for the coveted KMU Champions Trophy. "
                "Data Science FC opened the season with a dominant 3-1 victory over Engineering United at "
                "the KMU Main Pitch.",
                "2026-05-01",
            ),
            (
                "⚽ Misheck Mwape Named Player of Matchweek 1",
                "Data Science FC striker Misheck Mwape has been crowned the Player of Matchweek 1 after "
                "scoring two goals and providing an assist in his team's opener. The Clinical forward, "
                "who has been in blistering form, is already the early favourite for the Golden Boot award.",
                "2026-05-03",
            ),
            (
                "📅 Matchweek 2 Round-Up: Drama at Chinsali Complex",
                "Matchweek 2 produced thrilling action across all three venues. The standout result was "
                "Agriculture Athletic's 3-3 draw with Law Rovers in a seven-goal thriller at Chinsali "
                "Complex. Data Science FC maintained their perfect record with a 2-1 win over Medical XI.",
                "2026-05-09",
            ),
            (
                "🗓️ Matchweek 4 Fixtures Confirmed — June 28th",
                "The KMU Sports Directorate has confirmed all three Matchweek 4 fixtures scheduled for "
                "28 June 2026. Law Rovers host league leaders Data Science FC at Chinsali Complex in what "
                "promises to be the match of the round. All matches kick off at 14:00 hrs CAT.",
                "2026-06-20",
            ),
            (
                "🚨 Disciplinary Update: Francis Lungu Suspended",
                "Law Rovers defender Francis Lungu has received a one-match suspension following his "
                "red card in the MW2 clash. He will miss the upcoming fixture against Data Science FC. "
                "The KMU Disciplinary Committee confirmed the decision on Monday.",
                "2026-06-22",
            ),
        ]
        conn.executemany(
            "INSERT INTO news (title, content, date_posted) VALUES (?, ?, ?)",
            news_articles,
        )


# ---------------------------------------------------------------------------
# Internal team stats updater
# ---------------------------------------------------------------------------

def _apply_match_result_to_teams(
    conn: sqlite3.Connection,
    home_id: int,
    away_id: int,
    home_score: int,
    away_score: int,
) -> None:
    """Recalculate standings for both teams. Must be called inside an open conn."""
    if home_score > away_score:
        h_w, h_d, h_l, h_pts = 1, 0, 0, 3
        a_w, a_d, a_l, a_pts = 0, 0, 1, 0
    elif home_score < away_score:
        h_w, h_d, h_l, h_pts = 0, 0, 1, 0
        a_w, a_d, a_l, a_pts = 1, 0, 0, 3
    else:
        h_w, h_d, h_l, h_pts = 0, 1, 0, 1
        a_w, a_d, a_l, a_pts = 0, 1, 0, 1

    conn.execute(
        """UPDATE teams SET
               played        = played + 1,
               wins          = wins + ?,
               draws         = draws + ?,
               losses        = losses + ?,
               goals_for     = goals_for + ?,
               goals_against = goals_against + ?,
               goal_diff     = goal_diff + ? - ?,
               points        = points + ?
           WHERE id = ?""",
        (h_w, h_d, h_l, home_score, away_score, home_score, away_score, h_pts, home_id),
    )
    conn.execute(
        """UPDATE teams SET
               played        = played + 1,
               wins          = wins + ?,
               draws         = draws + ?,
               losses        = losses + ?,
               goals_for     = goals_for + ?,
               goals_against = goals_against + ?,
               goal_diff     = goal_diff + ? - ?,
               points        = points + ?
           WHERE id = ?""",
        (a_w, a_d, a_l, away_score, home_score, away_score, home_score, a_pts, away_id),
    )


# ---------------------------------------------------------------------------
# Match result (bulk final score)
# ---------------------------------------------------------------------------

def log_match_result(match_id: int, home_score: int, away_score: int) -> bool:
    """
    Atomically mark an upcoming match as finished and update standings.
    Returns True on success, False if not found or already finished.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM matches WHERE id = ? AND status = 'upcoming'", (match_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute(
                """UPDATE matches SET home_score = ?, away_score = ?, status = 'finished'
                   WHERE id = ?""",
                (home_score, away_score, match_id),
            )
            _apply_match_result_to_teams(conn, row["home_team_id"], row["away_team_id"],
                                          home_score, away_score)
        return True
    except sqlite3.Error:
        return False


# ---------------------------------------------------------------------------
# Live goal logger  ← NEW
# ---------------------------------------------------------------------------

def log_live_goal(
    match_id: int,
    scorer_id: int,
    assist_id: Optional[int],
    minute: int,
) -> tuple[bool, str]:
    """
    Atomic transaction that:
      1. Inserts a 'Goal' event for the scorer.
      2. Optionally inserts an 'Assist' event for the playmaker.
      3. Increments players.goals / players.assists.
      4. Increments the correct home_score or away_score on the match.

    Returns (success: bool, error_message: str).
    """
    try:
        with get_connection() as conn:
            match = conn.execute(
                """SELECT home_team_id, away_team_id, home_score, away_score, status
                   FROM matches WHERE id = ?""",
                (match_id,),
            ).fetchone()
            if not match:
                return False, "Match not found."
            if match["status"] == "finished":
                return False, "Match is already marked as finished."

            scorer = conn.execute(
                "SELECT team_id FROM players WHERE id = ?", (scorer_id,)
            ).fetchone()
            if not scorer:
                return False, "Scorer not found."

            scorer_team = scorer["team_id"]

            # Insert Goal event
            conn.execute(
                """INSERT INTO match_events (match_id, player_id, event_type, match_minute)
                   VALUES (?, ?, 'Goal', ?)""",
                (match_id, scorer_id, minute),
            )

            # Insert Assist event
            if assist_id and assist_id != scorer_id:
                conn.execute(
                    """INSERT INTO match_events (match_id, player_id, event_type, match_minute)
                       VALUES (?, ?, 'Assist', ?)""",
                    (match_id, assist_id, minute),
                )
                conn.execute(
                    "UPDATE players SET assists = assists + 1 WHERE id = ?", (assist_id,)
                )

            # Increment scorer's goal tally
            conn.execute(
                "UPDATE players SET goals = goals + 1 WHERE id = ?", (scorer_id,)
            )

            # Update match score: check which team the scorer belongs to
            if scorer_team == match["home_team_id"]:
                conn.execute(
                    "UPDATE matches SET home_score = home_score + 1 WHERE id = ?",
                    (match_id,),
                )
            else:
                conn.execute(
                    "UPDATE matches SET away_score = away_score + 1 WHERE id = ?",
                    (match_id,),
                )

        return True, ""
    except sqlite3.Error as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Timeline fetcher  ← NEW
# ---------------------------------------------------------------------------

def fetch_timeline_for_match(match_id: int) -> str:
    """
    Return a formatted goal timeline string for a match, e.g.:
      "⚽ Mwape (14'), ⚽ Banda (67')"
    Assist events are noted inline.
    """
    with get_connection() as conn:
        events = conn.execute(
            """SELECT me.event_type, me.match_minute, p.name
               FROM match_events me
               JOIN players p ON me.player_id = p.id
               WHERE me.match_id = ?
               ORDER BY me.match_minute ASC""",
            (match_id,),
        ).fetchall()

    if not events:
        return ""

    parts = []
    for e in events:
        shortname = _short_name(e["name"])
        if e["event_type"] == "Goal":
            parts.append(f"⚽ {shortname} ({e['match_minute']}')")
        elif e["event_type"] == "Assist":
            parts.append(f"🎯 {shortname} ({e['match_minute']}')")

    return "  ·  ".join(parts)


def _short_name(full: str) -> str:
    """Turn 'Misheck Mwape' → 'M. Mwape'."""
    parts = full.strip().split()
    if len(parts) == 1:
        return full
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


# ---------------------------------------------------------------------------
# News functions  ← NEW
# ---------------------------------------------------------------------------

def fetch_all_news() -> list[dict]:
    """Return all news articles sorted newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, content, date_posted FROM news ORDER BY date_posted DESC, id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def add_news_article(title: str, content: str) -> bool:
    """Insert a new campus news article."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO news (title, content) VALUES (?, ?)", (title, content)
            )
        return True
    except sqlite3.Error:
        return False


# ---------------------------------------------------------------------------
# Standard fetch functions
# ---------------------------------------------------------------------------

def fetch_standings() -> list[dict]:
    """Return league table sorted by Points DESC, GD DESC, GF DESC."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT name, played, wins, draws, losses,
                      goals_for, goals_against, goal_diff, points
               FROM teams
               ORDER BY points DESC, goal_diff DESC, goals_for DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_finished_matches() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT m.id, ht.name AS home_team, at.name AS away_team,
                      m.home_score, m.away_score, m.match_date, m.matchweek, m.venue
               FROM matches m
               JOIN teams ht ON m.home_team_id = ht.id
               JOIN teams at ON m.away_team_id = at.id
               WHERE m.status = 'finished'
               ORDER BY m.match_date DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_upcoming_matches() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT m.id, ht.name AS home_team, at.name AS away_team,
                      m.match_date, m.matchweek, m.venue,
                      m.home_score, m.away_score, m.status
               FROM matches m
               JOIN teams ht ON m.home_team_id = ht.id
               JOIN teams at ON m.away_team_id = at.id
               WHERE m.status = 'upcoming'
               ORDER BY m.match_date ASC"""
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_all_matches_active() -> list[dict]:
    """Return upcoming + in-progress matches for the Live Match Day Center."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT m.id, ht.name AS home_team, at.name AS away_team,
                      m.match_date, m.matchweek, m.venue,
                      m.home_score, m.away_score
               FROM matches m
               JOIN teams ht ON m.home_team_id = ht.id
               JOIN teams at ON m.away_team_id = at.id
               WHERE m.status = 'upcoming'
               ORDER BY m.match_date ASC"""
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_players() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.name, t.name AS team, p.position, p.goals,
                      p.assists, p.yellow_cards, p.red_cards, p.appearances
               FROM players p
               JOIN teams t ON p.team_id = t.id
               ORDER BY p.goals DESC, p.assists DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_all_teams() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM teams ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def fetch_players_for_team(team_id: int) -> list[dict]:
    """Return all players belonging to a specific team."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, position FROM players WHERE team_id = ? ORDER BY name",
            (team_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_player(name: str, team_id: int, position: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO players (name, team_id, position) VALUES (?, ?, ?)",
                (name, team_id, position),
            )
        return True
    except sqlite3.Error:
        return False


def fetch_all_players_id() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.name, t.name AS team, p.team_id
               FROM players p
               JOIN teams t ON p.team_id = t.id ORDER BY p.name"""
        ).fetchall()
    return [dict(r) for r in rows]
