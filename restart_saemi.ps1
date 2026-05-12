$token = 'ptr_qxZG4bcG7z1VLvalJX3dQKy/dDuWicAL+j4OTV0CEo8='
$base = 'https://portainer.cristhiansancore.com.br/api'
$endpoint = '1'
$url = "$base/endpoints/$endpoint/docker/containers/json?all=1"
$containers = Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri $url
$container = $containers | Where-Object { $_.Names -match 'saemi' } | Select-Object -First 1
if (-not $container) { Write-Error 'Container not found'; exit 1 }
$containerId = $container.Id
$before = (Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri "$base/endpoints/$endpoint/docker/containers/$containerId/json").State.Status
Invoke-RestMethod -Method Post -Headers @{Authorization = "Bearer $token"} -Uri "$base/endpoints/$endpoint/docker/containers/$containerId/restart?t=0"
Start-Sleep -Seconds 5
$after = (Invoke-RestMethod -Headers @{Authorization = "Bearer $token"} -Uri "$base/endpoints/$endpoint/docker/containers/$containerId/json").State.Status
[pscustomobject]@{containerId=$containerId; before=$before; after=$after} | ConvertTo-Json -Compress
