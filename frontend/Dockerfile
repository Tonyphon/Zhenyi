# 前端 Dockerfile
FROM node:20-slim
WORKDIR /app
COPY . /app
RUN npm install
CMD ["npx", "electron", "."]