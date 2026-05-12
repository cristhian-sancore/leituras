$token = 'ptr_0+0psRlh3nzAqmCSPXMwkqFVEkfCBx4ziNvuRq3rBgI='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '1'
# List containers
$containers = Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri "${base}/endpoints/${endpoint}/docker/containers/json?all=1"
Write-Host "Containers count:" $containers.Count
$container = $containers | Where-Object { $_.Names -match 'saemi' } | Select-Object -First 1
if (-not $container) { Write-Error "Container not found"; exit 1 }
$id = $container.Id
# Status before restart
$before = (Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri "${base}/endpoints/${endpoint}/docker/containers/${id}/json").State.Status
Write-Host "Status before:" $before
# Restart container
Invoke-RestMethod -Method Post -Headers @{Authorization = "Bearer $token"} -Uri "${base}/endpoints/${endpoint}/docker/containers/${id}/restart?t=0"
Start-Sleep -Seconds 5
# Status after restart
$after = (Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri "${base}/endpoints/${endpoint}/docker/containers/${id}/json").State.Status
Write-Host "Status after:" $after
[pscustomobject]@{containerId=$id; before=$before; after=$after} | ConvertTo-Json -Compress
