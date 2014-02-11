#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Cloudflare Dynamic DNS updater

Cloudflare has a nice API for managing DNS records, and this script is a simple
way of keeping your subdomains up to date.

You should probably run if from your crontab every five minutes or so:
*/5 *  * * *  cf-ddns.py ...

Requirements:
    - A Cloudflare account and domain name.
    - Python 2.7.4+, probably not Python 3.x.
    - python-cloudflare (https://github.com/eitak-ssim/python-cloudflare).

Credit/inspiration:
    - dyndns-cf by scotchmist (https://github.com/scotchmist/dyndns-cf)
"""

__author__ = "Pål Nilsen (@maedox)"

import logging
import logging.handlers
from cloudflare import CloudFlare
from os import path
from urllib2 import urlopen

log_path = path.join(path.expanduser("~"), ".cf-ddns.log")
log_handler = logging.handlers.RotatingFileHandler(
    filename=log_path, maxBytes=1000000, backupCount=1, encoding="utf-8")
log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_format)
log = logging.getLogger(log_path)
log.setLevel("INFO")
log.addHandler(log_handler)


def set_cf_record(subdomain, domain, email, token, dest_addr, rec_type, cf_mode):
    """Connect to the Cloudflare API and add or update a DNS record"""

    log.debug("""Domain: %s, subdomain: %s, email: %s, IP address: %s, record type: %s, service mode: %s""",
              domain, subdomain, email, dest_addr, rec_type, cf_mode)

    cf_api = CloudFlare(email, token)

    records = cf_api.rec_load_all(domain)
    log.debug("%s records: %s", domain, records)
    rec_id = None

    for record in records["response"]["recs"]["objs"]:
        rec_name = record["name"]
        if rec_name == subdomain:
            # Don't update identical record
            if record["content"] == dest_addr:
                log.debug("Identical record already exists.")
                return

            rec_id = record["rec_id"]
            break

    if rec_id:
        log.info("Found existing record with id: %s", rec_id)
        api_resp = cf_api.rec_edit(domain, rec_type, rec_id,
                                   rec_name, dest_addr, cf_mode)
        log.info("Updated record: %s %s %s",
                 subdomain, rec_type, dest_addr)
        log.debug("Response from Cloudflare: %s", api_resp)

    else:
        log.debug("The record doesn't exist, adding it...")
        api_resp = cf_api.rec_new(domain, rec_type, dest_addr,
                                  subdomain, cf_mode)
        log.info("Added new record: %s %s %s",
                 subdomain, rec_type, dest_addr)
        log.debug("Response from Cloudflare: %s", api_resp)


def get_external_ip(ip_services):
    """Get the external IP address from any available free web service"""
    ip_addr = None
    for service in ip_services:
        try:
            ip_addr = urlopen(service).read().strip()
        except:
            pass
        if ip_addr:
            return ip_addr


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--domain", dest="domain", required=True,
                        help="Cloudflare account domain")
    parser.add_argument("--email", dest="email", required=True,
                        help="Cloudflare account email")
    parser.add_argument("--token", dest="token", required=True,
                        help="Cloudflare API token")
    parser.add_argument("--subdomain", dest="subdomain", default="domain",
                        help="DNS record subdomain")
    parser.add_argument("--content", dest="dest_addr", default=None,
                        help="Destination address or DNS record content")
    parser.add_argument("--cf-mode", dest="cf_mode", default="1",
                        help="Cloudflare service mode on(1)/off(0)")
    parser.add_argument("--type", dest="rec_type", default="A",
                        help="DNS record type")
    parser.add_argument("--ip-service", dest="ip_services", nargs="+",
                        default=(
                            "http://icanhazip.com",
                            "http://ip.appspot.com",
                            "http://my-ip.heroku.com"
                        ), metavar="URL",
                        help="URL to a service for getting external IP address")
    parser.add_argument("--log-level", dest="log_level", default="INFO",
                        help="Log level (ERROR, WARNING, INFO, DEBUG etc.)")
    args = parser.parse_args()

    cf_mode = args.cf_mode
    dest_addr = args.dest_addr
    domain = args.domain
    email = args.email
    ip_services = args.ip_services
    rec_type = args.rec_type
    token = args.token
    log.setLevel(args.log_level.upper())

    if args.subdomain == "domain":
        subdomain = domain
    else:
        subdomain = args.subdomain + "." + domain

    if dest_addr:
        set_cf_record(subdomain, domain, email, token,
                      dest_addr, rec_type, cf_mode)

    else:
        ip_addr = get_external_ip(ip_services)
        if ip_addr:
            log.debug("Found external IP address: " + ip_addr)
            set_cf_record(subdomain, domain, email, token,
                          ip_addr, rec_type, cf_mode)
        else:
            log.error("Sorry, can't do anything without the external IP address.")
