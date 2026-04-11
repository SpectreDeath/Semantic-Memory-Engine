---
description: Start SME native stack (operator + frontend, no sidecar)
agent: code
subtask: true
---
Start the SME v3.0.1 native stack without Docker:
- SME Operator on port 8000 (includes AI provider)
- Frontend on port 5173

Use PowerShell to start both services:

```powershell
# Terminal 1 - Operator (includes AI provider)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\SME; python -m src.api.main" -WindowStyle Normal

# Terminal 2 - Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\SME\frontend; npm run dev" -WindowStyle Normal
```

Or use the script:
```powershell
.\start_native.ps1
```

After starting, verify services:
- Operator: http://localhost:8000/api/docs
- Frontend: http://localhost:5173
