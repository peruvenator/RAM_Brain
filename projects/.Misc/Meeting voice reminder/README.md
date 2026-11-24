# Meeting Voice

Meeting Voice is a PowerShell script that reads your Microsoft 365 calendar through Microsoft Graph and speaks each meeting a few minutes before it starts, for example:

> "In 5 minutes, you have Q4 pipeline review, with Corey Hoffstein and Adam Butler. It's on Teams."

It does not need Outlook. It runs hidden in the background, starts when you log in to Windows, and uses the voice built into Windows.

## Step 1: Register an app in Entra ID (about 5 minutes, once)

The script needs an app registration so that Microsoft will let it read your calendar.

1. Go to <https://entra.microsoft.com> and open **Applications > App registrations > New registration**.
2. Set **Name** to `Meeting Voice`. Under **Supported account types**, choose **Accounts in this organizational directory only**. Leave **Redirect URI** empty, then click **Register**.
3. On the app's **Overview** page, copy the **Application (client) ID** and the **Directory (tenant) ID** into `config.json` as `ClientId` and `TenantId`.
4. Open **Authentication**. Under **Advanced settings**, set **Allow public client flows** to **Yes**, then click **Save**. This lets the script sign in through the browser without storing a secret.
5. Open **API permissions > Add a permission > Microsoft Graph > Delegated permissions**, add **Calendars.Read**, and click **Add permissions**. (**User.Read** is already listed.)
6. If you are an admin, click **Grant admin consent for** (your organization's name). If you are not, you can approve the permissions yourself when you first sign in, unless your organization only allows admins to approve apps.

"Delegated" means the script can only read your own calendar, and only while your sign-in remains valid. It cannot read anyone else's calendar or send anything.

## Step 2: Install

Open PowerShell in this folder and run:

```
powershell -ExecutionPolicy Bypass -File .\Install-MeetingVoice.ps1
```

The installer:

1. Copies the script and `config.json` to `%LOCALAPPDATA%\MeetingVoice`.
2. Opens your browser so you can sign in. The sign-in code is copied to your clipboard.
3. Lists your meetings for the next 8 hours and speaks the next one, so you can hear that it works.
4. Adds a shortcut to your Startup folder and starts the script in the background.

No admin rights are needed. Your sign-in is stored in `%LOCALAPPDATA%\MeetingVoice\token.dat`, encrypted so that only your Windows account on this PC can read it.

## Settings (`config.json`)

| Setting | Default | What it does |
|---|---|---|
| `MinutesBefore` | `5` | How many minutes before the start to speak. |
| `MainReminderText` | `""` | When set (for example `"Meeting reminder"`), the `MinutesBefore` warning speaks this phrase instead of the meeting title and names. Leave empty for the full announcement. |
| `ShortReminders` | `[]` | Extra warnings that speak a fixed phrase, for example `[{ "MinutesBefore": 1, "Text": "Meeting reminder" }]`. |
| `MaxNames` | `3` | The maximum number of names to read. Any others are counted ("and 2 others"). |
| `MentionTeams` | `true` | Adds "It's on Teams" for Teams meetings. |
| `OnlyMeetingsWithOthers` | `false` | When `true`, skips events that have no other people, such as focus blocks. |
| `Voice` | `""` | Part of a voice name, such as `Zira` or `David`. Run `.\MeetingVoice.ps1 -ListVoices` to see the options. |
| `Rate` | `0` | Speaking speed, from `-10` to `10`. |
| `PollSeconds` | `30` | How often the script checks the calendar. |

To change a setting, edit `config.json` here and run the installer again. Running the installer again keeps your saved sign-in.

## What it skips

The script does not announce all-day events, cancelled meetings, or meetings you declined. When it reads out names, it leaves out you, meeting rooms, and people who declined.

## Troubleshooting

- **Log:** `%LOCALAPPDATA%\MeetingVoice\log.txt` records each announcement and any errors.
- **Sign-in expired:** the script says "Meeting reminders have stopped. Please sign in again." To fix it, run:
  `powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\MeetingVoice\MeetingVoice.ps1" -SignIn`
  Your sign-in normally stays valid as long as the script runs regularly, but your organization's policies can end it sooner.
- **"AADSTS65001" or "need admin approval" at sign-in:** your organization requires an admin to approve the app. Ask an admin to do step 1.6.
- **"AADSTS7000218":** step 1.4 (Allow public client flows) was not saved.
- **Uninstall:** `powershell -ExecutionPolicy Bypass -File .\Install-MeetingVoice.ps1 -Uninstall`
