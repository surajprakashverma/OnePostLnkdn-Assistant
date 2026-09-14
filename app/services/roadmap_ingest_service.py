import truststore
truststore.inject_into_ssl()

import json
import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import RoadmapTopic


llm = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_Model,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3,
)

ROADMAP_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert curriculum planner. Below is the raw text of a learning roadmap document.

Roadmap document text:
---
{roadmap_text}
---

Break this roadmap down into exactly {num_days} days of learning, distributed logically
(related topics grouped together, progressing from fundamentals to advanced concepts).

For each day, output:
- day: integer (1 to {num_days})
- topic: short topic name (e.g. "Django ORM")
- subtopic: a more specific angle for that day (e.g. "QuerySet optimization")
- notes: 1-2 sentences of learning context for that day, taken from the document

Respond ONLY with a valid JSON array, no other text, in this exact format:
[
  {{"day": 1, "topic": "...", "subtopic": "...", "notes": "..."}},
  {{"day": 2, "topic": "...", "subtopic": "...", "notes": "..."}}
]
"""
)


def extract_text_from_file(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == ".txt":
        return path.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported file type: {ext}. Use .pdf, .docx, or .txt")


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts).strip()
    return str(content).strip()


def structure_roadmap(roadmap_text: str, num_days: int) -> list:
    chain = ROADMAP_PROMPT | llm
    response = chain.invoke({"roadmap_text": roadmap_text, "num_days": num_days})
    raw_text = _extract_text(response.content)

    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def save_roadmap_to_db(days_list, replace_existing=False):
    db = SessionLocal()
    try:
        if replace_existing:
            db.query(RoadmapTopic).delete()
            db.commit()

        for day in days_list:
            db.add(RoadmapTopic(
                day_or_order=day["day"],
                topic=day["topic"],
                subtopic=day.get("subtopic", ""),
                notes=day.get("notes", ""),
            ))
        db.commit()
        print(f"Saved {len(days_list)} roadmap topics to the database.")
    finally:
        db.close()


def ingest_roadmap(file_path: str, num_days: int, replace_existing: bool = False):
    print(f"Extracting text from {file_path}...")
    text = extract_text_from_file(file_path)
    print(f"Extracted {len(text)} characters. Structuring into {num_days} days via Gemini...")

    days_list = structure_roadmap(text, num_days)
    print(f"Gemini produced {len(days_list)} day entries.")

    save_roadmap_to_db(days_list, replace_existing=replace_existing)
    return days_list