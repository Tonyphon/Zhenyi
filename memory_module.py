from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

class MemoryModule:
    def __init__(self, state_path="memory_state.pkl"): 
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.memories = []  # [(text, embedding, type, keywords)]
        self.state_path = state_path
        self.index = faiss.IndexFlatL2(384)
        self.embeddings = []
        self.keywords = []
        self.load_state()

    def add_memory(self, text, mtype="对话", keywords=None):
        emb = self.model.encode([text])[0]
        self.memories.append((text, emb, mtype, keywords or []))
        self.embeddings.append(emb)
        self.keywords.append(keywords or [])
        self.index.add(np.array([emb]).astype('float32'))

    def retrieve_memories(self, query, top_k=3):
        if not self.embeddings:
            return []
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), top_k)
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.memories):
                text, _, _, keywords = self.memories[idx]
                results.append((text, 1.0/(1+score), keywords))
        return results

    def save_state(self):
        with open(self.state_path, 'wb') as f:
            pickle.dump(self.memories, f)

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'rb') as f:
                self.memories = pickle.load(f)
            self.embeddings = [m[1] for m in self.memories]
            self.keywords = [m[3] for m in self.memories]
            if self.embeddings:
                self.index.add(np.array(self.embeddings).astype('float32'))