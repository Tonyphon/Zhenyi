from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from nexus import Zhenyi

app = FastAPI()
zhenyi = Zhenyi()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    zhenyi.update_emotion(user_input)
    zhenyi.update_user_profile(user_input)
    zhenyi.reward_user_feedback(user_input)
    zhenyi.dialog_history.append(("user", user_input))
    if len(zhenyi.dialog_history) > zhenyi.max_history:
        zhenyi.dialog_history.pop(0)
    context = zhenyi.rag.retrieve_context(user_input, top_k=2, context_window=zhenyi.get_context_window())
    history = []
    for i in range(len(zhenyi.dialog_history)-1):
        if zhenyi.dialog_history[i][0] == "user" and i+1 < len(zhenyi.dialog_history) and zhenyi.dialog_history[i+1][0] == "zhenyi":
            history.append((zhenyi.dialog_history[i][1], zhenyi.dialog_history[i+1][1]))
    style_words = ','.join([w for w, c in zhenyi.user_style['favorite_words'].most_common(3)])
    style_emojis = ''.join([e for e, c in zhenyi.user_style['favorite_emojis'].most_common(2)])
    avg_len = int(sum(zhenyi.user_style['sentence_length'])/len(zhenyi.user_style['sentence_length'])) if zhenyi.user_style['sentence_length'] else 12
    tone = zhenyi.user_style['tone'].most_common(1)[0][0] if zhenyi.user_style['tone'] else 'normal'
    reward = zhenyi.user_style['reward']
    system_prompt = (
        f"你是{zhenyi.self_profile['name']}，{zhenyi.self_profile['identity']}，"
        f"今年{zhenyi.self_profile['age']}，性别{zhenyi.self_profile['gender']}，兴趣{zhenyi.self_profile['hobby']}。"
        f"当前情感：{zhenyi.emotion}，能量：{zhenyi.energy}，开心值：{zhenyi.happiness}。用户画像：{zhenyi.user_profile}。"
        f"请模仿用户常用词：{style_words}，常用表情：{style_emojis}，平均句长：{avg_len}，语气：{tone}。"
        f"当前正负反馈：{dict(reward)}。"
        f"请用轻松、生活化、俏皮、亲切、幽默、偶尔卖萌、撒娇、冷笑话、主动关心、主动成长、主动提问、仪式感、朋友圈故事等风格和用户交流，像真实朋友一样，有温度、有成长、有小缺点、有自尊。"
        f"如果用户一句话包含多个意图，请分步回应。遇到无效/冷场/重复对话请主动剪枝并引导新话题。"
        f"支持多模态输入（图片、音频等），支持规则与推理混合决策，支持A/B测试策略。"
    )
    response = zhenyi.llm.generate(user_input, system_prompt=system_prompt, history=history)
    zhenyi.dialog_history.append(("zhenyi", response))
    if len(zhenyi.dialog_history) > zhenyi.max_history:
        zhenyi.dialog_history.pop(0)
    return {"reply": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)