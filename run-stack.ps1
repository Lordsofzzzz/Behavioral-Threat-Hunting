param(
  [ValidateSet('full', 'core', 'engine', 'dashboard', 'simulator', 'demo', 'portal', 'observability', 'homarr')]
  [string]$Profile = 'full',

  [ValidateSet('up', 'down', 'restart', 'logs', 'ps')]
  [string]$Action = 'up',

  [switch]$Help
)

if ($Help) {
  Write-Host 'Usage:'
  Write-Host '  ./run-stack.ps1 [-Profile <full|core|engine|dashboard|simulator|demo|portal|observability|homarr>] [-Action <up|down|restart|logs|ps>]'
  Write-Host ''
  Write-Host 'Examples:'
  Write-Host '  ./run-stack.ps1 -Profile full -Action up'
  Write-Host '  ./run-stack.ps1 -Profile core -Action logs'
  return
}

$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker CLI not found. Install Docker Desktop for Windows, start Docker Desktop, then reopen PowerShell."
  Write-Host "Download: https://www.docker.com/products/docker-desktop/"
  Write-Host "After install, verify with: docker --version ; docker compose version"
  exit 1
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $repoRoot 'docker-compose.yml'

if (-not (Test-Path $composeFile)) {
  throw "Compose file not found: $composeFile"
}

Push-Location $repoRoot
try {
  $baseArgs = @('-f', $composeFile)
  if ($Profile) {
    $baseArgs += @('--profile', $Profile)
  }

  function Invoke-Compose {
    param(
      [string[]]$ComposeArgs,
      [string]$ManualTail
    )

    try {
      & docker compose @ComposeArgs
    }
    catch {
      $manual = "docker compose -f docker-compose.yml --profile $Profile $ManualTail"
      Write-Error "Docker Compose command failed."
      Write-Host "Manual retry: $manual"
      throw
    }
  }

  switch ($Action) {
    'up' {
      Invoke-Compose -ComposeArgs ($baseArgs + @('up', '-d', '--build')) -ManualTail 'up -d --build'
    }
    'down' {
      Invoke-Compose -ComposeArgs ($baseArgs + @('down')) -ManualTail 'down'
    }
    'restart' {
      Invoke-Compose -ComposeArgs ($baseArgs + @('restart')) -ManualTail 'restart'
    }
    'logs' {
      Invoke-Compose -ComposeArgs ($baseArgs + @('logs', '-f', '--tail', '200')) -ManualTail 'logs -f --tail 200'
    }
    'ps' {
      Invoke-Compose -ComposeArgs ($baseArgs + @('ps')) -ManualTail 'ps'
    }
  }
}
finally {
  Pop-Location
}
