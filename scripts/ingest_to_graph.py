"""Ingest prepared public reference chunks into a Zep user graph."""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from zep_cloud import Zep

BASE_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("ZEP_API_KEY")
    user_id = os.getenv("ZEP_DOCS_USER_ID")
    if not api_key or not user_id:
        raise ValueError("Set ZEP_API_KEY and ZEP_DOCS_USER_ID in .env first.")

    chunks_path = BASE_DIR / "data" / "chunked-docs.json"
    if not chunks_path.is_file():
        raise FileNotFoundError(
            f"{chunks_path} is missing. Prepare chunked-docs.json before ingestion."
        )
    with chunks_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)
    if not isinstance(chunks, list):
        raise ValueError("chunked-docs.json must contain a JSON array.")

    zep = Zep(api_key=api_key)
    try:
        zep.user.add(
            user_id=user_id,
            email="docs@system.local",
            first_name="SmartClass",
            last_name="Reference",
        )
    except Exception as error:
        if "already exists" not in str(error).lower() and "409" not in str(error):
            raise

    episode_ids = []
    failures = []
    for index, chunk in enumerate(chunks, start=1):
        heading = str(chunk.get("heading", f"Reference {index}"))
        header = f"{chunk.get('context', '')}\n\n# {heading}\n\n"
        content = str(chunk.get("content", ""))
        available = max(0, 10_000 - len(header))
        if len(content) > available:
            content = content[: max(0, available - 20)] + "\n\n[truncated]"
        try:
            episode = zep.graph.add(
                user_id=user_id,
                type="text",
                data=header + content,
            )
            episode_ids.append(episode.uuid_)
            print(f"Ingested {index}/{len(chunks)}: {heading}")
        except Exception as error:
            failures.append((index, str(error)))
            print(f"Failed chunk {index}/{len(chunks)}: {error}")
        time.sleep(0.5)

    mapping = {
        "user_id": user_id,
        "total_episodes": len(episode_ids),
        "episode_ids": episode_ids,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    mapping_path = BASE_DIR / "data" / "episode-mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Ingested {len(episode_ids)}/{len(chunks)} chunks; mapping: {mapping_path}")
    if failures:
        raise RuntimeError(f"{len(failures)} chunks failed; review the messages above.")


if __name__ == "__main__":
    main()