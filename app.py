"""
Kapasa Makasa University — Campus Football Statistics & Analytics  (v2)
LeagueRepublic-style portal with news feed, live event logger, and timelines.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import (
    init_db,
    fetch_standings,
    fetch_finished_matches,
    fetch_upcoming_matches,
    fetch_all_matches_active,
    fetch_players,
    fetch_all_teams,
    fetch_all_players_id,
    fetch_players_for_team,
    fetch_timeline_for_match,
    fetch_all_news,
    add_news_article,
    log_match_result,
    log_live_goal,
    add_player,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="KMU Football | Kapasa Makasa University",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — premium dark theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ---- App background ---- */
.stApp {
    background: linear-gradient(135deg, #070c16 0%, #0c1829 55%, #081320 100%);
    min-height: 100vh;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1a30 0%, #07101f 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* ---- Metrics ---- */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 16px;
    backdrop-filter: blur(12px);
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 36px rgba(59,130,246,0.18);
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.75rem !important; letter-spacing:0.5px; }
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.55rem !important; font-weight: 800 !important; }

/* ---- Buttons ---- */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    border: none;
    border-radius: 9px;
    padding: 10px 24px;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    transform: translateY(-2px);
    box-shadow: 0 6px 22px rgba(59,130,246,0.45);
}

/* ---- Dataframe ---- */
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border-radius: 11px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    padding: 8px 18px;
    font-weight: 500;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    color: white !important;
}

/* ---- Forms ---- */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 24px 20px;
}

/* ---- News card ---- */
.news-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 4px solid #3b82f6;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    transition: transform 0.2s, box-shadow 0.2s;
}
.news-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(59,130,246,0.12);
    border-left-color: #60a5fa;
}
.news-title { font-size: 1.05rem; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
.news-date  { font-size: 0.72rem; color: #475569; margin-bottom: 10px; letter-spacing: 0.5px; }
.news-body  { font-size: 0.88rem; color: #94a3b8; line-height: 1.6; }

/* ---- Match result row ---- */
.match-row {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: box-shadow 0.2s;
}
.match-row:hover { box-shadow: 0 4px 20px rgba(255,255,255,0.04); }
.timeline-text { font-size: 0.78rem; color: #64748b; margin-top: 6px; }
.venue-badge {
    display: inline-block;
    background: rgba(59,130,246,0.12);
    color: #60a5fa;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* ---- Live event log ---- */
.live-header {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(220,38,38,0.05));
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.pulse {
    display: inline-block;
    width: 10px; height: 10px;
    background: #ef4444;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%  { box-shadow: 0 0 0 0 rgba(239,68,68,0.6); }
    70% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
    100%{ box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}

/* ---- Alert / info ---- */
.stAlert { border-radius: 10px; }

/* ---- Labels ---- */
.stSelectbox label, .stNumberInput label, .stTextInput label, .stTextArea label {
    color: #94a3b8 !important;
    font-weight: 500;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DB initialisation (cached — runs once per session)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def initialise():
    init_db()
    return True

initialise()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

ADMIN_PASSWORD = "kmu123"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 20px 0;">
        <div style="font-size:3rem; margin-bottom:4px;">⚽</div>
        <div style="font-size:1.0rem; font-weight:800; color:#f1f5f9; letter-spacing:2px;">KMU FOOTBALL</div>
        <div style="font-size:0.68rem; color:#475569; margin-top:3px; letter-spacing:2.5px; text-transform:uppercase;">Kapasa Makasa University</div>
        <hr style="border-color:rgba(255,255,255,0.07); margin:16px 0 10px;">
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "📢  Campus News",
            "🏆  League Standings",
            "📅  Fixtures & Results",
            "🏃  Player Statistics",
            "🔒  Admin Panel",
        ],
        label_visibility="collapsed",
    )

    st.markdown("""
    <hr style="border-color:rgba(255,255,255,0.05); margin:16px 0 10px;">
    <div style="font-size:0.67rem; color:#334155; text-align:center; line-height:1.8;">
        Season 2025/26 · Matchweek 6<br>
        <span style="color:#22c55e; font-weight:600;">● Live Database Connected</span>
    </div>
    """, unsafe_allow_html=True)


# ===========================================================================
# PAGE 1 — Campus News
# ===========================================================================
if "News" in page:
    st.markdown("""
    <h1 style="font-size:2.1rem; font-weight:900; color:#f1f5f9; margin-bottom:4px;">
        📢 Campus News
    </h1>
    <p style="color:#475569; margin-bottom:28px;">
        League announcements, matchweek updates & disciplinary notices
    </p>
    """, unsafe_allow_html=True)

    articles = fetch_all_news()

    if not articles:
        st.info("No news articles published yet.")
    else:
        for art in articles:
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">{art['title']}</div>
                <div class="news-date">📅 {art['date_posted']}</div>
                <div class="news-body">{art['content']}</div>
            </div>
            """, unsafe_allow_html=True)


# ===========================================================================
# PAGE 2 — League Standings
# ===========================================================================
elif "Standings" in page:
    st.markdown("""
    <h1 style="font-size:2.1rem; font-weight:900; color:#f1f5f9; margin-bottom:4px;">
        🏆 League Standings
    </h1>
    <p style="color:#475569; margin-bottom:24px;">KMU Inter-Faculty Football League · Season 2025/26</p>
    """, unsafe_allow_html=True)

    data = fetch_standings()
    df = pd.DataFrame(data)

    if df.empty:
        st.info("No standings data available yet.")
    else:
        leader = df.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🥇 League Leader",
                  leader["name"] if len(leader["name"]) <= 14 else leader["name"].split()[0] + "…")
        c2.metric("⚽ Most Goals For", f'{df["goals_for"].max()} GF',
                  df.loc[df["goals_for"].idxmax(), "name"].split()[0])
        c3.metric("🛡️ Best Defence",   f'{df["goals_against"].min()} GA')
        c4.metric("📊 Top Points",      f'{df["points"].max()} pts')
        c5.metric("🏅 Matches Played",  int(df["played"].max()))

        st.markdown("<br>", unsafe_allow_html=True)

        display_df = df.copy()
        display_df.insert(0, "Pos", range(1, len(display_df) + 1))
        display_df.columns = ["Pos", "Club", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]

        def row_style(row):
            if row["Pos"] == 1:
                return ["background-color:rgba(234,179,8,0.13); color:#fbbf24; font-weight:700"] * len(row)
            elif row["Pos"] <= 3:
                return ["background-color:rgba(59,130,246,0.09); color:#93c5fd"] * len(row)
            elif row["Pos"] >= len(display_df) - 1:
                return ["background-color:rgba(239,68,68,0.09); color:#fca5a5"] * len(row)
            return ["color:#cbd5e1"] * len(row)

        styled = display_df.style.apply(row_style, axis=1).format(
            {"GD": lambda x: f"+{x}" if x > 0 else str(x)}
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📊 Points Comparison")
        fig = px.bar(
            display_df, x="Pts", y="Club", orientation="h",
            color="Pts", text="Pts",
            color_continuous_scale=["#1a3560", "#3b82f6", "#93c5fd"],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
            coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"},
            margin=dict(l=10, r=10, t=10, b=10), height=310,
            font=dict(family="Inter", color="#e2e8f0"),
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# PAGE 3 — Fixtures & Results
# ===========================================================================
elif "Fixtures" in page:
    st.markdown("""
    <h1 style="font-size:2.1rem; font-weight:900; color:#f1f5f9; margin-bottom:4px;">
        📅 Fixtures & Results
    </h1>
    <p style="color:#475569; margin-bottom:24px;">Complete schedule for KMU Inter-Faculty League 2025/26</p>
    """, unsafe_allow_html=True)

    tab_results, tab_upcoming = st.tabs(["✅  Recent Results", "🗓️  Upcoming Fixtures"])

    # ---- Recent Results ----
    with tab_results:
        finished = fetch_finished_matches()
        if not finished:
            st.info("No results recorded yet.")
        else:
            for row in finished:
                h, a     = row["home_team"], row["away_team"]
                hs, as_  = row["home_score"], row["away_score"]
                mw, date = row["matchweek"], row["match_date"]
                venue    = row.get("venue", "KMU Main Pitch")
                mid      = row["id"]
                winner   = "home" if hs > as_ else ("away" if as_ > hs else "draw")

                # Fetch timeline
                timeline = fetch_timeline_for_match(mid)

                h_color = "#60a5fa" if winner == "home" else "#94a3b8"
                a_color = "#60a5fa" if winner == "away" else "#94a3b8"
                h_weight = "700" if winner == "home" else "400"
                a_weight = "700" if winner == "away" else "400"

                timeline_html = (
                    f'<div class="timeline-text">{timeline}</div>'
                    if timeline else ""
                )

                st.markdown(f"""
                <div class="match-row">
                    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                        <div style="text-align:right; flex:1; min-width:120px;">
                            <span style="color:{h_color}; font-weight:{h_weight}; font-size:0.97rem;">{h}</span>
                        </div>
                        <div style="text-align:center; min-width:90px;">
                            <span style="background:rgba(255,255,255,0.07); border-radius:8px;
                                         padding:5px 14px; font-size:1.15rem; font-weight:800;
                                         color:#f1f5f9; letter-spacing:2px;">{hs} – {as_}</span>
                        </div>
                        <div style="flex:1; min-width:120px;">
                            <span style="color:{a_color}; font-weight:{a_weight}; font-size:0.97rem;">{a}</span>
                        </div>
                        <div style="text-align:right; min-width:160px;">
                            <span class="venue-badge">📍 {venue}</span>
                            <span style="color:#334155; font-size:0.72rem; margin-left:8px;">MW{mw} · {date}</span>
                        </div>
                    </div>
                    {timeline_html}
                </div>
                """, unsafe_allow_html=True)

    # ---- Upcoming Fixtures ----
    with tab_upcoming:
        upcoming = fetch_upcoming_matches()
        if not upcoming:
            st.success("🎉 All fixtures have been played!")
        else:
            for row in upcoming:
                h, a     = row["home_team"], row["away_team"]
                mw, date = row["matchweek"], row["match_date"]
                venue    = row.get("venue", "KMU Main Pitch")
                hs, as_  = row.get("home_score", 0), row.get("away_score", 0)

                # Show live score if any events logged for this match
                live_timeline = fetch_timeline_for_match(row["id"])
                score_html = (
                    f'<span style="background:rgba(239,68,68,0.15); color:#fca5a5; '
                    f'border-radius:8px; padding:5px 14px; font-size:1.05rem; font-weight:800;">'
                    f'{hs} – {as_} 🔴</span>'
                    if live_timeline
                    else
                    '<span style="background:rgba(255,255,255,0.04); color:#475569; '
                    'border-radius:8px; padding:5px 14px; font-size:0.9rem; font-weight:600;">vs</span>'
                )
                live_html = (
                    f'<div class="timeline-text" style="color:#ef4444;">'
                    f'🔴 LIVE · {live_timeline}</div>'
                    if live_timeline else ""
                )

                st.markdown(f"""
                <div class="match-row">
                    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                        <div style="text-align:right; flex:1; min-width:120px;">
                            <span style="color:#e2e8f0; font-weight:600; font-size:0.97rem;">{h}</span>
                        </div>
                        <div style="text-align:center; min-width:90px;">{score_html}</div>
                        <div style="flex:1; min-width:120px;">
                            <span style="color:#e2e8f0; font-weight:600; font-size:0.97rem;">{a}</span>
                        </div>
                        <div style="text-align:right; min-width:160px;">
                            <span class="venue-badge">📍 {venue}</span>
                            <span style="color:#334155; font-size:0.72rem; margin-left:8px;">MW{mw} · {date}</span>
                        </div>
                    </div>
                    {live_html}
                </div>
                """, unsafe_allow_html=True)


# ===========================================================================
# PAGE 4 — Player Statistics
# ===========================================================================
elif "Player" in page:
    st.markdown("""
    <h1 style="font-size:2.1rem; font-weight:900; color:#f1f5f9; margin-bottom:4px;">
        🏃 Player Statistics
    </h1>
    <p style="color:#475569; margin-bottom:24px;">Season performance analytics for all KMU registered players</p>
    """, unsafe_allow_html=True)

    players = fetch_players()
    if not players:
        st.info("No player data available.")
    else:
        df_p = pd.DataFrame(players)

        top_scorer = df_p.loc[df_p["goals"].idxmax()]
        top_assist = df_p.loc[df_p["assists"].idxmax()]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⚽ Golden Boot Leader", top_scorer["name"], f'{top_scorer["goals"]} goals')
        c2.metric("🎯 Assists Leader",      top_assist["name"], f'{top_assist["assists"]} assists')
        c3.metric("👥 Registered Players",  len(df_p))
        c4.metric("📊 Total Goals Scored",  int(df_p["goals"].sum()))

        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)

        # Bar chart — top 10 scorers
        with col_l:
            st.markdown("#### 🥅 Top Goalscorers")
            top10 = df_p.nlargest(10, "goals")
            fig_g = px.bar(
                top10, x="goals", y="name", orientation="h",
                color="goals", text="goals",
                color_continuous_scale=["#1a3560", "#3b82f6", "#22d3ee"],
                hover_data=["team", "position", "appearances"],
                template="plotly_dark",
                labels={"goals": "Goals", "name": "Player"},
            )
            fig_g.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=10, b=10), height=390,
                font=dict(family="Inter", color="#e2e8f0"),
            )
            fig_g.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_g, use_container_width=True)

        # Scatter — goals vs assists
        with col_r:
            st.markdown("#### 📈 Goals vs. Assists")
            fig_s = px.scatter(
                df_p, x="goals", y="assists",
                color="team", size="appearances",
                hover_name="name",
                hover_data={"position": True, "appearances": True},
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"goals": "Goals Scored", "assists": "Assists Made"},
            )
            fig_s.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=30, b=10), height=390,
                font=dict(family="Inter", color="#e2e8f0"),
            )
            st.plotly_chart(fig_s, use_container_width=True)

        # Assists bar chart
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Assist Leaderboard")
        top_assists = df_p.nlargest(10, "assists")
        fig_a = px.bar(
            top_assists, x="assists", y="name", orientation="h",
            color="assists", text="assists",
            color_continuous_scale=["#14532d", "#22c55e", "#86efac"],
            hover_data=["team", "position"],
            template="plotly_dark",
            labels={"assists": "Assists", "name": "Player"},
        )
        fig_a.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
            coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"},
            margin=dict(l=10, r=10, t=10, b=10), height=320,
            font=dict(family="Inter", color="#e2e8f0"),
        )
        fig_a.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_a, use_container_width=True)

        # Full table
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📋 Full Player Register")
        disp = df_p.copy()
        disp.columns = ["Name", "Team", "Position", "Goals", "Assists", "Yellow", "Red", "Apps"]
        st.dataframe(disp, use_container_width=True, hide_index=True)


# ===========================================================================
# PAGE 5 — Admin Panel
# ===========================================================================
elif "Admin" in page:
    st.markdown("""
    <h1 style="font-size:2.1rem; font-weight:900; color:#f1f5f9; margin-bottom:4px;">
        🔒 Admin Panel
    </h1>
    <p style="color:#475569; margin-bottom:24px;">Restricted access — Match Coordinators & Sports Directorate only</p>
    """, unsafe_allow_html=True)

    # ---- Login wall ----
    if not st.session_state.admin_authenticated:
        _, centre, _ = st.columns([1, 1.4, 1])
        with centre:
            with st.form("login_form"):
                st.markdown("""
                <div style="text-align:center; margin-bottom:16px;">
                    <div style="font-size:2.5rem;">🔐</div>
                    <div style="font-weight:700; color:#f1f5f9; font-size:1.1rem;">Administrator Login</div>
                    <div style="color:#475569; font-size:0.8rem; margin-top:4px;">
                        Credentials required for Match Coordinators
                    </div>
                </div>
                """, unsafe_allow_html=True)
                password = st.text_input("Password", type="password", placeholder="Enter admin password")
                login_btn = st.form_submit_button("🔓 Login", use_container_width=True)
                if login_btn:
                    if password == ADMIN_PASSWORD:
                        st.session_state.admin_authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Invalid password.")
            st.markdown(
                '<div style="text-align:center; color:#334155; font-size:0.78rem; margin-top:8px;">'
                'Demo password: <code style="color:#60a5fa;">kmu123</code></div>',
                unsafe_allow_html=True,
            )

    else:
        # ---- Authenticated ----
        col_lg, _ = st.columns([1, 6])
        with col_lg:
            if st.button("🔒 Logout"):
                st.session_state.admin_authenticated = False
                st.rerun()

        st.success("✅ Logged in as Match Coordinator")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_live, tab_result, tab_news, tab_player = st.tabs([
            "⏱️  Live Match Day Center",
            "⚽  Log Final Result",
            "📝  Publish News",
            "👤  Register Player",
        ])

        # =====================================================================
        # TAB 1 — Live Match Day Center (NEW)
        # =====================================================================
        with tab_live:
            st.markdown("""
            <div class="live-header">
                <span class="pulse"></span>
                <span style="color:#fca5a5; font-weight:700; font-size:0.95rem;">
                    LIVE MATCH DAY CENTER
                </span>
                <span style="color:#64748b; font-size:0.8rem; margin-left:auto;">
                    Log goals in real-time · Standings update instantly
                </span>
            </div>
            """, unsafe_allow_html=True)

            active_matches = fetch_all_matches_active()

            if not active_matches:
                st.info("🎉 No upcoming fixtures to manage right now.")
            else:
                all_players = fetch_all_players_id()
                all_teams   = fetch_all_teams()

                # Select active match
                match_labels = {
                    f"MW{m['matchweek']} · {m['home_team']} {m['home_score']} – {m['away_score']} {m['away_team']}  |  📍 {m['venue']}": m
                    for m in active_matches
                }
                selected_label = st.selectbox(
                    "🏟️ Select Active Match",
                    list(match_labels.keys()),
                    key="live_match_select",
                )
                sel_match = match_labels[selected_label]
                mid = sel_match["id"]

                # Filter players to the two teams
                home_team_name = sel_match["home_team"]
                away_team_name = sel_match["away_team"]

                home_players = [p for p in all_players if p["team"] == home_team_name]
                away_players = [p for p in all_players if p["team"] == away_team_name]
                eligible = home_players + away_players

                player_map = {f"{p['name']} ({p['team']})": p["id"] for p in eligible}
                player_opts = list(player_map.keys())

                # Live score display
                live_score = fetch_timeline_for_match(mid)
                c_home, c_score, c_away = st.columns([3, 1, 3])
                with c_home:
                    st.markdown(
                        f'<div style="text-align:right; font-size:1.1rem; font-weight:700; '
                        f'color:#60a5fa; padding-top:8px;">{home_team_name}</div>',
                        unsafe_allow_html=True,
                    )
                with c_score:
                    st.markdown(
                        f'<div style="text-align:center; background:rgba(255,255,255,0.07); '
                        f'border-radius:10px; padding:8px 0; font-size:1.6rem; font-weight:900; '
                        f'color:#f1f5f9;">{sel_match["home_score"]} – {sel_match["away_score"]}</div>',
                        unsafe_allow_html=True,
                    )
                with c_away:
                    st.markdown(
                        f'<div style="font-size:1.1rem; font-weight:700; '
                        f'color:#60a5fa; padding-top:8px;">{away_team_name}</div>',
                        unsafe_allow_html=True,
                    )

                if live_score:
                    st.markdown(
                        f'<div style="text-align:center; margin:8px 0 16px; '
                        f'color:#94a3b8; font-size:0.82rem;">{live_score}</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### ⚽ Log a Goal Event")

                with st.form("live_goal_form", clear_on_submit=True):
                    f1, f2, f3 = st.columns([2, 2, 1])
                    scorer_label  = f1.selectbox("🥅 Scorer", player_opts, key="scorer")
                    assist_opts   = ["— No Assist —"] + [p for p in player_opts if p != scorer_label]
                    assist_label  = f2.selectbox("🎯 Assist Provider", assist_opts, key="assister")
                    minute        = f3.number_input("⏱️ Minute", min_value=1, max_value=120, value=45, step=1)

                    log_btn = st.form_submit_button("🔴 Log Goal", use_container_width=True)

                    if log_btn:
                        scorer_id = player_map.get(scorer_label)
                        assist_id = (
                            player_map.get(assist_label)
                            if assist_label != "— No Assist —"
                            else None
                        )
                        ok, err = log_live_goal(mid, scorer_id, assist_id, int(minute))
                        if ok:
                            st.success(f"⚽ Goal logged — {minute}'  {scorer_label.split(' (')[0]}!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {err}")

                # Timeline for selected match
                timeline = fetch_timeline_for_match(mid)
                if timeline:
                    st.markdown("##### 📋 Current Match Timeline")
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.03); border:1px solid '
                        f'rgba(255,255,255,0.07); border-radius:12px; padding:14px 18px; '
                        f'color:#94a3b8; font-size:0.85rem; line-height:2;">{timeline}</div>',
                        unsafe_allow_html=True,
                    )

        # =====================================================================
        # TAB 2 — Log Final Result
        # =====================================================================
        with tab_result:
            st.markdown("#### Record Full-Time Score")
            upcoming = fetch_upcoming_matches()

            if not upcoming:
                st.info("🎉 No upcoming matches — all fixtures have been played!")
            else:
                match_options = {
                    f"MW{r['matchweek']} · {r['home_team']} vs {r['away_team']} ({r['match_date']})": r["id"]
                    for r in upcoming
                }
                with st.form("log_result_form"):
                    sel = st.selectbox("Select Match", list(match_options.keys()))
                    mid_r = match_options[sel]
                    c1, c2 = st.columns(2)
                    hs = c1.number_input("Home Score", min_value=0, max_value=30, value=0, step=1)
                    as_ = c2.number_input("Away Score", min_value=0, max_value=30, value=0, step=1)
                    submitted = st.form_submit_button("✅ Submit Final Result", use_container_width=True)
                    if submitted:
                        ok = log_match_result(mid_r, int(hs), int(as_))
                        if ok:
                            st.success("🎉 Match result saved and standings updated!")
                            st.balloons()
                        else:
                            st.error("❌ Failed — match may already be finished.")

        # =====================================================================
        # TAB 3 — Publish News (NEW)
        # =====================================================================
        with tab_news:
            st.markdown("#### 📝 Publish a News Article")
            with st.form("news_form", clear_on_submit=True):
                title   = st.text_input("Headline", placeholder="e.g. 🏆 Matchweek 4 Preview")
                content = st.text_area(
                    "Article Body",
                    placeholder="Write your announcement, match report, or update here...",
                    height=160,
                )
                pub_btn = st.form_submit_button("📢 Publish Article", use_container_width=True)
                if pub_btn:
                    if title.strip() and content.strip():
                        ok = add_news_article(title.strip(), content.strip())
                        if ok:
                            st.success("✅ Article published to the Campus News feed!")
                        else:
                            st.error("❌ Failed to publish. Please try again.")
                    else:
                        st.warning("⚠️ Both headline and body are required.")

        # =====================================================================
        # TAB 4 — Register Player
        # =====================================================================
        with tab_player:
            st.markdown("#### 👤 Register New Player")
            teams = fetch_all_teams()
            team_map = {t["name"]: t["id"] for t in teams}

            with st.form("add_player_form"):
                pname    = st.text_input("Full Name", placeholder="e.g. Chanda Mwape")
                pteam    = st.selectbox("Faculty Team", list(team_map.keys()))
                ppos     = st.selectbox("Position", ["Forward", "Midfielder", "Defender", "Goalkeeper"])
                add_btn  = st.form_submit_button("➕ Register Player", use_container_width=True)
                if add_btn:
                    if pname.strip():
                        ok = add_player(pname.strip(), team_map[pteam], ppos)
                        if ok:
                            st.success(f"✅ {pname} registered to {pteam}!")
                        else:
                            st.error("❌ Registration failed. Please try again.")
                    else:
                        st.warning("⚠️ Please enter a valid player name.")
