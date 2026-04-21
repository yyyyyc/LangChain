param(
    [string]$FilePath = "..\.env",
    [string]$ResourceGroup = "RG_1",
    [string]$AppName = "yc-langchain-app-01"
)

Write-Host "Reading environment file: $FilePath"

$settings = @()

Get-Content $FilePath | ForEach-Object {
    $line = $_.Trim()

    # Skip empty lines and comments
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }

    # Split key=value
    $parts = $line -split "=", 2
    if ($parts.Length -ne 2) {
        return
    }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim()

    Write-Host "Adding: $key"

    # Escape quotes if needed
    $value = $value.Replace('"', '\"')

    $settings += "$key=$value"
}

Write-Host "Setting variables in Azure App Service..."

az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings $settings

Write-Host "Done ✅"