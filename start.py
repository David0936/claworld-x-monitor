#!/usr/bin/env python3
"""启动入口：python3 start.py（默认端口 5001，可用 PORT 环境变量改）。"""
import os

if __name__ == "__main__":
    from app import app, screener

    port = int(os.environ.get("PORT", 5001))
    print("=" * 50)
    print("📈 Claworld Monitor — 财经推文监控 + 股票秒筛")
    print(f"   A股名录：{screener.size} 只")
    print(f"   打开 http://localhost:{port}")
    print("   首次登录密码见控制台上方 / data/default_password.txt")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=False)
