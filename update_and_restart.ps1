$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'
$image = 'ghcr.io/cristhian-sancore/leituras/backend:latest'

try {
    $headers = @{"X-API-Key" = $token}
    Write-Host "Pulling image $image..."
    $pullUrl = "$base/endpoints/$endpoint/docker/images/create?fromImage=$image"
    $pullResp = Invoke-RestMethod -Method Post -Headers $headers -Uri $pullUrl
    Write-Host "Pull completed."
    
    # Now restart backend
    $containers = Invoke-RestMethod -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/json?all=1"
    $backend = $containers | Where-Object { $_.Names -match 'saemi_backend' } | Select-Object -First 1
    if ($backend) {
        $id = $backend.Id
        Write-Host "Restarting backend ($id)..."
        Invoke-RestMethod -Method Post -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/$id/restart?t=0"
        Write-Host "Done."
    }
} catch {
    Write-Error $_.Exception.Message
}
