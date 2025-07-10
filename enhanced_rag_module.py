import jieba
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import time

class EnhancedRAGModule:
    def __init__(self, kb_path="knowledge_base.txt"):
        self.kb_path = kb_path
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # (text, embedding, keywords, tags, context_window, source)
        self.knowledge = []
        self.index = faiss.IndexFlatL2(384)
        self.embeddings = []
        self.keywords = []
        self.tags = []
        self.contexts = []
        self.sources = []
        self.growth_log = []  # 新增：成长日志
        self.load_knowledge()

    def load_knowledge(self):
        self.knowledge = []
        self.embeddings = []
        self.keywords = []
        self.tags = []
        self.contexts = []
        self.sources = []
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                for line in f:
                    text = line.strip()
                    if text:
                        emb = self.model.encode([text])[0]
                        kws = list(jieba.cut(text))
                        # 简单标签和上下文自动生成
                        tags = []
                        context_window = []
                        source = "知识库"
                        self.knowledge.append((text, emb, kws, tags, context_window, source))
                        self.embeddings.append(emb)
                        self.keywords.append(kws)
                        self.tags.append(tags)
                        self.contexts.append(context_window)
                        self.sources.append(source)
            if self.embeddings:
                self.index.add(np.array(self.embeddings).astype('float32'))

    def add_knowledge(self, text, auto=False, tags=None, context_window=None, source="知识库"):
        # auto=True时避免重复写入
        if auto and any(text == k[0] for k in self.knowledge):
            return
        emb = self.model.encode([text])[0]
        kws = list(jieba.cut(text))
        tags = tags or []
        context_window = context_window or []
        self.knowledge.append((text, emb, kws, tags, context_window, source))
        self.embeddings.append(emb)
        self.keywords.append(kws)
        self.tags.append(tags)
        self.contexts.append(context_window)
        self.sources.append(source)
        with open(self.kb_path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
        self.index.add(np.array([emb]).astype('float32'))

    def retrieve_context(self, query, top_k=1, context_window=None, tags=None):
        # 语义+关键词+上下文+标签多重模糊检索，返回最相关的top_k条知识文本
        if not self.embeddings:
            return ""
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), min(top_k*3, len(self.embeddings)))
        query_words = set(jieba.cut(query))
        scored = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.knowledge):
                text, _, kws, tgs, ctx, src = self.knowledge[idx]
                kw_overlap = len(query_words & set(kws))
                tag_score = 0.2 * (len(set(tags or []) & set(tgs)) if tags else 0)
                ctx_score = 0.1 * (len(set(context_window or []) & set(ctx)) if context_window else 0)
                final_score = 1.0/(1+score) + 0.1*kw_overlap + tag_score + ctx_score
                scored.append((text, final_score))
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            return "；".join([s[0] for s in scored[:top_k]])
        return ""

    def retrieve_fuzzy_memories(self, query, top_k=3, context_window=None, tags=None):
        # 返回模糊相关的多条知识，含相关度、关键词、标签、上下文
        if not self.embeddings:
            return []
        q_emb = self.model.encode([query])[0]
        D, I = self.index.search(np.array([q_emb]).astype('float32'), min(top_k*3, len(self.embeddings)))
        query_words = set(jieba.cut(query))
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.knowledge):
                text, _, kws, tgs, ctx, src = self.knowledge[idx]
                kw_overlap = len(query_words & set(kws))
                tag_score = 0.2 * (len(set(tags or []) & set(tgs)) if tags else 0)
                ctx_score = 0.1 * (len(set(context_window or []) & set(ctx)) if context_window else 0)
                final_score = 1.0/(1+score) + 0.1*kw_overlap + tag_score + ctx_score
                results.append((text, final_score, list(set(kws) & query_words), tgs, ctx, src))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def log_growth(self, event):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.growth_log.append(f"[{ts}] {event}")
        if len(self.growth_log) > 20:
            self.growth_log.pop(0)

    def summarize_knowledge(self):
        # 简单自我归纳知识库内容
        summary = f"当前知识条目数：{len(self.knowledge)}。主要主题："
        all_words = []
        for k in self.knowledge:
            all_words.extend(k[2])
        from collections import Counter
        top_words = [w for w, c in Counter(all_words).most_common(5)]
        summary += ", ".join(top_words)
        self.log_growth(f"知识自我归纳：{summary}")
        return summary