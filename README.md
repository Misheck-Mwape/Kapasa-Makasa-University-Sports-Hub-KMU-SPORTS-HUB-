# ⚽ KMU Campus Football Analytics Hub

An interactive, database-driven web application built to manage, track, and analyze football league statistics, player performance, and live match day results for **Kapasa Makasa University (KMU)**.

##  Key Features
 **Campus News Feed**: A centralized bulletin board for official matchweek announcements, league headlines, and match updates.
 **Live Standings Table**: Dynamic calculation of league points, goal differences, wins, losses, and draws derived straight from relational SQL transactions.
** Match Center Timeline**: Displays comprehensive fixtures and recent results complete with a minute-by-minute scorer breakdown (e.g., *Misheck Mwape 14'*).
 **Advanced Player Statistics**: Dynamic analytics leaderboards tracking the league's top goalscorers and playmakers.
 **Admin Match Center Logger**: A secure administration panel allowing sports coordinators to input goals, assists, and match events in real-time straight from the pitchside.

##  Tech Stack
* **Frontend GUI:** Streamlit (Python-native web framework)
* **Data Visualizations:** Plotly Express & Pandas
* **Database Management:** SQLite3 (Relational pipeline with WAL mode enabled for concurrent traffic)

## 📁 Architecture Layout
```text
kmu-sports-hub/
│
├── .streamlit/
│   └── config.toml       # Custom university green/white theme settings
│
├── src/
│   └── database.py       # SQL schema initializations & relational transactions
│
├── app.py                # Main web application dashboard routing logic
└── requirements.txt      # Third-party dependency definitions
