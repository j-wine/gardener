import os
import pandas as pd
import requests
import json
from tqdm import tqdm
from datetime import datetime

RAG_CHUNKS_DIR = "resources/rag_chunks"
OUTPUT_PARQUET_PATH = "data/ecocrop_rag_embeddings.parquet"
EMBEDDING_MODEL_ENDPOINT = "https://models.mylab.th-luebeck.dev/v1/embeddings"
HEADERS = {"Content-Type": "application/json"}


def load_rag_chunk(idx):
    chunk_path = os.path.join(RAG_CHUNKS_DIR, f"{idx}.txt")
    with open(chunk_path, "r", encoding="utf-8") as f:
        return f.read()


def get_embedding(text):
    payload = {"input": text, "model": "bge-m3"}
    response = requests.post(EMBEDDING_MODEL_ENDPOINT, headers=HEADERS, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def main():
    df = pd.read_json("resources/cleaned_ecocrop.json")

    records = []
    now = datetime.utcnow()

    print("🔄 Generating embeddings...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        try:
            text = load_rag_chunk(idx)
            embedding = get_embedding(text)
            record = {
                "item_id": idx,
                "vector": embedding,
                "rag_chunk_text": text,
                "scientific_name": row["ScientificName"],
                "event_timestamp": now
            }
            records.append(record)
        except Exception as e:
            print(f"⚠️ Skipping row {idx} due to error: {e}")
            continue

    output_df = pd.DataFrame(records)
    output_df.to_parquet(OUTPUT_PARQUET_PATH, index=False)
    print(f"✅ Saved embeddings to {OUTPUT_PARQUET_PATH}")


if __name__ == "__main__":
    main()
