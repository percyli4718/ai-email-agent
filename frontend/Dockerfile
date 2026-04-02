# AI Email Agent Frontend - Dockerfile
# 生产环境前端容器镜像 - 多阶段构建

# ==================== 阶段 1: 构建 ====================
FROM node:20-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --only=production && \
    npm cache clean --force

# 复制源代码
COPY frontend/ ./

# 构建应用
RUN npm run build

# ==================== 阶段 2: 生产环境 ====================
FROM nginx:alpine

# 复制自定义 nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
