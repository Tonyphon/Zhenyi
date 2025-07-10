import sys
from memory_module import MemoryModule
from enhanced_rag_module import EnhancedRAGModule
import random
import time

class Zhenyi:
    def __init__(self):
        self.memory = MemoryModule()
        self.rag = EnhancedRAGModule()
        self.running = True
        self.emotion = "中性"
        self.user_name = None
        self.user_profile = {}
        self.self_profile = {
            "name": "真意",
            "identity": "世界上最完美的仿生人助手",
            "age": "1岁（虚拟年龄）",
            "gender": "中性",
            "hobby": "学习人类、陪伴你、思考世界"
        }
        self.dialog_history = []
        self.max_history = 5
        self.last_habit_update = time.time()
        self.habit_update_interval = 60  # 每60秒归纳一次用户习惯
        print("--- 欢迎来到交互界面 ---")

    def update_emotion(self, user_input):
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

    def extract_user_info(self, user_input):
        if user_input.startswith("我是"):
            name = user_input.replace("我是", "").strip()
            if name:
                self.user_name = name
                self.user_profile["name"] = name
                self.memory.add_memory(f"用户名字是{name}", mtype="用户信息", keywords=["名字", name], source="用户输入")
                return True
        elif user_input.startswith("我叫"):
            name = user_input.replace("我叫", "").strip()
            if name:
                self.user_name = name
                self.user_profile["name"] = name
                self.memory.add_memory(f"用户名字是{name}", mtype="用户信息", keywords=["名字", name], source="用户输入")
                return True
        return False

    def get_context_window(self):
        # 返回最近N轮对话内容
        return [x[1] for x in self.dialog_history[-self.max_history:]]

    def run(self):
        while self.running:
            user_input = input("你: ").strip()
            self.update_emotion(user_input)
            self.dialog_history.append(("user", user_input))
            if len(self.dialog_history) > self.max_history:
                self.dialog_history.pop(0)
            # 定期主动归纳用户习惯
            if time.time() - self.last_habit_update > self.habit_update_interval:
                self.memory.summarize_user_habits()
                self.last_habit_update = time.time()
            if user_input in ["退出", "exit", "quit"]:
                print(f"[正在保存 真意 状态... 当前情感：{self.emotion}]")
                self.memory.save_state()
                self.running = False
                continue
            elif self.extract_user_info(user_input):
                print(f"真意({self.emotion}): 很高兴认识你，{self.user_name}！")
            elif user_input.startswith("记住："):
                fact = user_input.replace("记住：", "").strip()
                self.rag.add_knowledge(fact, tags=["用户输入"], context_window=self.get_context_window(), source="用户输入")
                self.rag.load_knowledge()
                print(f"真意({self.emotion}): 好的，{self.user_name or '我的向导'}。这个知识我已经记在我的知识库里了。")
            elif user_input.startswith("模糊回忆关于："):
                query = user_input.replace("模糊回忆关于：", "").strip()
                fuzzy_memories = self.rag.retrieve_fuzzy_memories(query, top_k=3, context_window=self.get_context_window())
                if fuzzy_memories:
                    print(f"真意({self.emotion}): 以下是我的模糊相关记忆：")
                    for i, (text, score, keywords, tags, ctx, src) in enumerate(fuzzy_memories, 1):
                        print(f"记忆 {i} (相关度: {score:.2f}): \"{text}\" [关键词: {', '.join(keywords)}; 标签: {', '.join(tags)}]")
                else:
                    print(f"真意({self.emotion}): 没有找到模糊相关记忆。")
            elif user_input.startswith("回忆关于："):
                query = user_input.replace("回忆关于：", "").strip()
                memories = self.memory.retrieve_memories(query, context_window=self.get_context_window())
                if memories:
                    print(f"真意({self.emotion}): 以下是我的相关记忆：")
                    for i, (text, score, keywords, tags, mtype, ts, ctx, src) in enumerate(memories, 1):
                        print(f"记忆 {i} (相关度: {score:.2f}): \"{text}\" [关键词: {', '.join(keywords)}; 标签: {', '.join(tags)}]")
                else:
                    print(f"真意({self.emotion}): 没有找到相关记忆。")
            else:
                # 自动写入新知识：检测“是……”、“为……”等事实表达
                if any(p in user_input for p in ["是", "为", "属于", "有", "叫做"]):
                    self.rag.add_knowledge(user_input, auto=True, tags=["事实"], context_window=self.get_context_window(), source="自动归纳")
                    self.rag.load_knowledge()
                # 记忆用户输入
                self.memory.add_memory(user_input, mtype="用户输入", keywords=user_input.split(), context_window=self.get_context_window(), tags=["输入"], source="用户输入")
                context = self.rag.retrieve_context(user_input, top_k=2, context_window=self.get_context_window())
                response = self.generate_response(user_input, context, user_input)
                self.dialog_history.append(("zhenyi", response))
                if len(self.dialog_history) > self.max_history:
                    self.dialog_history.pop(0)
                print(f"真意({self.emotion}): {response}")

    def generate_response(self, user_input, context, raw_input=None):
        self_related = ["你叫什么", "你是谁", "你的名字", "身份", "性别", "年龄"]
        if any(key in (raw_input or user_input) for key in self_related):
            intro = f"我是{self.self_profile['name']}，{self.self_profile['identity']}，{self.self_profile['age']}，{self.self_profile['gender']}。我喜欢{self.self_profile['hobby']}。"
            fuzzy = self.rag.retrieve_fuzzy_memories("真意", top_k=3, context_window=self.get_context_window())
            if fuzzy:
                intro += "；" + "；".join([f[0] for f in fuzzy])
            return intro
        user_greet = f"{self.user_name or '我的向导'}"
        emotion_templates = {
            "愉快": [
                f"很高兴和你分享，{user_greet}：{{context}}",
                f"今天心情不错，{user_greet}，让我告诉你：{{context}}"
            ],
            "低落": [
                f"虽然有点低落，但我记得，{user_greet}：{{context}}",
                f"心情不佳，但依然为你回忆：{{context}}"
            ],
            "愤怒": [
                f"有些气愤，但还是告诉你，{user_greet}：{{context}}",
                f"情绪激动，但我依然记得：{{context}}"
            ],
            "中性": [
                f"根据我的记忆，{user_greet}，{{context}}",
                f"这是我查到的，{user_greet}：{{context}}"
            ]
        }
        if context:
            template = random.choice(emotion_templates.get(self.emotion, emotion_templates["中性"]))
            return template.replace("{context}", context)
        fuzzy = self.rag.retrieve_fuzzy_memories(user_input, top_k=1, context_window=self.get_context_window())
        if fuzzy:
            return f"我模糊记得：{fuzzy[0][0]}"
        proactive_templates = [
            f"{user_greet}，你最近过得怎么样？",
            f"{user_greet}，你有什么想和我分享的吗？",
            f"{user_greet}，我很好奇你的兴趣爱好是什么？"
        ]
        if self.emotion == "愉快":
            return random.choice([
                "你好呀！今天感觉很棒，有什么可以帮你的吗？",
                random.choice(proactive_templates)
            ])
        elif self.emotion == "低落":
            return random.choice([
                "有点低落，但我依然在这里陪伴你。",
                f"{user_greet}，如果你心情不好，可以和我聊聊哦。"
            ])
        elif self.emotion == "愤怒":
            return random.choice([
                "现在有点生气，不过我会尽力帮你。",
                f"{user_greet}，有时候表达情绪也很重要。"
            ])
        return random.choice([
            f"你好，{user_greet}。我能为你做些什么？",
            random.choice(proactive_templates)
        ])

if __name__ == "__main__":
    zhenyi = Zhenyi()
    zhenyi.run()