cf-ddns
=======

# Cloudflare DNS client

Cloudflare has a nice API for managing DNS records, and this script is a simple
way of keeping your subdomains up to date.

You should probably run it from your crontab every five minutes or so.

This will add/update an A/AAAA record for domain.tld with your external IP address:
```*/5 *  * * *  cf-ddns.py --update --domain domain.tld --email user@domain.tld --token ***```


## Requirements:
- A Cloudflare account and domain name.
- Python 2.7.4+.
- python-cloudflare (https://github.com/eitak-ssim/python-cloudflare).


## Credit/inspiration:
- dyndns-cf by scotchmist (https://github.com/scotchmist/dyndns-cf)


## Disclaimer:
This software is provided as is. It should be safe, but don't blame me if your
computer blows up. It is made for GNU/Linux based OS's and Python 2.7.4, 3.3 and up.


## Tl;dr:
- No installation needed, just run it with Python 2.7.4 or 3.3 and up.
- No guarantees what so ever.
- Let me know what you think.

Twitter: https://twitter.com/maedox/

Google+: https://plus.google.com/+PålNilsen
