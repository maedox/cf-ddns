cf-ddns
=======

# Cloudflare DNS client

Use the Cloudflare API to keep records up to date with your current IP address(es).

You could run it from your crontab every five minutes or so.

This will add/update an A/AAAA record for domain.tld with your external IP address:
```*/5 *  * * *  cf-ddns.py --name domain.tld```

Make sure CF_EMAIL and CF_TOKEN environment variables are set.

Execute `cf-ddns.py -h` for list of arguments.


## Requirements:
- A Cloudflare account and domain name.
- Python 2.7.6 or newer, 3.3 or newer
- Requests (https://github.com/kennethreitz/requests)


## Disclaimer:
This software is provided as is. It should be safe, but don't blame me if your
computer blows up. It is tested on Ubuntu 16.04 with Python 2.7.6 and 3.5.2.


Twitter: https://twitter.com/maedox/
