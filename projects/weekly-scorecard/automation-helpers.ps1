# automation-helpers.ps1
# Shared alerting and run-logging functions for all automations.
# Dot-source this from any script:  . "$PSScriptRoot\..\automation-helpers.ps1"
#
# Required keys in $Config before calling:
#   NotionToken, SlackWebhook, NotionRunsDbId, NotionInventoryDbId
#
# Required variable:
#   $logFile  (path to current log file, used in Slack messages)

function Send-SlackAlert {
    param([string]$Message)
    try {
        $body = @{ text = $Message } | ConvertTo-Json
        Invoke-RestMethod -Uri $Config.SlackWebhook -Method POST -Body $body -ContentType "application/json" | Out-Null
        Write-Log "Slack alert sent"
    }
    catch {
        Write-Log "Slack alert failed (non-fatal): $_"
    }
}

function Log-NotionRun {
    param(
        [string]$AutomationName,
        [string]$OverallStatus,
        [string]$Details
    )
    try {
        $now = Get-Date
        $runTitle = "$AutomationName " + $now.ToString("yyyy-MM-dd HH:mm")

        $body = @{
            parent = @{ database_id = $Config.NotionRunsDbId }
            properties = @{
                "Run" = @{
                    title = @( @{ text = @{ content = $runTitle } } )
                }
                "Date" = @{
                    date = @{ start = $now.ToString("yyyy-MM-ddTHH:mm:ss") }
                }
                "Automation" = @{
                    select = @{ name = $AutomationName }
                }
                "Status" = @{
                    select = @{ name = $OverallStatus }
                }
                "Details" = @{
                    rich_text = @( @{ text = @{ content = $Details.Substring(0, [Math]::Min($Details.Length, 2000)) } } )
                }
            }
        } | ConvertTo-Json -Depth 10

        $headers = @{
            Authorization    = "Bearer $($Config.NotionToken)"
            "Content-Type"   = "application/json"
            "Notion-Version" = "2022-06-28"
        }

        Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method POST -Headers $headers -Body $body | Out-Null
        Write-Log "Notion run log entry created: $runTitle ($OverallStatus)"

        # Update Automations Inventory "Last Run" and "Last Status"
        Update-InventoryStatus -AutomationName $AutomationName -Status $OverallStatus -RunDate $now
    }
    catch {
        Write-Log "Notion run logging failed (non-fatal): $_"
    }
}

function Update-InventoryStatus {
    param(
        [string]$AutomationName,
        [string]$Status,
        [datetime]$RunDate
    )
    try {
        $headers = @{
            Authorization    = "Bearer $($Config.NotionToken)"
            "Content-Type"   = "application/json"
            "Notion-Version" = "2022-06-28"
        }

        # Query for matching entry in inventory
        $queryBody = @{
            filter = @{
                property = "Name"
                title = @{ equals = $AutomationName }
            }
        } | ConvertTo-Json -Depth 5

        $queryResp = Invoke-RestMethod -Uri "https://api.notion.com/v1/databases/$($Config.NotionInventoryDbId)/query" -Method POST -Headers $headers -Body $queryBody
        if ($queryResp.results.Count -gt 0) {
            $pageId = $queryResp.results[0].id
            $updateBody = @{
                properties = @{
                    "Last Run" = @{
                        date = @{ start = $RunDate.ToString("yyyy-MM-ddTHH:mm:ss") }
                    }
                    "Last Status" = @{
                        select = @{ name = $Status }
                    }
                }
            } | ConvertTo-Json -Depth 10

            Invoke-RestMethod -Uri "https://api.notion.com/v1/pages/$pageId" -Method PATCH -Headers $headers -Body $updateBody | Out-Null
            Write-Log "Automations Inventory updated (Last Run, Last Status)"
        }
    }
    catch {
        Write-Log "Inventory update failed (non-fatal): $_"
    }
}
