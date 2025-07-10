# Frosted Glass Chatbot (Electron)

## Setup

1. 安装依赖  
   ```
   npm install
   ```

2. 启动应用  
   ```
   npm start
   ```

3. 配置后端  
   - 默认请求 `http://localhost:8000/chat`，如需更改请修改 `renderer.js` 里的 fetch 地址。

## 说明

- 独立桌面窗口，无需浏览器
- 毛玻璃背景、圆角、现代极简风格
- 支持窗口拖动、最小化、关闭
- 聊天气泡自适应宽度，渐变、阴影
- 输入框支持回车发送，自动聚焦
- 消息发送后立即请求后端，无模拟延迟