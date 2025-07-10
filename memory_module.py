from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle
import time

class MemoryModule:
    def __init__(self, state_path="memory_state.pkl"): 
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # (text, embedding, mtype, keywords, timestamp, context_window, tags, source)
        self.memories = []
        self.state_path = state_path
        self.index = faiss.IndexFlatL2(384)
        self.embeddings = []
        self.keywords = []
        self.tags = []
        self.mtypes = []
        self.contexts = []
        self.sources = []
        self.timestamps = []
        self.load_state()

    def add_memory(self, text, mtype="对话", keywords=None, context_window=None, tags=None, source="对话", timestamp=None):
        emb = self.model.encode([text])[0]
        timestamp = timestamp or time.time()
        entry = (text, emb, mtype, keywords or [], timestamp, context_window or [], tags or [], source)
        self.memories.append(entry)
        self.embeddings.append(emb)
        self.keywords.append(keywords or [])
        self.tags.append(tags or [])
        self.mtypes.append(mtype)
        self.contexts.append(context_window or [])
        self.sources.append(source)
        self.timestamps.append(timestamp)
        self.index.add(np.array([emb]).astype('float32'))

    def retrieve_memories(self, query, top_k=3, context_window=None, mtype=None, tags=None):
        if not self.embeddings:
            return []
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), min(top_k*3, len(self.embeddings)))
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.memories):
                text, _, mt, kws, ts, ctx, tgs, src = self.memories[idx]
                sim_score = 1.0/(1+score)
                kw_score = 0.1 * len(set(query.split()) & set(kws))
                tag_score = 0.2 * (len(set(tags or []) & set(tgs)) if tags else 0)
                mtype_score = 0.2 if (mtype and mt == mtype) else 0
                ctx_score = 0.1 * (len(set(context_window or []) & set(ctx)) if context_window else 0)
                final_score = sim_score + kw_score + tag_score + mtype_score + ctx_score
                results.append((text, final_score, kws, tgs, mt, ts, ctx, src))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def save_state(self):
        with open(self.state_path, 'wb') as f:
            pickle.dump(self.memories, f)

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'rb') as f:
                self.memories = pickle.load(f)
            self.embeddings = [m[1] for m in self.memories]
            self.keywords = [m[3] for m in self.memories]
            self.tags = [m[6] for m in self.memories]
            self.mtypes = [m[2] for m in self.memories]
            self.contexts = [m[5] for m in self.memories]
            self.sources = [m[7] for m in self.memories]
            self.timestamps = [m[4] for m in self.memories]
            if self.embeddings:
                self.index.add(np.array(self.embeddings).astype('float32'))

    def summarize_user_habits(self, min_count=2):
        from collections import Counter
        user_texts = [m[0] for m in self.memories if m[7] == "用户输入"]
        words = []
        for t in user_texts:
            words.extend(t.split())
        common = Counter(words).most_common()
        habits = []
        for w, c in common:
            if c >= min_count and len(w) > 1:
                habits.append(f"用户常提到：{w}")
        for h in habits:
            self.add_memory(h, mtype="用户习惯", keywords=[w], tags=["习惯", "兴趣"], source="归纳")
        return habits

    def forget_memory(self, text=None, before_timestamp=None, low_score_threshold=0.2):
        # 主动遗忘指定内容或自动遗忘久远/低相关记忆
        new_memories = []
        for m in self.memories:
            m_text, _, _, _, ts, _, _, _ = m
            if text and text in m_text:
                continue  # 忘掉指定内容
            if before_timestamp and ts < before_timestamp:
                continue  # 忘掉过早内容
            new_memories.append(m)
        self.memories = new_memories
        # 重新构建索引
        self.embeddings = [m[1] for m in self.memories]
        self.index = faiss.IndexFlatL2(384)
        if self.embeddings:
            self.index.add(np.array(self.embeddings).astype('float32'))