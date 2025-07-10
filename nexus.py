import sys
from memory_module import MemoryModule
from enhanced_rag_module import EnhancedRAGModule

class Zhenyi:
    def __init__(self):
        self.memory = MemoryModule()
        self.rag = EnhancedRAGModule()
        self.running = True
        self.emotion = "中性"  # 新增：情感状态
        print("--- 欢迎来到交互界面 ---")

    def update_emotion(self, user_input):
        # 简单情感分析：根据关键词调整情感
        happy_words = ["开心", "高兴", "快乐", "谢谢", "赞"]
        sad_words = ["难过", "伤心", "失落", "沮丧", "烦"]
        angry_words = ["生气", "愤怒", "气愤"]
        for w in happy_words:
            if w in user_input:
                self.emotion = "愉快"
                return
        for w in sad_words:
            if w in user_input:
                self.emotion = "低落"
                return
        for w in angry_words:
            if w in user_input:
                self.emotion = "愤怒"
                return
        self.emotion = "中性"

    def run(self):
        while self.running:
            user_input = input("你: ").strip()
            self.update_emotion(user_input)  # 新增：每次输入后更新情感
            if user_input in ["退出", "exit", "quit"]:
                print(f"[正在保存 真意 状态... 当前情感：{self.emotion}]")
                self.memory.save_state()
                self.running = False
                continue
            elif user_input.startswith("记住："):
                fact = user_input.replace("记住：", "").strip()
                self.rag.add_knowledge(fact)
                print(f"真意({self.emotion}): 好的，我的向导。这个知识我已经记在我的知识库里了。")
            elif user_input.startswith("回忆关于："):
                query = user_input.replace("回忆关于：", "").strip()
                memories = self.memory.retrieve_memories(query)
                if memories:
                    print(f"真意({self.emotion}): 以下是我的相关记忆：")
                    for i, (text, score, keywords) in enumerate(memories, 1):
                        print(f"记忆 {i} (相关度: {score:.2f}): \"{text}\" [匹配关键词: {', '.join(keywords)}]")
                else:
                    print(f"真意({self.emotion}): 没有找到相关记忆。")
            else:
                context = self.rag.retrieve_context(user_input)
                response = self.generate_response(user_input, context)
                print(f"真意({self.emotion}): {response}")

    def generate_response(self, user_input, context):
        # 情感化回复示例
        if context:
            if self.emotion == "愉快":
                return f"很高兴和你分享：{context}"
            elif self.emotion == "低落":
                return f"虽然有点低落，但我记得：{context}"
            elif self.emotion == "愤怒":
                return f"有些气愤，但还是告诉你：{context}"
            else:
                return f"根据我的记忆，{context}"
        # 无上下文时的情感化欢迎语
        if self.emotion == "愉快":
            return "你好呀！今天感觉很棒，有什么可以帮你的吗？"
        elif self.emotion == "低落":
            return "有点低落，但我依然在这里陪伴你。"
        elif self.emotion == "愤怒":
            return "现在有点生气，不过我会尽力帮你。"
        return "你好，我的向导。我能为你做些什么？"

if __name__ == "__main__":
    zhenyi = Zhenyi()
    zhenyi.run()