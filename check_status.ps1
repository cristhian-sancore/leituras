$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'
$url = "$base/endpoints/$endpoint/docker/containers/json?all=1"

try {
    $containers = Invoke-RestMethod -Headers @{"X-API-Key" = $token} -Uri $url
    $saemi_containers = $containers | Where-Object { $_.Names -match 'saemi' } | Select-Object Names, State, Status, Image
    $saemi_containers | ConvertTo-Json
} catch {
    Write-Error $_.Exception.Message
}
