from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
from api.config import settings

COLLECTION = "pois_fr"

class POIIndex:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.model = SentenceTransformer(settings.EMBED_MODEL)
        self._ensure_collection()

    def _ensure_collection(self):
        dim = self.model.get_sentence_embedding_dimension()
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION not in collections:
            self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )

    def seed_from_jsonl(self, path: str):
        points = []
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                rec = json.loads(line)
                text = f"{rec['name']} {rec['city']} {' '.join(rec['tags'])}"
                emb = self.model.encode(text).tolist()
                points.append(PointStruct(id=idx+1, vector=emb, payload=rec))
        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)

    def search(self, query: str, city: str, top_k: int = 8):
        qvec = self.model.encode(query).tolist()
        res = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=top_k,
            query_filter={"must": [{"key": "city", "match": {"value": city}}]},
        )
        return [hit.payload for hit in res]