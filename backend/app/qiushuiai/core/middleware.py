"""
核心中间件

提供API请求日志记录、性能监控、安全审计等功能，包括：
- 请求/响应日志记录
- 执行时间监控
- 错误跟踪
- 安全事件记录
- 限流和熔断
- 数据脱敏
"""

import time
import uuid
import json
import traceback
from typing import Any, Dict, List, Optional, Set, Callable
from urllib.parse import parse_qs
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings
from .logging import (
    get_logger,
    set_request_context,
    clear_request_context,
    LogType,
    SensitiveDataFilter
)
from .exceptions import handle_api_exception


class RequestLoggingConfig:
    """请求日志配置"""
    
    def __init__(
        self,
        log_requests: bool = True,
        log_responses: bool = True,
        log_headers: bool = False,
        log_query_params: bool = True,
        log_path_params: bool = True,
        log_body: bool = True,
        max_body_size: int = settings.MAX_BODY_SIZE,
        exclude_paths: Optional[Set[str]] = None,
        exclude_methods: Optional[Set[str]] = None,
        sensitive_fields: Optional[List[str]] = None,
        slow_request_threshold: float = settings.SLOW_REQUEST_THRESHOLD
    ):
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_headers = log_headers
        self.log_query_params = log_query_params
        self.log_path_params = log_path_params
        self.log_body = log_body
        self.max_body_size = max_body_size
        self.exclude_paths = exclude_paths or {"/api/v1/health", "/metrics", "/docs", "/openapi.json"}
        self.exclude_methods = exclude_methods or {"OPTIONS"}
        self.sensitive_fields = sensitive_fields or [
            "password", "token", "secret", "key", "authorization", 
            "cookie", "session", "csrf"
        ]
        self.slow_request_threshold = slow_request_threshold


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        config: Optional[RequestLoggingConfig] = None
    ):
        super().__init__(app)
        self.config = config or RequestLoggingConfig()
        self.logger = get_logger()
        self.filter = SensitiveDataFilter(
            self.config.sensitive_fields,
            max_length=self.config.max_body_size
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否需要跳过日志记录
        if self._should_skip_logging(request):
            return await call_next(request)
        
        # 生成请求ID并设置上下文
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 设置请求上下文
        user_id = self._extract_user_id(request)
        tenant_id = self._extract_tenant_id(request)
        set_request_context(
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        try:
            # 记录请求日志
            await self._log_request(request, request_id)
            
            # 处理请求
            response = await call_next(request)
            
            # 计算执行时间
            duration = time.time() - start_time
            
            # 记录响应日志
            await self._log_response(request, response, request_id, duration)
            
            # 记录性能日志
            await self._log_performance(request, duration)
            
            return response
            
        except Exception as e:
            # 记录异常
            duration = time.time() - start_time
            await self._log_exception(request, e, request_id, duration)
            
            # 返回错误响应
            return handle_api_exception(e)
            
        finally:
            # 清除上下文
            clear_request_context()
    
    def _should_skip_logging(self, request: Request) -> bool:
        """判断是否应该跳过日志记录"""
        # 检查路径
        if request.url.path in self.config.exclude_paths:
            return True
        
        # 检查方法
        if request.method in self.config.exclude_methods:
            return True
        
        # 检查静态文件
        if request.url.path.startswith("/static/"):
            return True
        
        return False
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """提取用户ID"""
        # 从JWT token中提取
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 这里可以解析JWT token获取用户ID
            pass
        
        # 从session中提取
        # 这里可以根据实际的认证机制实现
        
        return None
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """提取租户ID"""
        # 从header中提取
        tenant_id = request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id
        
        # 从子域名中提取
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain != "www" and subdomain != "api":
                return subdomain
        
        return None
    
    async def _log_request(self, request: Request, request_id: str):
        """记录请求日志"""
        if not self.config.log_requests:
            return
        
        # 基础请求信息
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "remote_addr": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length")
        }
        
        # 查询参数
        if self.config.log_query_params and request.query_params:
            query_params = dict(request.query_params)
            request_data["query_params"] = self.filter.filter_dict(query_params)
        
        # 路径参数
        if self.config.log_path_params and hasattr(request, "path_params"):
            request_data["path_params"] = dict(request.path_params)
        
        # 请求头
        if self.config.log_headers:
            headers = dict(request.headers)
            request_data["headers"] = self.filter.filter_dict(headers)
        
        # 请求体
        if self.config.log_body and request.method in ["POST", "PUT", "PATCH"]:
            body = await self._read_request_body(request)
            if body:
                request_data["body"] = body
        
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            log_type=LogType.ACCESS,
            data=request_data
        )
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        duration: float
    ):
        """记录响应日志"""
        if not self.config.log_responses:
            return
        
        # 基础响应信息
        response_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration": round(duration, 3),
            "response_size": self._get_response_size(response)
        }
        
        # 响应头
        if self.config.log_headers:
            headers = dict(response.headers)
            response_data["headers"] = self.filter.filter_dict(headers)
        
        # 响应体（仅对JSON响应记录）
        if (self.config.log_body and 
            isinstance(response, JSONResponse) and
            response.status_code < 500):
            
            body = await self._read_response_body(response)
            if body:
                response_data["body"] = body
        
        # 确定日志级别
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(self.logger, log_level)(
            f"Request completed: {request.method} {request.url.path} {response.status_code} {duration:.3f}s",
            log_type=LogType.ACCESS,
            data=response_data
        )
    
    async def _log_performance(self, request: Request, duration: float):
        """记录性能日志"""
        if duration > self.config.slow_request_threshold:
            self.logger.log_performance(
                operation=f"{request.method} {request.url.path}",
                duration=duration,
                threshold=self.config.slow_request_threshold,
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params) if request.query_params else None
            )
    
    async def _log_exception(
        self, 
        request: Request, 
        exception: Exception, 
        request_id: str, 
        duration: float
    ):
        """记录异常日志"""
        error_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration": round(duration, 3),
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(exception)}",
            log_type=LogType.ERROR,
            data=error_data
        )
    
    async def _read_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """读取请求体"""
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.body()
                if body and len(body) <= self.config.max_body_size:
                    json_body = json.loads(body)
                    return self.filter.filter_dict(json_body)
            elif request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                form = await request.form()
                form_dict = {key: value for key, value in form.items()}
                return self.filter.filter_dict(form_dict)
        except Exception:
            # 如果无法解析请求体，跳过
            pass
        
        return None
    
    async def _read_response_body(self, response: Response) -> Optional[Dict[str, Any]]:
        """读取响应体"""
        try:
            if hasattr(response, 'body') and response.body:
                body_bytes = response.body
                if len(body_bytes) <= self.config.max_body_size:
                    body_str = body_bytes.decode('utf-8')
                    json_body = json.loads(body_str)
                    return self.filter.filter_dict(json_body)
        except Exception:
            # 如果无法解析响应体，跳过
            pass
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查X-Forwarded-For头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # 检查X-Real-IP头
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 使用客户端地址
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_response_size(self, response: Response) -> Optional[int]:
        """获取响应大小"""
        content_length = response.headers.get("content-length")
        if content_length:
            return int(content_length)
        
        if hasattr(response, 'body') and response.body:
            return len(response.body)
        
        return None


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """安全日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger()
        self.suspicious_patterns = [
            "script>", "javascript:", "onload=", "onerror=",
            "union select", "drop table", "insert into",
            "../", "..\\", "/etc/passwd", "/windows/system32"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查可疑请求
        await self._check_suspicious_request(request)
        
        # 检查认证失败
        try:
            response = await call_next(request)
            
            if response.status_code == 401:
                await self._log_auth_failure(request)
            elif response.status_code == 403:
                await self._log_permission_denied(request)
            
            return response
            
        except Exception as e:
            await self._log_security_exception(request, e)
            raise
    
    async def _check_suspicious_request(self, request: Request):
        """检查可疑请求"""
        request_data = {
            "path": request.url.path,
            "query": str(request.url.query),
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": self._get_client_ip(request)
        }
        
        # 检查URL中的可疑模式
        full_url = str(request.url).lower()
        for pattern in self.suspicious_patterns:
            if pattern in full_url:
                self.logger.log_security(
                    f"Suspicious pattern detected: {pattern}",
                    data={**request_data, "pattern": pattern}
                )
                break
        
        # 检查异常大的请求
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.CONTENT_LENGTH_LIMIT:
            self.logger.log_security(
                "Large request detected",
                data={**request_data, "content_length": content_length}
            )
        
        # 检查异常的User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        if not user_agent or "bot" in user_agent or "crawler" in user_agent:
            self.logger.log_security(
                "Suspicious user agent",
                data={**request_data, "reason": "empty or bot user agent"}
            )
    
    async def _log_auth_failure(self, request: Request):
        """记录认证失败"""
        self.logger.log_security(
            "Authentication failed",
            data={
                "path": request.url.path,
                "method": request.method,
                "remote_addr": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent")
            }
        )
    
    async def _log_permission_denied(self, request: Request):
        """记录权限拒绝"""
        self.logger.log_security(
            "Permission denied",
            data={
                "path": request.url.path,
                "method": request.method,
                "remote_addr": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent")
            }
        )
    
    async def _log_security_exception(self, request: Request, exception: Exception):
        """记录安全异常"""
        self.logger.log_security(
            f"Security exception: {str(exception)}",
            level="error",
            data={
                "path": request.url.path,
                "method": request.method,
                "remote_addr": self._get_client_ip(request),
                "exception_type": type(exception).__name__,
                "exception_message": str(exception)
            }
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    def __init__(self, app: ASGIApp, audit_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.logger = get_logger()
        self.audit_paths = audit_paths or {
            "/api/users", "/api/tenants", "/api/agents", 
            "/api/knowledge", "/api/tools"
        }
        self.audit_methods = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否需要审计
        if not self._should_audit(request):
            return await call_next(request)
        
        # 记录审计日志
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            await self._log_audit_success(request, response, duration)
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            await self._log_audit_failure(request, e, duration)
            raise
    
    def _should_audit(self, request: Request) -> bool:
        """判断是否需要审计"""
        # 检查方法
        if request.method not in self.audit_methods:
            return False
        
        # 检查路径
        path = request.url.path
        return any(audit_path in path for audit_path in self.audit_paths)
    
    async def _log_audit_success(
        self, 
        request: Request, 
        response: Response, 
        duration: float
    ):
        """记录审计成功日志"""
        self.logger.log_audit(
            action=f"{request.method}",
            resource=request.url.path,
            status="success",
            status_code=response.status_code,
            duration=round(duration, 3),
            remote_addr=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
    
    async def _log_audit_failure(
        self, 
        request: Request, 
        exception: Exception, 
        duration: float
    ):
        """记录审计失败日志"""
        self.logger.log_audit(
            action=f"{request.method}",
            resource=request.url.path,
            status="failure",
            error=str(exception),
            duration=round(duration, 3),
            remote_addr=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


# 使用示例
"""
# 1. 在main.py中添加中间件
from fastapi import FastAPI
from qiushuiai.core.middleware import (
    RequestLoggingMiddleware,
    SecurityLoggingMiddleware,
    AuditLoggingMiddleware,
    RequestLoggingConfig
)

app = FastAPI()

# 配置请求日志
config = RequestLoggingConfig(
    log_requests=True,
    log_responses=True,
    log_body=True,
    max_body_size=settings.MAX_BODY_SIZE,
    slow_request_threshold=settings.SLOW_REQUEST_THRESHOLD
)

# 添加中间件（注意顺序）
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(RequestLoggingMiddleware, config=config)

# 2. 自定义配置
config = RequestLoggingConfig(
    log_requests=True,
    log_responses=True,
    log_headers=True,
    log_body=True,
    exclude_paths={"/api/v1/health", "/metrics", "/docs"},
    sensitive_fields=["password", "token", "secret"]
)

app.add_middleware(RequestLoggingMiddleware, config=config)

# 3. 在路由中使用上下文
from qiushuiai.core.logging import get_logger

@app.get("/api/users")
async def get_users():
    logger = get_logger()
    logger.log_business("users_listed", count=100)
    return {"users": [...]}
""" 