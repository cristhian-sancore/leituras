$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '3'
$images = @('ghcr.io/cristhian-sancore/leituras/backend:latest', 'ghcr.io/cristhian-sancore/leituras/nginx:latest')

try {
    $headers = @{"X-API-Key" = $token}
    
    foreach ($img in $images) {
        Write-Host "Pulling image $img..."
        $pullUrl = "$base/endpoints/$endpoint/docker/images/create?fromImage=$img"
        Invoke-RestMethod -Method Post -Headers $headers -Uri $pullUrl
        Write-Host "Pull completed for $img."
    }
    
    # Restart containers
    $containers = Invoke-RestMethod -Headers $headers -Uri "$base/endpoints/$endpoint/docker/containers/json?all=1"
    
    $backend = $containers | Where-Object { $_.Names -match 'saemi_backend' } | Select-Object -First 1
    if ($backend) {
        Write-Host "Restarting backend..."
        Invoke-RestMethod -Method Post -Headers $headers -Uri ("$base/endpoints/$endpoint/docker/containers/" + $backend.Id + "/restart?t=0")
    }
    
    $nginx = $containers | Where-Object { $_.Names -match 'saemi_proxy|nginx' } | Select-Object -First 1
    if ($nginx) {
        Write-Host "Restarting nginx..."
        Invoke-RestMethod -Method Post -Headers $headers -Uri ("$base/endpoints/$endpoint/docker/containers/" + $nginx.Id + "/restart?t=0")
    }
    
    Write-Host "All done."
} catch {
    Write-Error $_.Exception.Message
}
