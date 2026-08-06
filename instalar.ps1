# Setup unico: instala uv (se faltar), Python 3.12, cria .venv e instala dependencias.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
uv python install 3.12
uv venv --python 3.12
uv pip install -r requirements.txt
