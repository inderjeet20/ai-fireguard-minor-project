"""
Local Launcher for AI FireGuard Web Application.
Usage:
    python run.py
"""

import sys
import webbrowser
import uvicorn

if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    
    print("=" * 60)
    print("  AI FireGuard: Intelligent Fire Risk & Safe Evacuation")
    print("  Guru Tegh Bahadur Institute of Technology (GGSIPU)")
    print("=" * 60)
    print(f"  Starting local server at: {url}")
    print("  Press Ctrl+C to terminate.")
    print("=" * 60)

    try:
        # Launch browser tab automatically
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("api.index:app", host=host, port=port, reload=True)
