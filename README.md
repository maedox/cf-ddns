cf-ddns
=======

# Cloudflare DNS client

Use the Cloudflare API to keep records up to date with your current IP address(es).
By default it will try to get both IPv4 and IPv6 addresses from icanhazip.com. (new in v1.1.0)

This cron expression will add/update an A/AAAA record for domain.tld with your external IP address
every 30 minutes:
```*/30 *  * * *  cf-ddns.py --name domain.tld```

Make sure to set the required environment variable(s):
* CF_API_TOKEN, for the recommended least privilege access model.
* CF_EMAIL and CF_TOKEN, for the old access mode with the superuser account token.

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

## Usage with API (bearer) tokens
If you want to use an API token, there are two options for zone permissions:
1. Allow access to read all zones.
2. Allow access to only a specific zone.

If you go with 2. (recommended), you have to set the zone id manually as a command-line 
argument with ```--zone-id```. If you don't you'll get an error saying you don't have 
permission to list all zones. This is because cf-ddns is trying to find your zone id 
from the DNS name you gave it and it needs to list all zones to do so.

Additionally the token must have access to edit DNS records.

Complete (bearer) token instructions:
1. Go to your Cloudflare profile page and click "API Tokens" in the top menu
2. Create new token
3. Type a name for you token and select "Start with a template"
4. Choose the "Edit zone DNS" template
5. Under "Zone Resources" choose the zone you want to use cf-ddns with
6. Continue and save, then copy the token to the CF_API_TOKEN environment variable.
7. Find the zone id on the dashboard Overview page and add it to the command in the 
```--zone-id``` argument.
8. Execute cf-ddns with the ```--verify-token``` option to verify your setup.
It will exit with code 0 for success and 1 for failure. Results are logged as well.

Check out the [Cloudflare blog post](https://blog.cloudflare.com/api-tokens-general-availability/)
for more information about API tokens.

[@maedox](https://twitter.com/maedox/)
