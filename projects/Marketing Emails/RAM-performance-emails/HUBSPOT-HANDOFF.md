# HubSpot Upload Instructions: ReSolve Monthly Performance Email

## What you are getting

- **`email-template.html`** — the file to paste into HubSpot. 600px fixed-width, mobile-responsive, Outlook VML fallbacks included. All images are already hosted on HubSpot File Manager and referenced via public URLs.
- **`index.html`** — desktop + mobile preview (local reference only, not for HubSpot).

## Assets already uploaded to HubSpot File Manager

These URLs are hard-coded in `email-template.html`. No action needed unless you move the files.

- Header banner: `https://49174072.fs1.hubspotusercontent-na1.net/hubfs/49174072/header-banner.jpg`
- Footer topo texture: `https://49174072.fs1.hubspotusercontent-na1.net/hubfs/49174072/footer-topo.jpg`

## Upload path: Design Manager > Coded Email Template

1. HubSpot > Marketing > Files and Templates > **Design Manager**.
2. Top left: **File > New file**.
3. Select **HTML and HUBL**, then **Email**, name it `RAM Monthly Performance Email`, click **Create**.
4. In the code editor, delete the boilerplate template HubSpot provides.
5. Open `email-template.html` in a text editor, copy all contents, paste into the HubSpot code editor.
6. Click **Publish changes** (top right).

## Create the email from the template

1. HubSpot > Marketing > **Email** > **Create email** > **Regular**.
2. On the template picker, switch to the **Coded templates** tab and select `RAM Monthly Performance Email`.
3. Populate the Settings tab:
    - **From name:** ReSolve Asset Management
    - **From address:** updates@investresolve.com (or your preferred sender)
    - **Subject line:** April 2026 — Monthly Performance Updates (update monthly)
    - **Preview text:** Plus Q1 2026 commentary for the ReSolve All Terrain Program.
4. Recipients tab: select the contact list.

## Required token checks

HubSpot will flag missing compliance tokens during review. The template includes:

- `{{contact.firstname}}` — greeting personalization (optional, template reads "Hi," today)
- `{{unsubscribe_link}}` — one-click unsubscribe (CAN-SPAM required)
- `{{unsubscribe_section}}` — preference center link (CAN-SPAM required)

If HubSpot complains about the unsubscribe token format, wrap them with the HubL conditional the platform expects:

```hubl
{% if unsubscribe_link_type == "one_click" %}{{ unsubscribe_link }}{% else %}{{ unsubscribe_section }}{% endif %}
```

Address block in the footer satisfies the physical-address requirement.

## Before sending: test across clients

1. Click **Send test email** and send to yourself plus at least one Outlook user.
2. Check:
    - Header banner loads (both hosted JPGs are reachable)
    - Pill-shaped CTA buttons render correctly in Outlook (VML fallback)
    - Footer shows deep navy with topo texture
    - All 7 CTA links are live and tracked
    - Unsubscribe link works
3. Preview in the "Inbox previews" tool (HubSpot > Automation > Email tools, or the preview panel in the email editor) across Gmail, Outlook, Apple Mail, iOS Mail.

## Monthly updates

- Swap the subject line for the current month.
- The header banner says "April 2026" (baked into the image). For each new month, Rodrigo will supply a replacement JPG — upload it to File Manager with the same filename (`header-banner.jpg`) to overwrite, or upload with a new name and update the `<img src>` at line 105 of the template.
- Update the seven program button URLs if any monthly report links change.

## CTA button URLs in the template

- Program 01 (All Terrain): Review Monthly Updates, Download Presentation, Download Commentary
- Program 02 (Futures Yield / Carry): Review Monthly Updates, Download Presentation
- Program 03 (Trend Replication): Review Monthly Updates, Download Presentation

All URLs currently point to `investresolve.com/strategies/...` and the hosted HubSpot documents. Confirm these are the latest public links each month.

## If anything breaks

- Images do not load in test: confirm both JPGs are set to public access in File Manager (Files > right-click > Visibility > Public).
- Template fails HubSpot validation: most common issue is unsubscribe token format (see HubL wrapper above).
- Outlook renders buttons as plain blue rectangles with no rounding: expected fallback behavior on older Outlook; pill styling still appears in Outlook 2016+.
