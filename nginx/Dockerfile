# Nginx Dockerfile - 用于托管前端静态文件和反向代理后端服务
FROM nginx:alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义Nginx配置
COPY nginx.conf /etc/nginx/conf.d/qiushui.conf

# 复制前端构建产物 (由build.sh编译并复制过来)
COPY frontend/ /usr/share/nginx/html/

# 创建必要的目录并设置权限
RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp \
    /var/log/nginx \
    /var/run/nginx \
    /run && \
    chown -R nginx:nginx /usr/share/nginx/html \
    /var/cache/nginx \
    /var/log/nginx \
    /var/run/nginx \
    /run \
    /etc/nginx/conf.d && \
    chmod -R 755 /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 使用root用户运行以确保有足够权限
# USER nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Nginx将在前台运行
CMD ["nginx", "-g", "daemon off;"]
