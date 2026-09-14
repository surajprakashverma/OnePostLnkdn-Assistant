"""
Usage:
    python load_roadmap.py "C:\path\to\roadmap.pdf" 30
    python load_roadmap.py "C:\path\to\roadmap.pdf" 30 --replace
"""
import sys
from app.services.roadmap_ingest_service import ingest_roadmap

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python load_roadmap.py <file_path> <num_days> [--replace]")
        sys.exit(1)

    file_path = sys.argv[1]
    num_days = int(sys.argv[2])
    replace_existing = "--replace" in sys.argv

    ingest_roadmap(file_path, num_days, replace_existing=replace_existing)