from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from feast import FeatureStore

EMBEDDING_ENDPOINT = "https://models.mylab.th-luebeck.dev/v1/embeddings"
MODEL = "bge-m3"
FEAST_REPO_PATH = "feature_repo"
EMBEDDING_DIM = 1024

store = FeatureStore(repo_path=FEAST_REPO_PATH)

def _embed_text(text):
    response = requests.post(
        EMBEDDING_ENDPOINT,
        json={"input": [text], "model": MODEL}
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def get_rag_router() -> APIRouter:
    router = APIRouter()

    class QueryRequest(BaseModel):
        question: str
        top_k: int = 3

    @router.post("/query")
    def query_rag(req: QueryRequest):
        # Embed text using BGE-M3 remote model
        embedding = _embed_text(req.question)

        if not embedding or len(embedding) != EMBEDDING_DIM:
            raise HTTPException(status_code=500, detail="Invalid embedding returned")

        result_df = store.retrieve_online_documents_v2(
            features=[
                "ecocrop_embeddings:vector",
                "ecocrop_embeddings:scientific_name",
                "ecocrop_embeddings:rag_chunk_text",
            ],
            query=embedding,
            top_k=req.top_k,
            distance_metric="COSINE",
        ).to_df()

        return {
            "question": req.question,
            "results": result_df.to_dict(orient="records"),
        }

    return router

