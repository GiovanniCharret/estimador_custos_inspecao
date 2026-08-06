# Executa o estimador dentro da .venv; chama o setup se a venv nao existir.
Set-Location -Path $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    powershell -ExecutionPolicy Bypass -File .\instalar.ps1
}
.\.venv\Scripts\python.exe src\estimar_custos.py
if ($LASTEXITCODE -ne 0) { Read-Host "ERRO - pressione Enter para fechar" }
