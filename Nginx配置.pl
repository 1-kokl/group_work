worker_processes  1;
events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    # 你的项目服务
    server {
        listen 80;
        server_name localhost;

        # ================== 前端（你的 group_work 仓库） ==================
        root /https://github.com/1-kokl/group_work.git;
        index index.html;

        # 解决单页面路由刷新404
        try_files $uri $uri/ /index.html;

        # ================== 后端接口代理 ==================
        # 所有 /api 开头的请求，自动转发给后端服务
        location /api/ {
            proxy_pass http://127.0.0.1:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}