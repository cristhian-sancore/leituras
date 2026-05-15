$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'

# Get container ID for saemi_backend
$containers = Invoke-RestMethod -Headers @{"X-API-Key" = $token} -Uri "$base/endpoints/$endpoint/docker/containers/json?all=1"
$backend = $containers | Where-Object { $_.Names -match 'saemi_backend' } | Select-Object -First 1

if ($backend) {
    $id = $backend.Id
    $logsUrl = "$base/endpoints/$endpoint/docker/containers/$id/logs?stdout=1&stderr=1&tail=50"
    $logs = Invoke-RestMethod -Headers @{"X-API-Key" = $token} -Uri $logsUrl
    $logs # Output raw logs
} else {
    Write-Error "Backend container not found"
}
