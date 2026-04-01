COVID-19 Contact Tracer using Graph Traversal Algorithms (BFS/DFS)
CSA06 — Design and Analysis of Algorithms
SIMATS Engineering, Saveetha University

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO RUN THE APPLICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Install dependencies
  pip install flask networkx

Step 2: Run the application
  python app.py

Step 3: Open your browser
  http://localhost:5050

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

covid_tracer/
  app.py                  ← Flask backend (all 5 modules)
  templates/
    index.html            ← Full frontend (vis.js graph + UI)
  data/
    contacts.db           ← SQLite database (auto-created)
  README.txt              ← This file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

M1: Contact Log Ingestion     → /api/persons, /api/contacts
M2: BFS/DFS Infection Chain   → /api/bfs/<id>, /api/dfs/<id>
M3: Risk Scoring Engine       → /api/risk/<id>, /api/risk_all
M4: Graph Visualization       → /api/graph  (vis.js network)
M5: Alert & Quarantine Mgmt   → /api/quarantine, /api/alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALGORITHMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BFS: Queue (FIFO), O(V+E), shortest transmission path
DFS: Stack (LIFO), O(V+E), deep branch exploration
Risk Score: Proximity(40) + Duration(10) + ChainDepth(30) + Venue(20)