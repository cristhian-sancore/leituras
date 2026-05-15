$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'

$containers = Invoke-RestMethod -Headers @{"X-API-Key" = $token} -Uri "$base/endpoints/$endpoint/docker/containers/json?all=1"
$db = $containers | Where-Object { $_.Names -match 'saemi_db' } | Select-Object -First 1

if ($db) {
    $id = $db.Id
    $sql = "ALTER TABLE layout_impressao ADD COLUMN IF NOT EXISTS estado_fabric JSONB; ALTER TABLE clientes ADD COLUMN IF NOT EXISTS mensagens_fatura JSONB; ALTER TABLE clientes ADD COLUMN IF NOT EXISTS historico_consumo JSONB;"

    $execBody = @{
        AttachStdout = $true
        AttachStderr = $true
        Cmd = @("psql", "-U", "saemi", "-d", "saemi", "-c", $sql)
    } | ConvertTo-Json
    
    $execResp = Invoke-RestMethod -Method Post -Headers @{"X-API-Key" = $token; "Content-Type" = "application/json"} -Uri "$base/endpoints/$endpoint/docker/containers/$id/exec" -Body $execBody
    $execId = $execResp.Id
    
    # Correct URL for start via Portainer proxy
    $startUrl = "$base/endpoints/$endpoint/docker/exec/$execId/start"
    $startResp = Invoke-RestMethod -Method Post -Headers @{"X-API-Key" = $token; "Content-Type" = "application/json"} -Uri $startUrl -Body "{}"
    $startResp
} else {
    Write-Error "DB container not found"
}
