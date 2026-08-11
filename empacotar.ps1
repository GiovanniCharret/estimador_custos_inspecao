# Monta a pasta que vai para os usuarios de teste, com o MINIMO necessario para rodar
# numa maquina limpa (sem Python, sem bibliotecas). Rode a partir da raiz do projeto:
#
#     powershell -ExecutionPolicy Bypass -File .\empacotar.ps1
#
# O resultado fica em distribuicao\EstimadorCustos\ e em um .zip ao lado, pronto para enviar.
# Nao vai junto: testes, planning/, minhas_notas/ (pesquisa), .venv, Entrada/ e saida/ com dados.

Set-Location -Path $PSScriptRoot

$Destino = Join-Path $PSScriptRoot "distribuicao\EstimadorCustos"

# Comeca do zero para nao carregar sobra de um empacotamento anterior.
if (Test-Path $Destino) { Remove-Item $Destino -Recurse -Force }
New-Item -ItemType Directory -Path $Destino -Force | Out-Null

Write-Host "Montando $Destino"

# 1) O ritual de duplo-clique e a lista de dependencias.
foreach ($arquivo in @("executar.bat", "_exec.ps1", "requirements.txt")) {
    Copy-Item $arquivo -Destination $Destino
    Write-Host "  + $arquivo"
}

# 2) O codigo. Sem __pycache__, que so pesa e pode conter caminhos da maquina de origem.
New-Item -ItemType Directory -Path (Join-Path $Destino "src") -Force | Out-Null
Get-ChildItem "src\*.py" | ForEach-Object {
    Copy-Item $_.FullName -Destination (Join-Path $Destino "src")
    Write-Host "  + src\$($_.Name)"
}

# 3) A base de contratos: o programa precisa dela para resolver UF e tipo do contrato.
#    O caminho e' o mesmo do repositorio (config.ARQUIVO_BASE_CONTRATOS) para nao haver
#    divergencia entre o que roda aqui e o que roda na maquina do usuario.
$BaseContratos = "dados\base_contratos.json"
if (Test-Path $BaseContratos) {
    New-Item -ItemType Directory -Path (Join-Path $Destino "dados") -Force | Out-Null
    Copy-Item $BaseContratos -Destination (Join-Path $Destino "dados")
    Write-Host "  + $BaseContratos"
} else {
    Write-Host "  ! $BaseContratos nao encontrado - o pacote so vai funcionar sem informar contrato"
}

# 4) As pastas de trabalho, vazias. O .gitkeep garante que existam apos o unzip.
foreach ($pasta in @("Entrada", "saida")) {
    New-Item -ItemType Directory -Path (Join-Path $Destino $pasta) -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $Destino "$pasta\.gitkeep") -Force | Out-Null
    Write-Host "  + $pasta\ (vazia)"
}

# 5) As instrucoes para quem vai receber o pacote.
Copy-Item "LEIA-ME.txt" -Destination $Destino
Write-Host "  + LEIA-ME.txt"

# 6) Zip ao lado da pasta, que e' o que se manda por e-mail.
$Zip = Join-Path $PSScriptRoot "distribuicao\EstimadorCustos.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Destino -DestinationPath $Zip
Write-Host ""
Write-Host "Pronto:"
Write-Host "  pasta: $Destino"
Write-Host "  zip  : $Zip"
