# Setup do ambiente de DESENVOLVIMENTO: instala uv (se faltar), Python 3.12, cria a
# .venv e instala as dependencias INCLUINDO o pytest.
#
# O usuario final nao usa este arquivo: o _exec.ps1 prepara sozinho o ambiente de
# execucao (sem pytest) na primeira vez que o executar.bat e' clicado.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
uv python install 3.12
uv venv --python 3.12
uv pip install -r requirements-dev.txt
