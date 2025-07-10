import sys
from memory_module import MemoryModule
from enhanced_rag_module import EnhancedRAGModule

class Zhenyi:
    def __init__(self):
        self.memory = MemoryModule()
        self.rag = EnhancedRAGModule()
        self.running = True
        print("--- 欢迎来到交互界面 ---")

    def run(self):
        while self.running:
            user_input = input("你: ").strip()
            if user_input in ["退出", "exit", "quit"]:
                print("[正在保存 真意 状态...]")
                self.memory.save_state()
                self.running = False
                continue
            elif user_input.startswith("记住："):
                fact = user_input.replace("记住：", "").strip()
                self.rag.add_knowledge(fact)
                print("真意: 好的，我的向导。这个知识我已经记在我的知识库里了。")
            elif user_input.startswith("回忆关于："):
                query = user_input.replace("回忆关于：", "").strip()
                memories = self.memory.retrieve_memories(query)
                if memories:
                    print("真意: 以下是我的相关记忆：")
                    for i, (text, score, keywords) in enumerate(memories, 1):
                        print(f"记忆 {i} (相关度: {score:.2f}): \"{text}\" [匹配关键词: {', '.join(keywords)}]")
                else:
                    print("真意: 没有找到相关记忆。")
            else:
                context = self.rag.retrieve_context(user_input)
                response = self.generate_response(user_input, context)
                print(f"真意: {response}")

    def generate_response(self, user_input, context):
        # 这里应集成本地大模型（如Qwen），结合RAG上下文生成回复
        # 示例返回：
        if context:
            return f"根据我的记忆，{context}"
        return "你好，我的向导。我能为你做些什么？"

if __name__ == "__main__":
    zhenyi = Zhenyi()
    zhenyi.run()