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

    def add_knowledge(self, text, auto=False):
        # auto=True时避免重复写入
        if auto and any(text == k[0] for k in self.knowledge):
            return
        emb = self.model.encode([text])[0]
        kws = list(jieba.cut(text))
        self.knowledge.append((text, emb, kws))
        self.embeddings.append(emb)
        self.keywords.append(kws)
        self.index.add(np.array([emb]).astype('float32'))
        with open(self.kb_path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')

    def retrieve_context(self, query, top_k=1):
        # 语义+关键词双重模糊检索，返回最相关的top_k条知识文本
        if not self.embeddings:
            return ""
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), min(top_k, len(self.embeddings)))
        # 关键词匹配分数
        query_words = set(jieba.cut(query))
        scored = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.knowledge):
                text, _, kws = self.knowledge[idx]
                kw_overlap = len(query_words & set(kws))
                final_score = 1.0/(1+score) + 0.1*kw_overlap
                scored.append((text, final_score))
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            return "；".join([s[0] for s in scored[:top_k]])
        return ""

    def retrieve_fuzzy_memories(self, query, top_k=3):
        # 返回模糊相关的多条知识，含相关度和关键词
        if not self.embeddings:
            return []
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), min(top_k, len(self.embeddings)))
        query_words = set(jieba.cut(query))
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.knowledge):
                text, _, kws = self.knowledge[idx]
                kw_overlap = len(query_words & set(kws))
                final_score = 1.0/(1+score) + 0.1*kw_overlap
                results.append((text, final_score, list(set(kws) & query_words)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]