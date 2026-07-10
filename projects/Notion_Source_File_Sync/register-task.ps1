# register-task.ps1
# Run this from an elevated (Admin) PowerShell prompt to create the scheduled task.
# Usage: Right-click PowerShell > Run as Administrator > .\register-task.ps1

$taskName = "Source File Sync"
$batPath  = "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\Notion_Source_File_Sync\run-source-file-sync.bat"
$workDir  = "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\Notion_Source_File_Sync"

$action   = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ("/c `"`"$batPath`"`"") -WorkingDirectory $workDir
$trigger  = New-ScheduledTaskTrigger -Daily -At '1:00AM'
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Description "Daily sync of approved source files from Notion Runs DB to Publications pages"

Write-Host "`nTask '$taskName' registered successfully." -ForegroundColor Green
Write-Host "Schedule: Daily at 1:00 AM"
Write-Host "Verify with: Get-ScheduledTaskInfo -TaskName '$taskName'"
