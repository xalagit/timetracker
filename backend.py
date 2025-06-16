# backend.py
import sqlite3, time, os
from datetime import datetime, timedelta

DB = "time_tracker.db"

class TrackerDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                description TEXT,
                start_ts REAL,
                end_ts REAL
            )""")
        self.conn.commit()

    def start_entry(self, description):
        ts = time.time()
        cur = self.conn.cursor()
        cur.execute("INSERT INTO entries (description, start_ts) VALUES (?,?)", (description, ts))
        self.conn.commit()
        return cur.lastrowid

    def stop_entry(self, entry_id):
        ts = time.time()
        self.conn.execute("UPDATE entries SET end_ts = ? WHERE id = ?", (ts, entry_id))
        self.conn.commit()

    def delete_entry(self, entry_id):
        self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

    def get_entries(self):
        return self.conn.execute(
            "SELECT id,description,start_ts,end_ts FROM entries ORDER BY start_ts DESC"
        ).fetchall()

    def export_csv(self, filepath):
        rows = self.get_entries()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID","Description","Start","End","Duration(s)"])
            for id_, d, s, e in rows:
                dur = (e or time.time()) - s
                w.writerow([id_, d,
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s)),
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e)) if e else "",
                            int(dur)])

    def auto_backup(self, backup_dir="backups", interval_s=600, retention_days=7):
        os.makedirs(backup_dir, exist_ok=True)
        now = datetime.now()
        cutoff = now - timedelta(days=retention_days)

        for fn in os.listdir(backup_dir):
            path = os.path.join(backup_dir, fn)
            if os.path.getmtime(path) < cutoff.timestamp():
                os.remove(path)

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(backup_dir, f"backup_{timestamp}.db")

        with sqlite3.connect(DB) as src, sqlite3.connect(dest) as dst:
            src.backup(dst)  # backup seguro incluso si DB está en uso :contentReference[oaicite:1]{index=1}
