from sqlalchemy import text
from app.db.database import engine, init_db

with engine.connect() as conn:
    for stmt in [
        "ALTER TABLE roadmap_topics ADD COLUMN roadmap_run_id INTEGER",
        "ALTER TABLE posted_log ADD COLUMN roadmap_run_id INTEGER",
    ]:
        try:
            conn.execute(text(stmt))
            conn.commit()
            print(f"Applied: {stmt}")
        except Exception as e:
            print(f"Skipped (likely already applied): {e}")

init_db()
print("roadmap_runs table ensured.")

