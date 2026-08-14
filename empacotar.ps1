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
# A limpeza PODE FALHAR: basta o usuario ter aberto no Excel um Resumo_Custos.xlsx gerado
# por um teste dentro do proprio pacote. Se falhar e o script seguir em frente, o zip sai
# com dados reais da distribuidora dentro - por isso aqui e' abortar, nao avisar.
if (Test-Path $Destino) {
    Remove-Item $Destino -Recurse -Force -ErrorAction SilentlyContinue
}
# O que interessa e' nao sobrar ARQUIVO - a pasta em si pode resistir a exclusao sem que
# isso seja problema. No Windows basta o Explorer, o editor ou um terminal com o cwd ali
# dentro para segurar o diretorio, e abortar nesse caso seria recusar trabalho por nada.
$Presos = @()
if (Test-Path $Destino) {
    $Presos = @(Get-ChildItem $Destino -Recurse -File -Force -ErrorAction SilentlyContinue)
}
if ($Presos.Count -gt 0) {
    Write-Host ""
    Write-Host "ERRO: nao consegui limpar $Destino." -ForegroundColor Red
    Write-Host "Algum arquivo esta aberto (tipicamente um .xlsx no Excel). Feche e rode de novo."
    Write-Host "Ficaram:"
    $Presos | ForEach-Object { Write-Host "  $($_.FullName)" }
    exit 1
}
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

# 6) Conferencia de vazamento: Entrada/ e saida/ do pacote so podem ter o .gitkeep.
#    Sao as duas pastas que recebem dados REAIS da distribuidora quando alguem testa o
#    pacote no lugar; mandar isso para um terceiro seria vazamento, nao inconveniencia.
foreach ($pasta in @("Entrada", "saida")) {
    $Sujeira = Get-ChildItem (Join-Path $Destino $pasta) -Recurse -File |
               Where-Object { $_.Name -ne ".gitkeep" }
    if ($Sujeira) {
        Write-Host ""
        Write-Host "ERRO: $pasta\ do pacote nao esta vazia:" -ForegroundColor Red
        $Sujeira | ForEach-Object { Write-Host "  $($_.Name)" }
        exit 1
    }
}

# 7) Zip ao lado da pasta, que e' o que se manda por e-mail. Compress-Archive falha SEM
#    parar o script (erro nao-terminante), entao a existencia do arquivo e' conferida
#    depois - ja aconteceu de o script dizer "Pronto" sem ter gerado zip nenhum.
$Zip = Join-Path $PSScriptRoot "distribuicao\EstimadorCustos.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Destino -DestinationPath $Zip -ErrorAction SilentlyContinue
if (-not (Test-Path $Zip)) {
    Write-Host ""
    Write-Host "ERRO: a pasta foi montada, mas o zip nao foi gerado." -ForegroundColor Red
    Write-Host "Cheque se algum arquivo do pacote esta aberto e rode de novo."
    exit 1
}
Write-Host ""
Write-Host "Pronto:"
Write-Host "  pasta: $Destino"
Write-Host "  zip  : $Zip ($([math]::Round((Get-Item $Zip).Length / 1KB)) KB)"
