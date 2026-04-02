# Setup script for Elasticsearch index lifecycle policy and template
# This script configures 30-day log retention for EduPilot logs

$ErrorActionPreference = "Stop"

$ELASTICSEARCH_URL = if ($env:ELASTICSEARCH_URL) { $env:ELASTICSEARCH_URL } else { "http://localhost:9200" }
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PARENT_DIR = Split-Path -Parent $SCRIPT_DIR

Write-Host "Waiting for Elasticsearch to be ready..."
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "$ELASTICSEARCH_URL/_cluster/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            break
        }
    }
    catch {
        Write-Host "Elasticsearch is unavailable - sleeping"
        Start-Sleep -Seconds 5
        $attempt++
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Error "Elasticsearch did not become ready in time"
    exit 1
}

Write-Host "Elasticsearch is up - configuring index lifecycle policy"

# Create index lifecycle policy for 30-day retention
Write-Host "Creating index lifecycle policy..."
$policyJson = Get-Content "$PARENT_DIR/elasticsearch/index-lifecycle-policy.json" -Raw
Invoke-RestMethod -Uri "$ELASTICSEARCH_URL/_ilm/policy/edupilot-logs-policy" `
    -Method Put `
    -ContentType "application/json" `
    -Body $policyJson

Write-Host "Index lifecycle policy created successfully"

# Create index template
Write-Host "Creating index template..."
$templateJson = Get-Content "$PARENT_DIR/elasticsearch/index-template.json" -Raw
Invoke-RestMethod -Uri "$ELASTICSEARCH_URL/_index_template/edupilot-logs-template" `
    -Method Put `
    -ContentType "application/json" `
    -Body $templateJson

Write-Host "Index template created successfully"

# Create initial index with alias
Write-Host "Creating initial index..."
$initialIndexJson = @{
    aliases = @{
        "edupilot-logs" = @{
            is_write_index = $true
        }
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$ELASTICSEARCH_URL/edupilot-logs-000001" `
    -Method Put `
    -ContentType "application/json" `
    -Body $initialIndexJson

Write-Host "Initial index created successfully"

Write-Host ""
Write-Host "Elasticsearch setup complete!"
Write-Host "Logs will be retained for 30 days and automatically deleted after that period."
Write-Host ""
Write-Host "Access Kibana at: http://localhost:5601"
Write-Host "Elasticsearch API: $ELASTICSEARCH_URL"
