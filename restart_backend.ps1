$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'

try {
    $headers = @{"X-API-Key" = $token}
    
    # Get backend container
    $containers = Invoke-RestMethod -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/json?all=1"
    $backend = $containers | Where-Object { $_.Names -match 'saemi_backend' } | Select-Object -First 1
    
    if (-not $backend) {
        Write-Error "Backend container not found"
        exit 1
    }
    
    $id = $backend.Id
    Write-Host "Restarting backend ($id)..."
    Invoke-RestMethod -Method Post -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/$id/restart?t=0"
    
    Start-Sleep -Seconds 10
    
    # Check status
    $status = (Invoke-RestMethod -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/$id/json").State.Status
    Write-Host "Current Status:" $status
} catch {
    Write-Error $_.Exception.Message
}
