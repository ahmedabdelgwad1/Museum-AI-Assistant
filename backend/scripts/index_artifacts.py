#!/usr/bin/env python3
"""
Indexing pipeline: Load the CSV, embed artifacts, and store in ChromaDB.

Run once (or when the dataset changes):
    python scripts/index_artifacts.py
"""

import sys
import os
import logging

# Make sure parent package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.rag.embedder import embed_texts
from app.rag.vectorstore import get_collection, add_documents, collection_count
from app.utils.helpers import clean_text, truncate_text, build_artifact_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# Column name mapping (from CSV header)
COL_SECTION_NUMBER = "Section Number"
COL_SECTION_NAME_AR = "Section Name Arabic"
COL_SECTION_NAME_EN = "Section Name English"
COL_NAME_AR = "Artifact Name Arabic"
COL_NAME_EN = "Artifact Name English"
COL_DESC_AR = "Description Arabic"
COL_DESC_EN = "Description English"
COL_CAT_AR = "Category Arabic"
COL_CAT_EN = "Category English"
COL_SITE_AR = "Discovery site Arabic"
COL_SITE_EN = "Discovery Site English"
COL_HALL_AR = "Hall Arabic"
COL_HALL_EN = "Hall English"
COL_LINK = "Link"

BATCH_SIZE = 32


def build_document_text(row: pd.Series) -> str:
    """
    Build the combined text chunk for embedding from a single artifact row.
    Uses both English and Arabic fields for true multilingual retrieval.
    """
    name_en = clean_text(str(row.get(COL_NAME_EN, "") or ""))
    name_ar = clean_text(str(row.get(COL_NAME_AR, "") or ""))
    category_en = clean_text(str(row.get(COL_CAT_EN, "") or ""))
    hall_en = clean_text(str(row.get(COL_HALL_EN, "") or ""))
    site_en = clean_text(str(row.get(COL_SITE_EN, "") or ""))
    section_en = clean_text(str(row.get(COL_SECTION_NAME_EN, "") or ""))
    desc_en = truncate_text(clean_text(str(row.get(COL_DESC_EN, "") or "")), 1000)
    desc_ar = truncate_text(clean_text(str(row.get(COL_DESC_AR, "") or "")), 500)

    parts = [
        f"Name: {name_en} / {name_ar}",
        f"Category: {category_en}",
        f"Hall: {hall_en}",
        f"Section: {section_en}",
        f"Discovery Site: {site_en}",
        f"Description: {desc_en}",
        f"وصف: {desc_ar}",
    ]
    return "\n".join(p for p in parts if p.split(": ", 1)[-1].strip())


def build_metadata(row: pd.Series, artifact_id: str) -> dict:
    """Build the metadata dict to store alongside the embedding."""
    return {
        "artifact_id": artifact_id,
        "artifact_name_en": clean_text(str(row.get(COL_NAME_EN, "") or "")),
        "artifact_name_ar": clean_text(str(row.get(COL_NAME_AR, "") or "")),
        "description_en": clean_text(str(row.get(COL_DESC_EN, "") or "")),
        "description_ar": clean_text(str(row.get(COL_DESC_AR, "") or "")),
        "category_en": clean_text(str(row.get(COL_CAT_EN, "") or "")),
        "category_ar": clean_text(str(row.get(COL_CAT_AR, "") or "")),
        "hall_en": clean_text(str(row.get(COL_HALL_EN, "") or "")),
        "hall_ar": clean_text(str(row.get(COL_HALL_AR, "") or "")),
        "discovery_site_en": clean_text(str(row.get(COL_SITE_EN, "") or "")),
        "discovery_site_ar": clean_text(str(row.get(COL_SITE_AR, "") or "")),
        "section_name_en": clean_text(str(row.get(COL_SECTION_NAME_EN, "") or "")),
        "section_name_ar": clean_text(str(row.get(COL_SECTION_NAME_AR, "") or "")),
        "section_number": str(row.get(COL_SECTION_NUMBER, "") or ""),
        "link": str(row.get(COL_LINK, "") or ""),
    }


def main() -> None:
    csv_path = settings.csv_data_path
    logger.info("Loading dataset from: %s", csv_path)

    if not os.path.exists(csv_path):
        logger.error("CSV file not found: %s", csv_path)
        sys.exit(1)

    df = pd.read_csv(csv_path, encoding="utf-8")
    logger.info("Loaded %d rows from CSV.", len(df))

    # Drop rows where both English and Arabic artifact names are missing
    df = df.dropna(subset=[COL_NAME_EN, COL_NAME_AR], how="all")
    logger.info("After filtering: %d valid artifact rows.", len(df))

    # Check existing indexed count
    existing = collection_count()
    logger.info("Existing documents in ChromaDB: %d", existing)

    all_ids: list[str] = []
    all_documents: list[str] = []
    all_metadatas: list[dict] = []
    all_embeddings: list[list[float]] = []

    logger.info("Building document chunks and embeddings...")

    for batch_start in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[batch_start : batch_start + BATCH_SIZE]
        batch_docs = []
        batch_ids = []
        batch_metas = []

        for local_idx, (_, row) in enumerate(batch.iterrows()):
            global_idx = batch_start + local_idx
            name_en = str(row.get(COL_NAME_EN, "") or "").strip()
            artifact_id = build_artifact_id(global_idx, name_en or f"artifact_{global_idx}")

            doc_text = build_document_text(row)
            metadata = build_metadata(row, artifact_id)

            batch_docs.append(doc_text)
            batch_ids.append(artifact_id)
            batch_metas.append(metadata)

        # Embed the batch
        batch_embeddings = embed_texts(batch_docs)

        all_ids.extend(batch_ids)
        all_documents.extend(batch_docs)
        all_metadatas.extend(batch_metas)
        all_embeddings.extend(batch_embeddings)

        pct = min(100, int((batch_start + len(batch)) / len(df) * 100))
        logger.info(
            "Progress: %d/%d artifacts embedded (%d%%)",
            batch_start + len(batch),
            len(df),
            pct,
        )

    logger.info("Storing %d documents in ChromaDB...", len(all_ids))
    add_documents(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_documents,
        metadatas=all_metadatas,
    )

    final_count = collection_count()
    logger.info("=" * 60)
    logger.info("Indexing complete!")
    logger.info("Total artifacts in ChromaDB: %d", final_count)
    logger.info("Embedding model: %s", settings.embedding_model)
    logger.info("Collection name: %s", settings.chroma_collection_name)
    logger.info("ChromaDB path: %s", settings.chroma_persist_dir)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
