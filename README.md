# Zhenyi Desktop (前后端一体桌面智能体)

## 目录结构

- backend/   —— Python 智能体后端（含API服务）
- frontend/  —— Electron 桌面聊天前端
- start.sh   —— 一键启动脚本

## 运行方式

1. 安装 Python 依赖（首次运行）
   ```
   cd backend
   pip install -r requirements.txt
   ```
2. 安装前端依赖（首次运行）
   ```
   cd ../frontend
   npm install
   ```
3. 一键启动（自动启动后端API+前端桌面窗口）
   ```
   cd ..
   bash start.sh
   ```

## 说明
- Electron 前端自动请求本地后端 http://localhost:8000/chat
- 后端API基于 FastAPI，主逻辑复用原有 zhenyi 智能体
- 支持窗口拖动、毛玻璃、圆角、现代极简风格
- 适合二次开发和打包为桌面应用
