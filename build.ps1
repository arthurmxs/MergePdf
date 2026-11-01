<#
.SYNOPSIS
Gera o executável e o instalador Windows do MergePdf.
#>

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

$version = python -c "from version import APP_VERSION; print(APP_VERSION)"
if ($LASTEXITCODE -ne 0) {
    throw "Não foi possível ler a versão em version.py."
}

python -m PyInstaller --noconfirm --clean --windowed --onefile --name MergePdf --icon assets\app_icon.ico --add-data "assets;assets" script.py
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o executável."
}

$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $standardPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $standardPath) {
        $iscc = Get-Item $standardPath
    }
}
if (-not $iscc) {
    throw "Inno Setup não encontrado. Instale-o em https://jrsoftware.org/isdl.php"
}

& $iscc.Source "/DMyAppVersion=$version" MergePdf.iss
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o instalador."
}

Write-Host "Instalador criado em: dist\installer\MergePdf-Setup.exe"
