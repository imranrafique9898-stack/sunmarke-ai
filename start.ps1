# Start AI Voice Agent - Backend and Frontend

# Set the project path
$projectPath = "C:\Users\PMLS\Downloads\AI Voice Agent\AI Voice Agent"

# Start Backend
$backendJob = Start-Job -ScriptBlock {
    param($path)
    cd "$path\backend"
    pip install -r requirements.txt
    $env:DATABASE_URL = "sqlite:///sunmarke_ai.db"
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
} -ArgumentList $projectPath

# Start Frontend
$frontendJob = Start-Job -ScriptBlock {
    param($path)
    cd "$path\frontend"
    npm install
    npm run dev
} -ArgumentList $projectPath

# Wait a bit for servers to start
Start-Sleep -Seconds 10

# Open browser
Start-Process "http://localhost:3000"

# Output status
Write-Host "Backend job ID: $($backendJob.Id)"
Write-Host "Frontend job ID: $($frontendJob.Id)"
Write-Host "Opening browser to http://localhost:3000"
Write-Host "Press Ctrl+C to stop all jobs when done."