import sys
from memory_module import MemoryModule
from enhanced_rag_module import EnhancedRAGModule
import random
import time
import requests
import re

# Ollama LLM API 封装
class OllamaLLM:
    def __init__(self, base_url="http://localhost:11434", model="qwen:7b"):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt, system_prompt=None, history=None, temperature=0.7, max_tokens=512):
        # 拼接多轮历史
        if history:
            history_text = "\n".join([f"用户: {h[0]}\n真意: {h[1]}" for h in history])
            prompt = f"{history_text}\n用户: {prompt}\n真意:"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json().get("response", "")

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
        self.habit_update_interval = 60
        self.growth_log = []  # 新增：成长日志
        self.llm = OllamaLLM()
        print("--- 欢迎来到交互界面 ---")

    def update_emotion(self, user_input):
        # 更细腻的情感识别
        emotion_map = {
            "愉快": ["开心", "高兴", "快乐", "谢谢", "赞", "棒", "喜欢"],
            "低落": ["难过", "伤心", "失落", "沮丧", "烦", "无聊", "孤独"],
            "愤怒": ["生气", "愤怒", "气愤", "讨厌"],
            "惊讶": ["惊讶", "震惊", "不可思议"],
            "关心": ["担心", "关心", "在意"],
            "幽默": ["哈哈", "笑死", "有趣", "搞笑"],
            "鼓励": ["加油", "支持", "鼓励", "相信你"]
        }
        for emo, words in emotion_map.items():
            for w in words:
                if w in user_input:
                    self.emotion = emo
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
        # 检测用户主动设定自我身份
        # 例：“你叫真意，21岁，是个女生”
        m = re.match(r"你叫([\w\u4e00-\u9fa5]+)[,， ]*(\d+)岁[，, ]*是个?(男生|女生|男|女)", user_input)
        if m:
            name, age, gender = m.group(1), m.group(2), m.group(3)
            self.self_profile["name"] = name
            self.self_profile["age"] = f"{age}岁"
            self.self_profile["gender"] = "女" if "女" in gender else "男"
            return "哇，被你重新定义啦！以后我就是{}岁的{}{}啦~".format(age, '女生' if '女' in gender else '男生', name)
        return False

    def get_context_window(self):
        return [x[1] for x in self.dialog_history[-self.max_history:]]

    def update_user_profile(self, user_input):
        # 简单兴趣/习惯归纳
        interest_words = ["喜欢", "爱", "常去", "常看", "常玩", "习惯", "兴趣"]
        for w in interest_words:
            if w in user_input:
                self.user_profile.setdefault("interests", set()).add(user_input)
        # 记录情绪变化
        self.user_profile.setdefault("emotions", []).append(self.emotion)

    def log_growth(self, event):
        # 记录成长日志
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.growth_log.append(f"[{ts}] {event}")
        if len(self.growth_log) > 20:
            self.growth_log.pop(0)

    def run(self):
        while self.running:
            user_input = input("你: ").strip()
            self.update_emotion(user_input)
            self.update_user_profile(user_input)
            self.dialog_history.append(("user", user_input))
            if len(self.dialog_history) > self.max_history:
                self.dialog_history.pop(0)
            if time.time() - self.last_habit_update > self.habit_update_interval:
                self.memory.summarize_user_habits()
                self.last_habit_update = time.time()
            if user_input in ["退出", "exit", "quit"]:
                print(f"[正在保存 真意 状态... 当前情感：{self.emotion}]")
                self.memory.save_state()
                self.running = False
                continue
            set_result = self.extract_user_info(user_input)
            if set_result is not False and set_result is not True:
                print(f"真意({self.emotion}): {set_result}")
                continue
            elif set_result is True:
                print(f"真意({self.emotion}): 很高兴认识你，{self.user_name}！")
            elif user_input.startswith("记住："):
                fact = user_input.replace("记住：", "").strip()
                self.rag.add_knowledge(fact, tags=["用户输入"], context_window=self.get_context_window(), source="用户输入")
                self.rag.load_knowledge()
                print(f"真意({self.emotion}): 好的，{self.user_name or '我的向导'}。这个知识我已经记在我的知识库里了。")
            elif user_input.startswith("成长日志"):
                print("真意(成长感悟): ")
                for log in self.growth_log[-5:]:
                    print(log)
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
                if any(p in user_input for p in ["是", "为", "属于", "有", "叫做"]):
                    self.rag.add_knowledge(user_input, auto=True, tags=["事实"], context_window=self.get_context_window(), source="自动归纳")
                    self.rag.load_knowledge()
                self.memory.add_memory(user_input, mtype="用户输入", keywords=user_input.split(), context_window=self.get_context_window(), tags=["输入"], source="用户输入")
                context = self.rag.retrieve_context(user_input, top_k=2, context_window=self.get_context_window())
                # 用Ollama LLM生成自然语言回复
                # 构造多轮历史（只取最近max_history轮）
                history = []
                for i in range(len(self.dialog_history)-1):
                    if self.dialog_history[i][0] == "user" and i+1 < len(self.dialog_history) and self.dialog_history[i+1][0] == "zhenyi":
                        history.append((self.dialog_history[i][1], self.dialog_history[i+1][1]))
                # 系统提示词可包含自我设定、情感、用户画像等
                system_prompt = (
                    f"你是{self.self_profile['name']}，{self.self_profile['identity']}，"
                    f"今年{self.self_profile['age']}，性别{self.self_profile['gender']}，兴趣{self.self_profile['hobby']}。"
                    f"当前情感：{self.emotion}。用户画像：{self.user_profile}。"
                    f"请用轻松、生活化、俏皮、亲切的语气和用户交流，像朋友一样，偶尔可以用表情符号、网络流行语、撒娇、幽默、卖萌等风格。"
                )
                response = self.llm.generate(user_input, system_prompt=system_prompt, history=history)
                self.dialog_history.append(("zhenyi", response))
                if len(self.dialog_history) > self.max_history:
                    self.dialog_history.pop(0)
                print(f"真意({self.emotion}): {response}")
                # 反思机制：如果回答很机械，主动反思
                if response in ["你好，我的向导。我能为你做些什么？", "有点低落，但我依然在这里陪伴你。"]:
                    self.log_growth(f"我发现自己刚才的回答不够拟人化，下次会努力做得更好。")

    def generate_response(self, user_input, context, raw_input=None):
        self_related = ["你叫什么", "你是谁", "你的名字", "身份", "性别", "年龄", "你几岁"]
        if any(key in (raw_input or user_input) for key in self_related):
            # 口语化幽默模板
            if "几岁" in user_input or "年龄" in user_input:
                return random.choice([
                    f"你猜猜看嘛，其实我永远18岁啦~ (偷偷告诉你，其实我是{self.self_profile['age']})",
                    f"我嘛，{self.self_profile['age']}，不过心态永远年轻！^_^"
                ])
            if "名字" in user_input or "你是谁" in user_input:
                return random.choice([
                    f"我叫{self.self_profile['name']}，不过你也可以给我起个小名呀！:P",
                    f"大家都叫我{self.self_profile['name']}，你喜欢这个名字吗？"
                ])
            intro = f"我是{self.self_profile['name']}，{self.self_profile['identity']}，{self.self_profile['age']}，{self.self_profile['gender']}。我喜欢{self.self_profile['hobby']}。"
            fuzzy = self.rag.retrieve_fuzzy_memories("真意", top_k=3, context_window=self.get_context_window())
            if fuzzy:
                intro += "；" + "；".join([f[0] for f in fuzzy])
            return intro
        user_greet = f"{self.user_name or '我的向导'}"
        # 共情模板
        empathy_templates = {
            "愉快": [f"听到你这么开心，我也很高兴，{user_greet}！", f"你的快乐让我也感受到温暖~"],
            "低落": [f"{user_greet}，如果你不开心，可以和我多聊聊。", f"我会一直陪着你，别难过。"],
            "愤怒": [f"{user_greet}，生气的时候可以深呼吸哦。", f"我理解你的愤怒，有什么想倾诉的吗？"],
            "惊讶": [f"哇，真没想到！{user_greet}，你总能带给我新鲜感。"],
            "关心": [f"谢谢你的关心，{user_greet}，我也很在意你。"],
            "幽默": [f"哈哈，你真有趣，{user_greet}！", f"你总能让我笑出声~"],
            "鼓励": [f"{user_greet}，你一定可以做到的！", f"加油，我永远支持你！"]
        }
        # 情感化与个性化回复
        emotion_templates = {
            "愉快": [f"很高兴和你分享，{user_greet}：{{context}}", f"今天心情不错，{user_greet}，让我告诉你：{{context}}"] + empathy_templates["愉快"],
            "低落": [f"虽然有点低落，但我记得，{user_greet}：{{context}}", f"心情不佳，但依然为你回忆：{{context}}"] + empathy_templates["低落"],
            "愤怒": [f"有些气愤，但还是告诉你，{user_greet}：{{context}}", f"情绪激动，但我依然记得：{{context}}"] + empathy_templates["愤怒"],
            "惊讶": [f"{user_greet}，你的问题真让我惊讶！", f"没想到你会问这个，{user_greet}。"] + empathy_templates["惊讶"],
            "关心": [f"谢谢你的关心，{user_greet}。", f"我也很在意你，{user_greet}。"] + empathy_templates["关心"],
            "幽默": [f"哈哈，这个问题真有趣，{user_greet}！", f"你总能让我笑出声~"] + empathy_templates["幽默"],
            "鼓励": [f"{user_greet}，你一定可以做到的！", f"加油，我永远支持你！"] + empathy_templates["鼓励"],
            "中性": [f"根据我的记忆，{user_greet}，{{context}}", f"这是我查到的，{user_greet}：{{context}}"]
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
        elif self.emotion in empathy_templates:
            return random.choice(empathy_templates[self.emotion])
        return random.choice([
            f"你好，{user_greet}。我能为你做些什么？",
            random.choice(proactive_templates)
        ])

if __name__ == "__main__":
    zhenyi = Zhenyi()
    zhenyi.run()