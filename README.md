# kanka-discord
A Kanka.io to Discord bridge. Automatically posts Kanka changes to a Discord channel.

![Example Discord screenshot](https://github.com/Fallayn/kanka-discord/raw/main/screenshot.png)

This is mostly a quickly cobbled together Python script to post changes made in Kanka.io to a Discord channel.
Using the Kanka API and Discord channel webhooks. Requires Python 3.

Hope this is helpful to others, but no guarantees :)

## Quick guide
1. Check out the repo or grab `kanka.py` and `kankabot.py` at a minimum
2. Edit `kankabot.py`:
  - Insert your [Kanka API key](https://kanka.io/de/docs/1.0/setup): `secret = "<YOUR KANKA API KEY HERE>"`
  - Insert your [Discord channel webhook URL](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks): `discord_channel_post = "<LOG DISCORD CHANNEL WEBHOOK URL>"`
    This should start with `https://discord.com/api/webhooks/...`
  - Insert your campaign name (`campaign_name`) and ID (`camapign_id`)
    You can view your campaign ID in your URL on Kanka.io, at the dashboard:
    `https://kanka.io/de/campaign/<ID>` - insert this as an int above
  - Optionally, change `lang` if you want links to point to non-english pages
  - Optionally, set an image for the webhook inside discord
  - In general, have a look at the top of the Python file to see all options :)
3. Run `python kankabot.py`, making sure to use Python 3
4. You may want to have this run as a service or cron job

## Features
- Pretty Discord embed formatting
- Uses user names, colors, categories and avatars from Kanka.io
- Support for localization/I18N
- Configuration for colors, footer, titles etc. in Discord embeds
- Somewhat smart text shortening
- Stores last posted update IDs in a text file to avoid re-posting
- Tries to only notify a single time if the same entity is updated multiple
  times in a short time frame
- Tries to be a good web citizen and API user with configurable poll intervals,
  dynamically increasing backoff times on errors, and trying for few API calls
  (using mechanisms like Kanka.io's `lastSync` where possible)

Licensed under GPL 3.
Credits for the Python Kanka API go to [Poolitzer](https://github.com/Poolitzer/kanka).