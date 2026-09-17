from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.database.session import AsyncSessionLocal
from app.database.models import AuditLog
import re
import asyncio

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            asyncio.create_task(self.log_audit(request, status_code))
            
    async def log_audit(self, request: Request, status_code: int):
        method_map = {
            "POST": "CREATE",
            "GET": "READ",
            "PUT": "UPDATE",
            "DELETE": "DELETE"
        }
        
        path = request.url.path
        method = request.method
        action = method_map.get(method, "SEARCH")
        
        resource_type = "Unknown"
        resource_id = None
        
        match = re.match(r"^/fhir/([A-Za-z]+)/?([A-Za-z0-9\-]+)?", path)
        if match:
            resource_type = match.group(1)
            resource_id = match.group(2)
            
        result = "SUCCESS" if status_code < 400 else "FAILURE"
        ip = request.client.host if request.client else None

        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token_str = auth_header.split(" ", 1)[1].strip()
            try:
                from app.auth.security import decode_token
                payload = decode_token(token_str)
                user_id = payload.get("sub")
            except Exception:
                pass
        
        try:
            async with AsyncSessionLocal() as session:
                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result=result,
                    ip_address=ip,
                    http_method=method,
                    path=path,
                    status_code=status_code
                )
                session.add(log)
                await session.commit()
        except Exception:
            pass # Never let audit log break request processing
