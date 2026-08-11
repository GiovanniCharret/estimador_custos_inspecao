# Executa o estimador. Se faltar qualquer dependencia - inclusive o proprio Python -
# instala tudo antes de rodar. E' o que permite mandar esta pasta para uma maquina
# limpa: o usuario final so da duplo-clique no executar.bat.
#
# A instalacao acontece UMA VEZ. Depois disso a pasta .venv fica ao lado deste arquivo
# e as execucoes seguintes sao imediatas.

Set-Location -Path $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"


function Achar-Uv {
    # Procura o uv (gerenciador da Astral) nos tres lugares onde ele costuma ficar:
    # no PATH, no diretorio padrao do instalador e no diretorio antigo do cargo.
    $noPath = Get-Command uv -ErrorAction SilentlyContinue
    if ($noPath) { return $noPath.Source }
    foreach ($caminho in @("$env:USERPROFILE\.local\bin\uv.exe", "$env:USERPROFILE\.cargo\bin\uv.exe")) {
        if (Test-Path $caminho) { return $caminho }
    }
    return $null
}


function Instalar-ComUv {
    # Caminho preferido: o uv baixa o proprio Python 3.12 e monta a .venv isolada,
    # sem exigir nada instalado na maquina nem direito de administrador.
    $uv = Achar-Uv
    if (-not $uv) {
        Write-Host "  - baixando o instalador de ambiente (uv)..."
        # TLS 1.2 explicito: maquinas com Windows PowerShell antigo negociam TLS 1.0 por
        # padrao e a conexao com o servidor e' recusada.
        try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
        powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
        $uv = Achar-Uv
    }
    if (-not $uv) { return $false }
    Write-Host "  - instalando o Python 3.12..."
    & $uv python install 3.12
    if ($LASTEXITCODE -ne 0) { return $false }
    Write-Host "  - criando o ambiente..."
    # Caminho ABSOLUTO do destino: sem ele o uv resolve o .venv pelo diretorio corrente
    # ou por VIRTUAL_ENV herdado do terminal que chamou.
    & $uv venv --python 3.12 (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) { return $false }
    if (-not (Test-Path $Python)) { return $false }
    Write-Host "  - instalando as bibliotecas..."
    # --python aponta o interpretador EXATO onde instalar. Sem isso o uv escolhe o
    # ambiente que ele achar (VIRTUAL_ENV do terminal, ou um .venv de outra pasta) e as
    # bibliotecas vao parar no lugar errado - o programa depois quebra com
    # "No module named 'pandas'" mesmo tendo dito que instalou tudo.
    & $uv pip install --python $Python -r requirements.txt
    if ($LASTEXITCODE -ne 0) { return $false }
    # Conferencia final: instalou mesmo no ambiente certo?
    & $Python -c "import pandas, numpy, openpyxl, folium"
    return ($LASTEXITCODE -eq 0)
}


function Instalar-ComPythonDoSistema {
    # Plano B: se o download do uv foi bloqueado (proxy/firewall corporativo) mas a
    # maquina ja tem Python, monta a .venv com as ferramentas nativas.
    $exe = $null
    foreach ($candidato in @("py", "python", "python3")) {
        $achado = Get-Command $candidato -ErrorAction SilentlyContinue
        if ($achado) { $exe = $achado.Source; break }
    }
    if (-not $exe) { return $false }
    Write-Host "  - uv indisponivel; usando o Python ja instalado na maquina..."
    # O lancador 'py' precisa do -3 para escolher o Python 3.
    if ([IO.Path]::GetFileNameWithoutExtension($exe) -eq "py") {
        & $exe -3 -m venv .venv
    } else {
        & $exe -m venv .venv
    }
    if (-not (Test-Path $Python)) { return $false }
    Write-Host "  - instalando as bibliotecas..."
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { return $false }
    # Mesma conferencia do caminho do uv: so declara sucesso se der para importar.
    & $Python -c "import pandas, numpy, openpyxl, folium"
    return ($LASTEXITCODE -eq 0)
}


# --- Preparo do ambiente (so na primeira execucao) ---
if (-not (Test-Path $Python)) {
    Write-Host ""
    Write-Host "Primeira execucao: preparando o ambiente. Isso leva alguns minutos e"
    Write-Host "acontece uma unica vez. E' necessario acesso a internet."
    Write-Host ""
    # O Windows corta caminhos em 260 caracteres. A .venv acrescenta uns 130 (o mais
    # fundo e' .venv\Lib\site-packages\<biblioteca>\...), entao uma pasta com nome longo
    # faz a instalacao falhar com "o sistema nao pode encontrar o caminho especificado".
    # Avisar ANTES economiza o tempo de descobrir isso pelo erro cru.
    if ($PSScriptRoot.Length -gt 100) {
        Write-Host "AVISO: esta pasta tem um caminho muito longo ($($PSScriptRoot.Length) caracteres):"
        Write-Host "  $PSScriptRoot"
        Write-Host "O Windows limita caminhos a 260 caracteres e a instalacao pode falhar."
        Write-Host "Se falhar, mova a pasta para um lugar curto, como C:\EstimadorCustos."
        Write-Host ""
    }
    $ok = Instalar-ComUv
    if (-not $ok) {
        # Um .venv pela metade (download interrompido, antivirus, caminho longo) faz o
        # plano B falhar tambem, porque o 'python -m venv' nao conserta ambiente quebrado.
        $venv = Join-Path $PSScriptRoot ".venv"
        if (Test-Path $venv) {
            Write-Host "  - descartando ambiente incompleto..."
            Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
        }
        $ok = Instalar-ComPythonDoSistema
    }
    if (-not $ok) {
        Write-Host ""
        Write-Host "NAO FOI POSSIVEL PREPARAR O AMBIENTE."
        Write-Host ""
        Write-Host "O programa precisa baixar o Python e algumas bibliotecas na primeira"
        Write-Host "execucao. O que costuma impedir isso:"
        Write-Host "  - sem acesso a internet;"
        Write-Host "  - proxy ou firewall corporativo bloqueando https://astral.sh e"
        Write-Host "    https://pypi.org;"
        Write-Host "  - antivirus impedindo a criacao da pasta .venv;"
        Write-Host "  - caminho longo demais (mova a pasta para C:\EstimadorCustos e tente de novo)."
        Write-Host ""
        Write-Host "Peca ao suporte de TI a liberacao desses dois enderecos, ou a"
        Write-Host "instalacao do Python 3.12 na maquina, e rode de novo."
        Read-Host "Pressione Enter para fechar"
        exit 1
    }
    Write-Host ""
    Write-Host "Ambiente pronto."
    Write-Host ""
}

# --- Execucao ---
& $Python "src\estimar_custos.py"
# O exit code do Python manda: a janela so fica aberta quando houve erro.
if ($LASTEXITCODE -ne 0) { Read-Host "ERRO - pressione Enter para fechar" }
