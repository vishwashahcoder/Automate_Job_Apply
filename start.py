import sys
import uvicorn

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("🚀 Starting JobPulse AI Web Platform on http://localhost:8080 ...")
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True, timeout_graceful_shutdown=1)
