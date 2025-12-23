# This script is used to copy files from contracts/protobuf to service dirs.

$ErrorActionPreference = "Stop"

$PROTO_SRC_DIR = "contracts/protobuf"

function Copy-Protos {
    param(
        [string]$ServiceDir
    )

    $serviceLang = ""
    $destDir = ""

    if (Test-Path "$ServiceDir/pom.xml") {
        $serviceLang = "Java"
        $destDir = "$ServiceDir/src/main/proto"
    }
    elseif (Test-Path "$ServiceDir/pyproject.toml") {
        $serviceLang = "Python"
        $destDir = "$ServiceDir/libs/proto"
    }
    elseif (Test-Path "$ServiceDir/go.mod") {
        $serviceLang = "Go"
        $destDir = "$ServiceDir/proto"
    }
    elseif (Test-Path "$ServiceDir/package.json") {
        $serviceLang = "Node.js"
        $destDir = "$ServiceDir/lib/proto"
    }
    else {
        Write-Host "[WARN] Skip $ServiceDir (language not recognized)" -ForegroundColor Yellow
        return
    }

    Write-Host "Detected $serviceLang service, copying protos to $destDir"

    if (Test-Path $destDir) {
        Remove-Item -Recurse -Force $destDir
    }
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Copy-Item -Recurse -Force "$PROTO_SRC_DIR/*" $destDir

    Write-Host "Protos are copied to $ServiceDir"
}

# Main execution
if ($args.Count -eq 0) {
    Write-Host "Usage: copy-protos.ps1 <service-dir> [service-dir...]"
    exit 1
}

foreach ($serviceDir in $args) {
    if (Test-Path $serviceDir) {
        Copy-Protos -ServiceDir $serviceDir
    }
    else {
        Write-Host "[WARN] Directory not found: $serviceDir" -ForegroundColor Yellow
    }
}
