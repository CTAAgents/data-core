"""Prometheus metrics HTTP 端点。

使用标准库 http.server 暴露 /metrics 端点，不依赖第三方库。
支持优雅关闭。
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from .observability import generate_text


class _MetricsHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器：暴露 /metrics 端点。"""

    def do_GET(self) -> None:
        if self.path in ("/metrics", "/metrics/"):
            try:
                text = generate_text()
            except Exception as e:
                body = f"# error generating metrics: {e}\n".encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; version=0.0.4; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/", "/healthz"):
            body = b"datacore metrics server\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        # 抑制默认访问日志输出
        pass


class MetricsServer:
    """Prometheus metrics HTTP 服务器。

    支持后台线程运行，可优雅关闭。

    使用方式:
        server = MetricsServer(port=9090)
        server.start()
        # ... 服务运行中 ...
        server.stop()
    """

    def __init__(self, port: int = 9090, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动 HTTP 服务器（后台线程）。"""
        if self._server is not None:
            return
        self._server = HTTPServer((self.host, self.port), _MetricsHandler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="datacore-metrics-server",
        )
        self._thread.start()

    def stop(self) -> None:
        """优雅关闭 HTTP 服务器。"""
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        """返回服务器是否在运行。"""
        return self._server is not None


def generate_metrics() -> str:
    """生成 Prometheus exposition format 字符串。

    Returns:
        包含所有已注册指标的 Prometheus exposition format 文本
    """
    return generate_text()


def start_metrics_server(port: int = 9090, host: str = "0.0.0.0") -> MetricsServer:
    """启动 Prometheus metrics HTTP 服务器。

    Args:
        port: 监听端口，默认 9090
        host: 监听地址，默认 0.0.0.0

    Returns:
        已启动的 MetricsServer 实例，可调用 .stop() 关闭

    使用方式:
        server = start_metrics_server(port=9090)
        # 服务运行中，访问 http://localhost:9090/metrics
        # 程序退出前调用 server.stop()
    """
    server = MetricsServer(port=port, host=host)
    server.start()
    return server


__all__ = [
    "MetricsServer",
    "generate_metrics",
    "start_metrics_server",
]
