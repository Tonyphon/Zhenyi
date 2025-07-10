import jieba
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

class EnhancedRAGModule:
    def __init__(self, kb_path="knowledge_base.txt"):
        self.kb_path = kb_path
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.knowledge = []  # [(text, embedding, keywords)]
        self.index = faiss.IndexFlatL2(384)
        self.embeddings = []
        self.keywords = []
        self.load_knowledge()

    def load_knowledge(self):
        self.knowledge = []
        self.embeddings = []
        self.keywords = []
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                for line in f:
                    text = line.strip()
                    if text:
                        emb = self.model.encode([text])[0]
                        kws = list(jieba.cut(text))
                        self.knowledge.append((text, emb, kws))
                        self.embeddings.append(emb)
                        self.keywords.append(kws)
            if self.embeddings:
                self.index.add(np.array(self.embeddings).astype('float32'))

    def add_knowledge(self, text):
        emb = self.model.encode([text])[0]
        kws = list(jieba.cut(text))
        self.knowledge.append((text, emb, kws))
        self.embeddings.append(emb)
        self.keywords.append(kws)
        self.index.add(np.array([emb]).astype('float32'))
        with open(self.kb_path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')

    def retrieve_context(self, query, top_k=1):
        if not self.embeddings:
            return ""
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), top_k)
        for idx in I[0]:
            if idx < len(self.knowledge):
                return self.knowledge[idx][0]
        return ""