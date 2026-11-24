$ErrorActionPreference = "Stop"

$installRoot = if ($env:OLLAMA_INSTALL_DIR) { $env:OLLAMA_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "Programs\Ollama" }
$ollamaExe = Join-Path $installRoot "ollama.exe"
if (-not (Test-Path -LiteralPath $ollamaExe)) {
    throw "Ollama was not found at $ollamaExe. Install or extract the Ollama Windows standalone package first."
}

$env:OLLAMA_MODELS = Join-Path $env:USERPROFILE ".ollama\models"
$env:OLLAMA_HOST = "127.0.0.1:11434"
$apiUri = "http://127.0.0.1:11434/api/version"

try {
    $version = Invoke-RestMethod -Uri $apiUri -TimeoutSec 2
    Write-Host "Ollama is already running (version $($version.version))."
    exit 0
} catch {
    # Start the local API service when it is not already running.
}

Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden | Out-Null

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    try {
        $version = Invoke-RestMethod -Uri $apiUri -TimeoutSec 2
        Write-Host "Ollama is running (version $($version.version))."
        exit 0
    } catch {
        # Keep waiting for the local service to bind its API port.
    }
}

throw "Ollama did not start. Check the Ollama installation and try again."