"""
COVID-19 Contact Tracer using Graph Traversal Algorithms (BFS/DFS)
CSA06 - Design and Analysis of Algorithms
SIMATS Engineering, Saveetha University
"""

from flask import Flask, render_template, request, jsonify
import sqlite3, json, os, datetime
import networkx as nx

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'contacts.db')

# ─────────────────────────────────────────────────────────────
# DATABASE INITIALISATION
# ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS persons (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            location TEXT,
            status TEXT DEFAULT 'healthy',
            test_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_a TEXT NOT NULL,
            person_b TEXT NOT NULL,
            contact_date TEXT NOT NULL,
            duration_min REAL DEFAULT 10,
            distance_m REAL DEFAULT 1.5,
            location TEXT,
            signal_type TEXT DEFAULT 'Bluetooth LE',
            FOREIGN KEY(person_a) REFERENCES persons(id),
            FOREIGN KEY(person_b) REFERENCES persons(id)
        );

        CREATE TABLE IF NOT EXISTS quarantine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT,
            reason TEXT,
            algorithm TEXT,
            risk_score REAL,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(person_id) REFERENCES persons(id)
        );

        CREATE TABLE IF NOT EXISTS traversal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT,
            algorithm TEXT,
            nodes_visited INTEGER,
            edges_traversed INTEGER,
            depth INTEGER,
            execution_time_ms REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            result_json TEXT
        );
    """)
    conn.commit()

    # ── Seed sample data if empty ──
    c.execute("SELECT COUNT(*) FROM persons")
    if c.fetchone()[0] == 0:
        persons = [
            ('P001','Arjun Kumar',34,'Male','Adyar','positive','2025-03-08'),
            ('P002','Priya Sharma',28,'Female','T Nagar','exposed','2025-03-09'),
            ('P003','Ravi Mehta',45,'Male','Velachery','exposed','2025-03-10'),
            ('P004','Sneha Iyer',31,'Female','Anna Nagar','healthy',None),
            ('P005','Karthik L',22,'Male','Chromepet','healthy',None),
            ('P006','Hemanth Kumar',23,'Male','Tambaram','exposed','2025-03-11'),
            ('P007','Durga Prasanth',24,'Male','Guindy','healthy',None),
            ('P008','Lakshmi R',38,'Female','Mylapore','exposed','2025-03-11'),
            ('P009','Vijay S',55,'Male','Porur','positive','2025-03-07'),
            ('P010','Meena T',42,'Female','Sholinganallur','healthy',None),
            ('P011','Anand J',29,'Male','Nungambakkam','healthy',None),
            ('P012','Deepa K',36,'Female','Vadapalani','exposed','2025-03-12'),
        ]
        c.executemany("INSERT OR IGNORE INTO persons VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", persons)

        contacts = [
            ('P001','P002','2025-03-06',45,0.8,'Central Market','Bluetooth LE'),
            ('P001','P003','2025-03-06',30,1.2,'Office Block A','GPS'),
            ('P001','P004','2025-03-07',15,1.8,'Bus Stop #7','Bluetooth LE'),
            ('P002','P005','2025-03-07',20,1.0,'Mall Corridor','Bluetooth LE'),
            ('P002','P006','2025-03-08',60,0.5,'Office','GPS'),
            ('P003','P007','2025-03-07',10,1.5,'Park','GPS'),
            ('P003','P008','2025-03-08',25,0.9,'Restaurant','Bluetooth LE'),
            ('P006','P010','2025-03-09',40,1.1,'Library','GPS'),
            ('P006','P011','2025-03-09',12,1.6,'Gym','Bluetooth LE'),
            ('P008','P012','2025-03-10',35,0.7,'Hospital','Bluetooth LE'),
            ('P009','P001','2025-03-05',90,0.3,'Home','GPS'),
            ('P009','P004','2025-03-06',20,1.4,'Pharmacy','Bluetooth LE'),
            ('P010','P012','2025-03-11',18,1.3,'Park','GPS'),
        ]
        c.executemany("""INSERT INTO contacts
            (person_a,person_b,contact_date,duration_min,distance_m,location,signal_type)
            VALUES(?,?,?,?,?,?,?)""", contacts)
        conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────
def build_graph():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT person_a, person_b, duration_min, distance_m FROM contacts WHERE duration_min > 5 AND distance_m < 2.0")
    edges = c.fetchall()
    c.execute("SELECT id, name, status FROM persons")
    persons = c.fetchall()
    conn.close()

    G = nx.Graph()
    for pid, name, status in persons:
        G.add_node(pid, name=name, status=status)
    for pa, pb, dur, dist in edges:
        G.add_edge(pa, pb, duration=dur, distance=dist)
    return G


# ─────────────────────────────────────────────────────────────
# MODULE 1 – CONTACT LOG INGESTION  (helper)
# ─────────────────────────────────────────────────────────────
def get_all_persons():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM persons ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    cols = ['id','name','age','gender','location','status','test_date','created_at']
    return [dict(zip(cols, r)) for r in rows]

def get_all_contacts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT c.id, c.person_a, pa.name, c.person_b, pb.name,
                        c.contact_date, c.duration_min, c.distance_m,
                        c.location, c.signal_type
                 FROM contacts c
                 JOIN persons pa ON c.person_a = pa.id
                 JOIN persons pb ON c.person_b = pb.id
                 ORDER BY c.contact_date DESC""")
    rows = c.fetchall()
    conn.close()
    cols = ['id','person_a_id','person_a_name','person_b_id','person_b_name',
            'contact_date','duration_min','distance_m','location','signal_type']
    return [dict(zip(cols, r)) for r in rows]


# ─────────────────────────────────────────────────────────────
# MODULE 2 – INFECTION CHAIN  (BFS + DFS)
# ─────────────────────────────────────────────────────────────
def bfs_trace(source_id, incubation_days=14):
    import time
    start = time.time()
    G = build_graph()
    if source_id not in G:
        return {'error': 'Person not found'}

    visited = {}   # node -> depth
    queue = [(source_id, 0)]
    order = []
    parent = {source_id: None}
    edges_traversed = 0

    while queue:
        node, depth = queue.pop(0)
        if node in visited:
            continue
        if depth > incubation_days:
            continue
        visited[node] = depth
        order.append({'id': node,
                      'name': G.nodes[node].get('name','?'),
                      'status': G.nodes[node].get('status','healthy'),
                      'depth': depth})
        for neighbor in G.neighbors(node):
            edges_traversed += 1
            if neighbor not in visited:
                parent[neighbor] = node
                queue.append((neighbor, depth + 1))

    ms = round((time.time() - start) * 1000, 2)
    result = {'algorithm': 'BFS', 'source': source_id,
              'nodes_visited': len(visited), 'edges_traversed': edges_traversed,
              'max_depth': max(v for v in visited.values()) if visited else 0,
              'execution_ms': ms, 'chain': order, 'parent': parent}

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""INSERT INTO traversal_log
        (source_id, algorithm, nodes_visited, edges_traversed, depth, execution_time_ms, result_json)
        VALUES(?,?,?,?,?,?,?)""",
        (source_id, 'BFS', len(visited), edges_traversed,
         result['max_depth'], ms, json.dumps(result)))
    conn.commit(); conn.close()
    return result


def dfs_trace(source_id, incubation_days=14):
    import time
    start = time.time()
    G = build_graph()
    if source_id not in G:
        return {'error': 'Person not found'}

    visited = {}
    stack = [(source_id, 0)]
    order = []
    edges_traversed = 0

    while stack:
        node, depth = stack.pop()
        if node in visited:
            continue
        if depth > incubation_days:
            continue
        visited[node] = depth
        order.append({'id': node,
                      'name': G.nodes[node].get('name','?'),
                      'status': G.nodes[node].get('status','healthy'),
                      'depth': depth})
        for neighbor in list(G.neighbors(node))[::-1]:
            edges_traversed += 1
            if neighbor not in visited:
                stack.append((neighbor, depth + 1))

    ms = round((time.time() - start) * 1000, 2)
    result = {'algorithm': 'DFS', 'source': source_id,
              'nodes_visited': len(visited), 'edges_traversed': edges_traversed,
              'max_depth': max(v for v in visited.values()) if visited else 0,
              'execution_ms': ms, 'chain': order}

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""INSERT INTO traversal_log
        (source_id, algorithm, nodes_visited, edges_traversed, depth, execution_time_ms, result_json)
        VALUES(?,?,?,?,?,?,?)""",
        (source_id, 'DFS', len(visited), edges_traversed,
         result['max_depth'], ms, json.dumps(result)))
    conn.commit(); conn.close()
    return result


# ─────────────────────────────────────────────────────────────
# MODULE 3 – RISK SCORING
# ─────────────────────────────────────────────────────────────
def compute_risk(person_id):
    import math
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # contacts of this person
    c.execute("""SELECT c.duration_min, c.distance_m,
                        p.status
                 FROM contacts c
                 JOIN persons p ON (CASE WHEN c.person_a=? THEN c.person_b ELSE c.person_a END) = p.id
                 WHERE (c.person_a=? OR c.person_b=?) AND c.duration_min > 5 AND c.distance_m < 2""",
              (person_id, person_id, person_id))
    rows = c.fetchall()

    if not rows:
        conn.close()
        return {'person_id': person_id, 'risk_score': 0, 'risk_level': 'LOW',
                'factors': {'proximity': 0, 'duration': 0, 'chain_depth': 0, 'positive_contacts': 0}}

    # run BFS to get chain depth
    bfs = bfs_trace(person_id)
    chain_depth = bfs.get('max_depth', 0)
    positive_contacts = sum(1 for r in rows if r[2] == 'positive')

    avg_dist = sum(r[1] for r in rows) / len(rows)
    avg_dur  = sum(r[0] for r in rows) / len(rows)
    indoor_pct = 80  # simplified

    proximity  = max(0, 1 - avg_dist/2.0) * 40
    duration_s = min(avg_dur/30, 1) * 10
    chain_s    = 30 / (1 + math.exp(-0.5 * (positive_contacts - 2)))
    venue_s    = (indoor_pct/100) * 20

    total = min(100, round(proximity + duration_s + chain_s + venue_s))
    level = 'HIGH' if total >= 70 else ('MEDIUM' if total >= 40 else 'LOW')

    conn.close()
    return {
        'person_id': person_id, 'risk_score': total, 'risk_level': level,
        'contacts_count': len(rows), 'positive_contacts': positive_contacts,
        'chain_depth': chain_depth,
        'factors': {
            'proximity': round(proximity, 1),
            'duration': round(duration_s, 1),
            'chain_depth_score': round(chain_s, 1),
            'venue': round(venue_s, 1)
        }
    }


# ─────────────────────────────────────────────────────────────
# MODULE 4 – GRAPH VISUALIZATION DATA
# ─────────────────────────────────────────────────────────────
def get_graph_data():
    G = build_graph()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, status, location FROM persons")
    pdata = {r[0]: {'name': r[1], 'status': r[2], 'location': r[3]} for r in c.fetchall()}
    conn.close()

    color_map = {'positive': '#ff3d71', 'exposed': '#ffd740',
                 'healthy': '#39d353', 'quarantine': '#00e5ff'}

    nodes = []
    for node in G.nodes():
        info = pdata.get(node, {})
        status = info.get('status', 'healthy')
        nodes.append({
            'id': node,
            'label': info.get('name', node),
            'status': status,
            'location': info.get('location', ''),
            'color': color_map.get(status, '#888888'),
            'size': 20 if status == 'positive' else 14
        })

    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({'from': u, 'to': v,
                      'duration': d.get('duration', 10),
                      'distance': d.get('distance', 1.5)})
    return {'nodes': nodes, 'edges': edges}


# ─────────────────────────────────────────────────────────────
# MODULE 5 – ALERT & DASHBOARD STATS
# ─────────────────────────────────────────────────────────────
def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM persons GROUP BY status")
    status_counts = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM contacts")
    total_contacts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM traversal_log")
    traversals = c.fetchone()[0]
    c.execute("SELECT AVG(nodes_visited) FROM traversal_log")
    avg_nodes = c.fetchone()[0] or 0
    conn.close()

    return {
        'total_persons': sum(status_counts.values()),
        'positive': status_counts.get('positive', 0),
        'exposed': status_counts.get('exposed', 0),
        'healthy': status_counts.get('healthy', 0),
        'quarantine': status_counts.get('quarantine', 0),
        'total_contacts': total_contacts,
        'traversals_run': traversals,
        'avg_nodes_per_traversal': round(avg_nodes, 1),
        'status_counts': status_counts
    }


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# Module 1
@app.route('/api/persons', methods=['GET'])
def api_persons():
    return jsonify(get_all_persons())

@app.route('/api/persons', methods=['POST'])
def api_add_person():
    d = request.json
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO persons(id,name,age,gender,location,status,test_date) VALUES(?,?,?,?,?,?,?)",
                     (d['id'], d['name'], d.get('age'), d.get('gender'),
                      d.get('location'), d.get('status','healthy'), d.get('test_date')))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/contacts', methods=['GET'])
def api_contacts():
    return jsonify(get_all_contacts())

@app.route('/api/contacts', methods=['POST'])
def api_add_contact():
    d = request.json
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""INSERT INTO contacts(person_a,person_b,contact_date,
                        duration_min,distance_m,location,signal_type)
                        VALUES(?,?,?,?,?,?,?)""",
                     (d['person_a'], d['person_b'], d.get('contact_date', str(datetime.date.today())),
                      d.get('duration_min', 10), d.get('distance_m', 1.5),
                      d.get('location',''), d.get('signal_type','Bluetooth LE')))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# Module 2 – BFS / DFS
@app.route('/api/bfs/<source_id>')
def api_bfs(source_id):
    days = int(request.args.get('days', 14))
    return jsonify(bfs_trace(source_id, days))

@app.route('/api/dfs/<source_id>')
def api_dfs(source_id):
    days = int(request.args.get('days', 14))
    return jsonify(dfs_trace(source_id, days))

@app.route('/api/traversal_log')
def api_traversal_log():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM traversal_log ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    cols = ['id','source_id','algorithm','nodes_visited','edges_traversed','depth','execution_ms','timestamp','result_json']
    return jsonify([dict(zip(cols, r)) for r in rows])

# Module 3 – Risk
@app.route('/api/risk/<person_id>')
def api_risk(person_id):
    return jsonify(compute_risk(person_id))

@app.route('/api/risk_all')
def api_risk_all():
    persons = get_all_persons()
    results = []
    for p in persons:
        r = compute_risk(p['id'])
        r['name'] = p['name']
        r['status'] = p['status']
        results.append(r)
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    return jsonify(results)

@app.route('/api/quarantine', methods=['POST'])
def api_quarantine():
    d = request.json
    conn = sqlite3.connect(DB_PATH)
    try:
        start = str(datetime.date.today())
        end = str(datetime.date.today() + datetime.timedelta(days=14))
        conn.execute("""INSERT INTO quarantine_log(person_id,reason,algorithm,risk_score,start_date,end_date)
                        VALUES(?,?,?,?,?,?)""",
                     (d['person_id'], d.get('reason','High risk contact'),
                      d.get('algorithm','BFS'), d.get('risk_score',0), start, end))
        conn.execute("UPDATE persons SET status='quarantine' WHERE id=?", (d['person_id'],))
        conn.commit()
        return jsonify({'success': True, 'start': start, 'end': end})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# Module 4 – Graph
@app.route('/api/graph')
def api_graph():
    return jsonify(get_graph_data())

# Module 5 – Dashboard
@app.route('/api/dashboard')
def api_dashboard():
    return jsonify(get_dashboard_stats())

@app.route('/api/alerts')
def api_alerts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT q.id, q.person_id, p.name, q.reason, q.algorithm,
                        q.risk_score, q.start_date, q.end_date, q.status
                 FROM quarantine_log q JOIN persons p ON q.person_id = p.id
                 ORDER BY q.id DESC LIMIT 20""")
    rows = c.fetchall()
    conn.close()
    cols = ['id','person_id','name','reason','algorithm','risk_score','start_date','end_date','status']
    return jsonify([dict(zip(cols, r)) for r in rows])


if __name__ == '__main__':
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    app.run(debug=True, port=5050)