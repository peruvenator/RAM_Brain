#requires -Version 5.1
<#
Meeting Voice: reads your Microsoft 365 calendar through Microsoft Graph and
speaks each meeting a few minutes before it starts, using the Windows voice.

  .\MeetingVoice.ps1 -SignIn      Sign in once (opens the browser).
  .\MeetingVoice.ps1 -Test        List the next 8 hours of meetings and speak the next one.
  .\MeetingVoice.ps1 -ListVoices  Show the voices you can put in config.json.
  .\MeetingVoice.ps1 -SelfTest    Check the spoken wording offline (no sign-in needed).
  .\MeetingVoice.ps1              Run continuously (this is what starts at logon).
#>
[CmdletBinding()]
param(
    [switch]$SignIn,
    [switch]$Test,
    [switch]$ListVoices,
    [switch]$SelfTest
)

$ErrorActionPreference = 'Stop'
$AppDir     = Join-Path $env:LOCALAPPDATA 'MeetingVoice'
$ConfigPath = Join-Path $PSScriptRoot 'config.json'
$TokenPath  = Join-Path $AppDir 'token.dat'
$LogPath    = Join-Path $AppDir 'log.txt'
$Scopes     = 'offline_access User.Read Calendars.Read'

# ---------------------------------------------------------------- utilities

function Write-Log([string]$Text) {
    $line = '{0:yyyy-MM-dd HH:mm:ss}  {1}' -f (Get-Date), $Text
    Write-Host $line
    try {
        if ((Test-Path $LogPath) -and (Get-Item $LogPath).Length -gt 1MB) {
            Move-Item $LogPath "$LogPath.old" -Force
        }
        Add-Content -Path $LogPath -Value $line
    } catch { }
}

function Get-Config {
    if (-not (Test-Path $ConfigPath)) { throw "Missing $ConfigPath." }
    $c = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $defaults = [ordered]@{
        MinutesBefore = 5; MaxNames = 3; MentionTeams = $true
        OnlyMeetingsWithOthers = $false; Voice = ''; Rate = 0; PollSeconds = 30
        ShortReminders = @()
    }
    foreach ($k in $defaults.Keys) {
        if ($null -eq $c.$k) { $c | Add-Member -NotePropertyName $k -NotePropertyValue $defaults[$k] }
    }
    if (-not $c.TenantId -or -not $c.ClientId -or "$($c.TenantId)$($c.ClientId)" -like '*PASTE*') {
        throw "Fill in TenantId and ClientId in $ConfigPath (see README.md)."
    }
    return $c
}

function Get-OAuthError($ErrorRecord) {
    try { return ($ErrorRecord.ErrorDetails.Message | ConvertFrom-Json).error }
    catch { return $ErrorRecord.Exception.Message }
}

function New-AuthException([string]$Message) {
    return [System.UnauthorizedAccessException]::new($Message)
}

# ---------------------------------------------------------------- sign-in and tokens

# The refresh token is encrypted with Windows DPAPI, so only your Windows
# account on this PC can decrypt it.
function Save-RefreshToken([string]$Token) {
    $Token | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString |
        Set-Content -Path $TokenPath
}

function Read-RefreshToken {
    if (-not (Test-Path $TokenPath)) { return $null }
    $secure = (Get-Content $TokenPath -Raw).Trim() | ConvertTo-SecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Invoke-SignIn($Config) {
    $base = "https://login.microsoftonline.com/$($Config.TenantId)/oauth2/v2.0"
    $dc = Invoke-RestMethod -Method Post -Uri "$base/devicecode" -Body @{
        client_id = $Config.ClientId; scope = $Scopes
    }
    Write-Host ''
    Write-Host $dc.message -ForegroundColor Yellow
    try { Set-Clipboard -Value $dc.user_code; Write-Host '(The code is on your clipboard.)' } catch { }
    Start-Process $dc.verification_uri

    $deadline = (Get-Date).AddSeconds([int]$dc.expires_in)
    $interval = [int]$dc.interval
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds $interval
        try {
            $t = Invoke-RestMethod -Method Post -Uri "$base/token" -Body @{
                grant_type  = 'urn:ietf:params:oauth:grant-type:device_code'
                client_id   = $Config.ClientId
                device_code = $dc.device_code
            }
            Save-RefreshToken $t.refresh_token
            Write-Host 'Signed in. The sign-in is saved for this Windows account only.' -ForegroundColor Green
            return
        } catch {
            $err = Get-OAuthError $_
            if ($err -eq 'authorization_pending') { continue }
            if ($err -eq 'slow_down') { $interval += 5; continue }
            throw "Sign-in failed: $err"
        }
    }
    throw 'Sign-in timed out. Run with -SignIn again.'
}

$script:AccessToken = $null
$script:AccessTokenExpires = [datetime]::MinValue

function Get-AccessToken($Config) {
    if ($script:AccessToken -and (Get-Date) -lt $script:AccessTokenExpires) { return $script:AccessToken }
    $rt = Read-RefreshToken
    if (-not $rt) { throw (New-AuthException 'Not signed in. Run MeetingVoice.ps1 -SignIn.') }
    try {
        $t = Invoke-RestMethod -Method Post `
            -Uri "https://login.microsoftonline.com/$($Config.TenantId)/oauth2/v2.0/token" -Body @{
                grant_type = 'refresh_token'; client_id = $Config.ClientId
                refresh_token = $rt; scope = $Scopes
            }
    } catch {
        $err = Get-OAuthError $_
        if ($err -in 'invalid_grant', 'interaction_required') {
            throw (New-AuthException "Sign-in expired ($err). Run MeetingVoice.ps1 -SignIn.")
        }
        throw
    }
    if ($t.refresh_token) { Save-RefreshToken $t.refresh_token }   # Microsoft rotates these
    $script:AccessToken = $t.access_token
    $script:AccessTokenExpires = (Get-Date).AddSeconds([int]$t.expires_in - 300)
    return $script:AccessToken
}

# ---------------------------------------------------------------- Graph

function Invoke-Graph($Config, [string]$Path) {
    $headers = @{
        Authorization = "Bearer $(Get-AccessToken $Config)"
        Prefer        = 'outlook.timezone="UTC"'
    }
    return Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0$Path" -Headers $headers
}

# Your addresses and display name. The name is used to leave you out when you
# are invited under another address, and to recognize booking-tool titles.
function Get-Me($Config) {
    $r = Invoke-Graph $Config '/me?$select=displayName,mail,userPrincipalName'
    return [pscustomobject]@{
        Addresses = @($r.mail, $r.userPrincipalName | Where-Object { $_ } | ForEach-Object { $_.ToLower() })
        Name      = ("$($r.displayName)" -replace '\s+', ' ').Trim()
    }
}

function Get-UpcomingEvents($Config, [int]$AheadMinutes) {
    $fmt = "yyyy-MM-dd'T'HH:mm:ss'Z'"
    $now = (Get-Date).ToUniversalTime()
    $s = $now.AddMinutes(-5).ToString($fmt)
    $e = $now.AddMinutes($AheadMinutes).ToString($fmt)
    $sel = 'id,subject,start,isAllDay,isCancelled,responseStatus,organizer,attendees,isOnlineMeeting,onlineMeetingProvider'
    $r = Invoke-Graph $Config "/me/calendarView?startDateTime=$s&endDateTime=$e&`$select=$sel&`$orderby=start/dateTime&`$top=50"
    return @($r.value)
}

function ConvertFrom-GraphTime($DateTimeTimeZone) {
    return [datetime]::Parse($DateTimeTimeZone.dateTime,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]'AssumeUniversal, AdjustToUniversal')
}

# ---------------------------------------------------------------- wording

# Returns the name to speak and whether it came from a real display name
# (Real = $false when it had to be made from the email address).
function Get-SpokenName($EmailAddress) {
    $n = "$($EmailAddress.name)" -replace '\s*<[^>]*>\s*$', ''        # "Name <address>"
    $real = $true
    if (-not $n.Trim() -or $n -like '*@*') {
        $real = $false
        $local = ("$($EmailAddress.address)" -split '@')[0]
        $n = if ($local -match '[._]') {
            (Get-Culture).TextInfo.ToTitleCase(($local -replace '[._]+', ' ').ToLower())   # first.last
        } else { $local }
    }
    # Kept ASCII-only: Windows PowerShell reads a file without a BOM as ANSI.
    $credentials = '^[A-Z.,\s' + [char]0xAE + [char]0x2122 + ']+$'   # e.g. "CFA, CFP(R)"
    if ($n -match '^\s*([^,]+),\s*(.+)$') {
        $before = $Matches[1]; $after = $Matches[2]
        if ($after -cmatch $credentials) { $n = $before }                   # "Name, CFA(R)": drop credentials
        else { $n = "$after $before" }                                      # "Last, First"
    }
    $n = $n -replace '^(Mr|Mrs|Ms|Dr)\.?\s+', ''
    return [pscustomobject]@{ Name = ($n -replace '\s+', ' ').Trim(); Real = $real }
}

# Organizer first, then attendees. Leaves out you (by address or by name),
# rooms/resources, no-reply senders, people who declined, and duplicates:
# the same name twice, or a name made from an email address when someone with a
# real name has the same address before the @ (rlaterman@ at two domains).
function Get-OtherPeople($Event, $Me) {
    $people = @()
    if ($Event.organizer -and $Event.organizer.emailAddress) {
        $people += [pscustomobject]@{ type = 'organizer'; emailAddress = $Event.organizer.emailAddress; status = $null }
    }
    $people += @($Event.attendees)

    $entries = @()
    foreach ($p in $people) {
        if (-not $p -or -not $p.emailAddress) { continue }
        if ($p.type -eq 'resource') { continue }
        if ($p.status -and $p.status.response -eq 'declined') { continue }
        $addr = "$($p.emailAddress.address)".ToLower()
        if ($addr -and $Me.Addresses -contains $addr) { continue }
        if ($addr -match '^(no-?reply|do-?not-?reply)@') { continue }
        $sn = Get-SpokenName $p.emailAddress
        if (-not $sn.Name) { continue }
        if ($Me.Name -and $sn.Name -eq $Me.Name) { continue }
        $entries += [pscustomobject]@{ Name = $sn.Name; Real = $sn.Real; Local = ($addr -split '@')[0] }
    }

    $realLocals = @{}
    foreach ($e in $entries) { if ($e.Real -and $e.Local) { $realLocals[$e.Local] = $true } }
    $seen = @{}
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($e in $entries) {
        if (-not $e.Real -and $e.Local -and $realLocals.ContainsKey($e.Local)) { continue }
        if ($seen.ContainsKey($e.Name)) { continue }      # hashtable keys ignore case
        $seen[$e.Name] = $true
        $names.Add($e.Name)
    }
    return , $names
}

# Booking tools title meetings like "Meeting: Rodrigo Gordillo (ReSolve) & Nathan Helms".
# Returns the other side ("Nathan Helms") when the subject is your name joined to
# someone else's, otherwise $null.
function Get-BookingGuest([string]$Subject, $Me) {
    if (-not $Me.Name -or -not $Subject) { return $null }
    $name = [regex]::Escape($Me.Name) -replace '\\ ', '\s+'
    $org  = '(?:\s*\([^)]*\))?'
    $sep  = '\s*(?:&|\+|<>|/|\band\b|-)\s*'
    $pre  = '^\s*(?:meeting\s*:\s*)?'
    if ($Subject -match "$pre$name$org$sep(?<other>.+?)\s*$") { return $Matches['other'] }
    if ($Subject -match "$pre(?<other>.+?)$org$sep$name$org\s*$") { return $Matches['other'] }
    return $null
}

function Join-Names($Names, [int]$Max) {
    $Names = @($Names)
    if ($Names.Count -eq 0 -or $Max -le 0) { return '' }
    if ($Names.Count -eq 1) { return $Names[0] }
    if ($Names.Count -le $Max) {
        return (($Names[0..($Names.Count - 2)]) -join ', ') + ' and ' + $Names[-1]
    }
    $more = $Names.Count - $Max
    $label = if ($more -eq 1) { '1 other' } else { "$more others" }
    return (($Names[0..($Max - 1)]) -join ', ') + " and $label"
}

function New-Announcement($Event, [double]$MinutesUntil, $Me, $Config) {
    $subject = "$($Event.subject)".Trim()
    $list = Get-OtherPeople $Event $Me
    $people = @($list)
    $guest = Get-BookingGuest $subject $Me
    if ($guest) {
        # Read the person named in the title first.
        $inTitle = @($people | Where-Object { $guest.IndexOf($_, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
        $people = $inTitle + @($people | Where-Object { $inTitle -notcontains $_ })
    }
    $who = Join-Names $people ([int]$Config.MaxNames)

    if ($guest) {
        $what = if ($who) { "a meeting with $who" } else { $guest }
    } else {
        $what = if ($subject) { $subject } else { 'a meeting with no title' }
        if ($who) { $what += ", with $who" }
    }

    $m = [int][math]::Round($MinutesUntil)
    if ($m -ge 1) {
        $unit = if ($m -eq 1) { 'minute' } else { 'minutes' }
        $msg = "In $m $unit, you have $what"
    } else {
        $msg = "Starting now: $what"
    }
    if ($Config.MentionTeams -and $Event.isOnlineMeeting -and $Event.onlineMeetingProvider -eq 'teamsForBusiness') {
        $msg += ". It's on Teams"
    }
    return "$msg."
}

# Each meeting can be spoken at several points ("stages"): the full announcement
# at MinutesBefore, plus any ShortReminders, which speak a fixed phrase.
function Get-Stages($Config) {
    $stages = @([pscustomobject]@{ Key = 'full'; Minutes = [double]$Config.MinutesBefore; Text = $null })
    foreach ($r in @($Config.ShortReminders)) {
        if ($null -eq $r -or $null -eq $r.MinutesBefore) { continue }
        $text = if ("$($r.Text)".Trim()) { "$($r.Text)".Trim() } else { 'Meeting reminder' }
        $stages += [pscustomobject]@{ Key = "short$($r.MinutesBefore)"; Minutes = [double]$r.MinutesBefore; Text = $text }
    }
    return $stages
}

# When several stages fall due in the same check (for example, the script
# started 30 seconds before a meeting), speak only one: the full announcement
# if it is due, otherwise the short reminder closest to the start.
function Select-Stage($DueStages) {
    $full = @($DueStages | Where-Object { $_.Key -eq 'full' })
    if ($full.Count) { return $full[0] }
    return @($DueStages | Sort-Object Minutes)[0]
}

function Test-ShouldAnnounce($Event, $Me, $Config) {
    if ($Event.isAllDay -or $Event.isCancelled) { return $false }
    if ($Event.responseStatus -and $Event.responseStatus.response -eq 'declined') { return $false }
    if ($Config.OnlyMeetingsWithOthers -and (Get-OtherPeople $Event $Me).Count -eq 0) { return $false }
    return $true
}

# ---------------------------------------------------------------- speech

function New-SpVoice($Config) {
    $v = New-Object -ComObject SAPI.SpVoice
    if ($Config.Voice) {
        $all = $v.GetVoices()
        for ($i = 0; $i -lt $all.Count; $i++) {
            if ($all.Item($i).GetDescription() -like "*$($Config.Voice)*") { $v.Voice = $all.Item($i); break }
        }
    }
    $v.Rate = [int]$Config.Rate
    return $v
}

# ---------------------------------------------------------------- modes

function Start-Watching($Config) {
    $mutex = New-Object System.Threading.Mutex($false, 'Local\MeetingVoice')
    if (-not $mutex.WaitOne(0)) { Write-Log 'Another copy is already running; exiting.'; return }

    $voice = New-SpVoice $Config
    $stages = Get-Stages $Config
    $lookahead = [int](($stages | Measure-Object Minutes -Maximum).Maximum) + 10
    $announced = @{}
    $me = $null
    $authWarned = $false
    Write-Log ("Started. Speaking at: " + (($stages | ForEach-Object { "$($_.Minutes) min" }) -join ', ') + ' before each meeting.')

    while ($true) {
        try {
            if (-not $me) { $me = Get-Me $Config }
            $now = (Get-Date).ToUniversalTime()
            foreach ($ev in Get-UpcomingEvents $Config $lookahead) {
                $base = "$($ev.id)|$($ev.start.dateTime)"
                $start = ConvertFrom-GraphTime $ev.start
                $until = ($start - $now).TotalMinutes
                if ($until -le -2) { continue }
                $due = @($stages | Where-Object { $until -le $_.Minutes -and -not $announced.ContainsKey("$base|$($_.Key)") })
                if ($due.Count -eq 0) { continue }
                foreach ($s in $due) { $announced["$base|$($s.Key)"] = $start }
                if (-not (Test-ShouldAnnounce $ev $me $Config)) { continue }
                $pick = Select-Stage $due
                $msg = if ($pick.Key -eq 'full') { New-Announcement $ev $until $me $Config } else { $pick.Text }
                Write-Log "Speaking: $msg"
                [void]$voice.Speak($msg)
            }
            foreach ($k in @($announced.Keys)) {
                if ($announced[$k] -lt $now.AddHours(-3)) { $announced.Remove($k) }
            }
            $authWarned = $false
        } catch [System.UnauthorizedAccessException] {
            Write-Log $_.Exception.Message
            if (-not $authWarned) {
                [void]$voice.Speak('Meeting reminders have stopped. Please sign in again.')
                $authWarned = $true
            }
        } catch {
            Write-Log "Error (will retry): $($_.Exception.Message)"
        }
        Start-Sleep -Seconds ([int]$Config.PollSeconds)
    }
}

function Invoke-Test($Config) {
    $me = Get-Me $Config
    $now = (Get-Date).ToUniversalTime()
    $events = Get-UpcomingEvents $Config 480 | Where-Object { Test-ShouldAnnounce $_ $me $Config }
    $first = $null
    Write-Host "Meetings in the next 8 hours that would be announced:`n"
    foreach ($ev in $events) {
        $start = ConvertFrom-GraphTime $ev.start
        $until = ($start - $now).TotalMinutes
        if ($until -le -2) { continue }
        $msg = New-Announcement $ev ([math]::Max($until, 0)) $me $Config
        Write-Host ('  {0:ddd HH:mm}  {1}' -f $start.ToLocalTime(), $msg)
        if (-not $first) { $first = $msg }
    }
    if (-not $first) { $first = 'Meeting Voice is connected. You have no meetings in the next 8 hours.'; Write-Host '  (none)' }
    Write-Host "`nSpeaking: $first"
    [void](New-SpVoice $Config).Speak($first)
}

function Invoke-ListVoices {
    $all = (New-Object -ComObject SAPI.SpVoice).GetVoices()
    for ($i = 0; $i -lt $all.Count; $i++) { Write-Host "  $($all.Item($i).GetDescription())" }
}

function Invoke-SelfTest {
    $cfg = [pscustomobject]@{ MinutesBefore = 5; MaxNames = 3; MentionTeams = $true; OnlyMeetingsWithOthers = $true }
    $me = [pscustomobject]@{ Addresses = @('me@example.com'); Name = 'Pat Me' }
    function P($name, $addr, $type = 'required', $resp = 'accepted') {
        [pscustomobject]@{ type = $type; emailAddress = [pscustomobject]@{ name = $name; address = $addr }; status = [pscustomobject]@{ response = $resp } }
    }
    function O($name, $addr) { [pscustomobject]@{ emailAddress = [pscustomobject]@{ name = $name; address = $addr } } }

    $cases = @(
        @{ ev = [pscustomobject]@{ subject = 'Q4 pipeline review'; organizer = (O 'Me' 'ME@example.com'); isOnlineMeeting = $true; onlineMeetingProvider = 'teamsForBusiness'
                attendees = @((P 'Corey Hoffstein' 'corey@example.com'), (P 'Adam Butler' 'adam@example.com'), (P 'Boardroom 4' 'room4@example.com' 'resource'), (P 'Me' 'me@example.com')) }
           until = 4.8; want = "In 5 minutes, you have Q4 pipeline review, with Corey Hoffstein and Adam Butler. It's on Teams." }
        @{ ev = [pscustomobject]@{ subject = 'All hands'; organizer = (O 'Ann Lee' 'ann@example.com')
                attendees = @((P 'Ann Lee' 'ann@example.com'), (P 'Bo Chen' 'bo@example.com'), (P 'Cy Diaz' 'cy@example.com'), (P 'Di Eng' 'di@example.com'), (P 'Ed Fox' 'ed@example.com')) }
           until = 1.2; want = 'In 1 minute, you have All hands, with Ann Lee, Bo Chen, Cy Diaz and 2 others.' }
        @{ ev = [pscustomobject]@{ subject = 'Intro call'; organizer = (O 'Butler, Adam' 'adam@example.com')
                attendees = @((P '' 'jane.doe@example.com'), (P 'Sam Roe' 'sam@example.com' 'optional' 'declined')) }
           until = 0.2; want = 'Starting now: Intro call, with Adam Butler and Jane Doe.' }
        @{ ev = [pscustomobject]@{ subject = ''; organizer = (O 'Me' 'me@example.com'); attendees = @((P 'Pat Kim' 'pat@example.com')) }
           until = 3; want = 'In 3 minutes, you have a meeting with no title, with Pat Kim.' }
        # Booking-tool title: drop your own name, read the guest first, ignore a decliner.
        @{ ev = [pscustomobject]@{ subject = 'Meeting: Pat Me (ReSolve) & Nate Helms '; organizer = (O 'Pat Me' 'me@example.com'); isOnlineMeeting = $true; onlineMeetingProvider = 'teamsForBusiness'
                attendees = @((P 'kyle.lonsinger@acme.com' 'kyle.lonsinger@acme.com'), (P 'Nate Helms' 'nate.helms@acme.com'), (P 'sbooth@rs.com' 'sbooth@rs.com' 'required' 'declined')) }
           until = 5; want = "In 5 minutes, you have a meeting with Nate Helms and Kyle Lonsinger. It's on Teams." }
        # Same name under two addresses; an email-only name with no real-name match stays.
        @{ ev = [pscustomobject]@{ subject = 'Meeting: Pat Me (ReSolve) & Aaron St Pierre'; organizer = (O 'Pat Me' 'me@example.com')
                attendees = @((P 'cbudd@acp.com' 'cbudd@acp.com'), (P 'Pat Me' 'me@example.com' 'required' 'organizer'), (P 'Aaron St Pierre' 'acpadpx@ACP.com' 'required' 'none'), (P 'Aaron St Pierre' 'astpierre@acp.com' 'optional')) }
           until = 5; want = 'In 5 minutes, you have a meeting with Aaron St Pierre and cbudd.' }
        # Booking title with the guest first and no other people: speak the guest.
        @{ ev = [pscustomobject]@{ subject = 'Nate Helms (Acme) <> Pat Me'; organizer = (O 'Pat Me' 'me@example.com') }
           until = 2; want = 'In 2 minutes, you have Nate Helms.' }
        # Same address before the @ at two domains, "Name <address>" display names,
        # and you invited under another address (left out by name).
        @{ ev = [pscustomobject]@{ subject = 'Solutions - Tron and Richard'; organizer = (O 'Richard Laterman' 'rlaterman@a.com')
                attendees = @((P 'Richard Laterman' 'rlaterman@a.com' 'required' 'none'), (P 'Richard Laterman <rlaterman@b.com>' 'rlaterman@b.com' 'optional' 'none'),
                              (P 'rlaterman@b.com' 'rlaterman@b.com' 'optional' 'none'), (P 'tron@welch.com' 'tron@welch.com'), (P 'Pat Me' 'pme@b.com' 'required' 'none'), (P 'Pat Me' 'me@example.com')) }
           until = 5; want = 'In 5 minutes, you have Solutions - Tron and Richard, with Richard Laterman and tron.' }
        # Credentials after a comma, honorifics, double spaces, no-reply senders.
        @{ ev = [pscustomobject]@{ subject = 'Team Meeting'; organizer = (O 'Return Stacked Webinars' 'no-reply@zoom.us')
                attendees = @((P "Carmen MacCallum, CIM$([char]0xAE)" 'carmen@x.com'), (P 'Mr. Corey Hoffstein' 'corey@nf.com'), (P 'Corey Hoffstein' 'corey@rs.com' 'optional'), (P 'Adam  Butler' 'adam@x.com')) }
           until = 5; want = 'In 5 minutes, you have Team Meeting, with Carmen MacCallum, Corey Hoffstein and Adam Butler.' }
        # A subject that only mentions you is not treated as a booking title.
        @{ ev = [pscustomobject]@{ subject = 'Work on Pat Mews objection answers'; organizer = (O 'Pat Me' 'me@example.com') }
           until = 5; want = 'In 5 minutes, you have Work on Pat Mews objection answers.' }
    )

    $fail = 0
    foreach ($c in $cases) {
        $got = New-Announcement $c.ev $c.until $me $cfg
        if ($got -ceq $c.want) { Write-Host "PASS  $got" -ForegroundColor Green }
        else { Write-Host "FAIL  got:  $got`n      want: $($c.want)" -ForegroundColor Red; $fail++ }
    }

    $skipChecks = @(
        @{ name = 'all-day event';   ev = [pscustomobject]@{ isAllDay = $true; attendees = @((P 'A B' 'a@example.com')) } }
        @{ name = 'cancelled event'; ev = [pscustomobject]@{ isCancelled = $true; attendees = @((P 'A B' 'a@example.com')) } }
        @{ name = 'declined by me';  ev = [pscustomobject]@{ responseStatus = [pscustomobject]@{ response = 'declined' }; attendees = @((P 'A B' 'a@example.com')) } }
        @{ name = 'solo block (OnlyMeetingsWithOthers)'; ev = [pscustomobject]@{ subject = 'Focus'; organizer = (O 'Me' 'me@example.com'); attendees = @() } }
    )
    foreach ($s in $skipChecks) {
        if (Test-ShouldAnnounce $s.ev $me $cfg) { Write-Host "FAIL  should skip: $($s.name)" -ForegroundColor Red; $fail++ }
        else { Write-Host "PASS  skips $($s.name)" -ForegroundColor Green }
    }

    $stageCfg = [pscustomobject]@{ MinutesBefore = 5; ShortReminders = @([pscustomobject]@{ MinutesBefore = 1; Text = 'Meeting reminder' }) }
    $st = Get-Stages $stageCfg
    $checks = @(
        @{ until = 4.8; want = 'full' }               # only the 5-minute stage is due
        @{ until = 0.9; want = 'short1' }             # both due, but suppose full was already spoken
        @{ until = 0.5; want = 'full'; fresh = $true } # script just started: speak full, not both
    )
    foreach ($c in $checks) {
        $due = @($st | Where-Object { $c.until -le $_.Minutes })
        if (-not $c.fresh -and $c.until -lt 1) { $due = @($due | Where-Object { $_.Key -ne 'full' }) }
        $got = (Select-Stage $due).Key
        if ($got -eq $c.want) { Write-Host "PASS  stage at $($c.until) min -> $got" -ForegroundColor Green }
        else { Write-Host "FAIL  stage at $($c.until) min -> $got, want $($c.want)" -ForegroundColor Red; $fail++ }
    }

    $t = ConvertFrom-GraphTime ([pscustomobject]@{ dateTime = '2026-11-12T15:00:00.0000000' })
    if ($t.Kind -eq 'Utc' -and $t.Hour -eq 15) { Write-Host 'PASS  Graph time parsed as UTC' -ForegroundColor Green }
    else { Write-Host "FAIL  time parse: $t ($($t.Kind))" -ForegroundColor Red; $fail++ }

    if ($fail) { throw "$fail self-test check(s) failed." }
    Write-Host "`nAll self-test checks passed."
}

# ---------------------------------------------------------------- entry point

New-Item -ItemType Directory -Force -Path $AppDir | Out-Null

if ($SelfTest)   { Invoke-SelfTest; return }
if ($ListVoices) { Invoke-ListVoices; return }

$config = Get-Config
if ($SignIn) { Invoke-SignIn $config; return }
if ($Test)   { Invoke-Test $config; return }
Start-Watching $config
