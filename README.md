cf-ddns
=======

# Cloudflare DNS client

Use the Cloudflare API to keep records up to date with your current IP address(es).
By default it will try to get both IPv4 and IPv6 addresses from icanhazip.com. (new in v1.1.0)

This cron expression will add/update an A/AAAA record for domain.tld with your external IP address
every 30 minutes:
```*/30 *  * * *  cf-ddns.py --name domain.tld```

Make sure CF_EMAIL and CF_TOKEN environment variables are set.

Execute `cf-ddns.py -h` for a list of all the arguments.

You can add multiple names like this: ```--name subdomain1.domain.tld someother.domain.tld```

If you want to use Sentry for alerts, set the DSN in the SENTRY_DSN environment variable.

## Requirements:
- A Cloudflare account and domain name.
- Python 3.4 or newer
- Requests (https://github.com/kennethreitz/requests)
- Optional: Raven (for Sentry alerting)

## Disclaimer:
This software is provided as is. It should be safe, but don't blame me if your
computer blows up. It is tested on Mac OSX Python 3.7, Synology NAS Python 3.5.

## Installation:
```pip install --upgrade cf-ddns```

Optionally with Sentry alerting:

```pip install --upgrade cf-ddns[sentry]```


Twitter: https://twitter.com/maedox/
