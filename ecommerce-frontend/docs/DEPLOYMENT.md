## 部署指南

### 1. 开发环境

1. 克隆项目并安装依赖：
   ```bash
   npm install
   cp config/environment.example .env.local
   ```
2. 根据后端配置调整 `.env.local`，常用变量：
   ```ini
   VUE_APP_API_BASE_URL=http://localhost:5000
   VUE_APP_USE_MSW=false
   ```
3. 启动本地开发：
   ```bash
   npm run serve
   ```
4. 如需 mock 后端，执行：
   ```bash
   npm run serve:mock
   ```

### 2. 生产构建

```bash
npm run build
```

产物位于 `dist/` 目录，包含已压缩的 JS/CSS/HTML。部署至任意静态文件服务（如 Nginx、OSS、Netlify）。

#### Nginx 示例配置

```nginx
server {
  listen 80;
  server_name your-domain.com;

  root /var/www/ecommerce-frontend/dist;
  index index.html;

  location /api/ {
    proxy_pass http://backend:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

### 3. Docker 容器化（可选）

`docker/Dockerfile` 示例：

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --frozen-lockfile
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

如需多容器调试，可使用 `docker-compose.yml`：

```yaml
version: '3.9'
services:
  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8080:80"
    environment:
      - VUE_APP_API_BASE_URL=http://backend:5000
    depends_on:
      - backend
  backend:
    image: your-backend-image
    ports:
      - "5000:5000"
```

### 4. CI/CD（GitHub Actions）

`.github/workflows/ci.yml` 步骤：

1. Checkout + 缓存依赖
2. `npm run lint`
3. `npm run test:unit` / `npm run test:api` / `npm run test:e2e`
4. 生产构建并上传 artifact

可在后续添加如下步骤实现自动部署：

```yaml
- name: Deploy to OSS
  run: npm run deploy
  env:
    OSS_BUCKET: ${{ secrets.OSS_BUCKET }}
    OSS_KEY: ${{ secrets.OSS_KEY }}
```

若使用其他平台（如 GitLab CI、Jenkins），可参考上述步骤调整。

### 5. 运维建议

- 启用 Nginx/Gateway 的 Gzip 与 Brotli 压缩。
- 设置缓存策略：`/js` 和 `/css` 使用较长 `max-age`，`index.html` 使用 `no-cache`。
- 结合后端日志分析，定期回归测试关键流程（登录、下单、个人中心等）。


