#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CloudFlare Dynamic DNS updater

CloudFlare has a nice API for managing DNS records, and this script is a simple
way of keeping your subdomains up to date.

You should probably run it from your crontab every five minutes or so:
*/5 *  * * *  cf-ddns.py ...

Requirements:
    - A CloudFlare account and domain name.
    - Python 2.7.4+, probably not Python 3.x.
    - python-cloudflare (https://github.com/eitak-ssim/python-cloudflare).

Credit/inspiration:
    - dyndns-cf by scotchmist (https://github.com/scotchmist/dyndns-cf)
"""

__author__ = "Pål Nilsen (@maedox)"

import logging
import logging.handlers
import socket

from os import path
from sys import version_info

# Support Python 2.7 and 3.3+ even if python-cloudflare doesn't yet.
if version_info >= (2, 7):
    from urllib import urlopen
elif version_info >= (3, 3):
    from urllib.request import urlopen
else:
    exit('Incompatible Python version {}.\n'
         'Please use Python 2.7 or 3.3+')

try:
    import cloudflare
except ImportError:
    exit('python-cloudflare is required for this script to work.\n'
         'See https://github.com/eitak-ssim/python-cloudflare')

valid_record_types = ("A", "AAAA", "CNAME", "LOC",
                      "MX", "NS", "SPF", "SRV", "TXT")
valid_log_levels = ("CRITICAL", "ERROR", "WARNING",
                    "INFO", "DEBUG", "NOTSET")

log_path = path.join(path.expanduser("~"), ".cf-ddns.log")
log_handler = logging.handlers.RotatingFileHandler(
    filename=log_path, maxBytes=1000000, backupCount=1, encoding="utf-8")
log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_format)
log = logging.getLogger(log_path)
log.setLevel("INFO")
log.addHandler(log_handler)


def is_ipv4(ip_address):
    try:
        return socket.inet_pton(socket.AF_INET, ip_address)
    except socket.error:
        return False


def is_ipv6(ip_address):
    try:
        return socket.inet_pton(socket.AF_INET6, ip_address)
    except socket.error:
        return False


def set_cf_record(subdomain, domain, email, token, dest_addr, rec_type, cf_mode):
    """Connect to the CloudFlare API and add or update a DNS record"""

    if rec_type == "A":
        if is_ipv6(dest_addr):
            print(dest_addr + " is an IPv6 address. Use --type AAAA.")
            exit(1)

        if not is_ipv4(dest_addr):
            print(dest_addr + " is not a valid IPv4 address.")
            exit(1)

    if rec_type == "AAAA":
        if is_ipv4(dest_addr):
            print(dest_addr + " is an IPv4 address. Use --type A.")
            exit(1)

        if not is_ipv6(dest_addr):
            print(dest_addr + " is not a valid IPv6 address.")
            exit(1)

    log.debug("""Domain: %s, subdomain: %s, email: %s, IP address: %s, record type: %s, service mode: %s""",
              domain, subdomain, email, dest_addr, rec_type, cf_mode)

    cf_api = cloudflare.CloudFlare(email, token)

    records = cf_api.rec_load_all(domain)
    log.debug("%s records: %s", domain, records)
    rec_id = None
    rec_name = None

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
        log.debug("Response from CloudFlare: %s", api_resp)

    else:
        log.debug("The record doesn't exist, adding it...")
        api_resp = cf_api.rec_new(domain, rec_type, dest_addr,
                                  subdomain, cf_mode)
        log.info("Added new record: %s %s %s",
                 subdomain, rec_type, dest_addr)
        log.debug("Response from CloudFlare: %s", api_resp)


def get_external_ip(services):
    """Get the external IP address from any available free web service"""
    ip = None
    for service in services:
        try:
            ip = urlopen(service).read().strip()
        except Exception:
            pass
    return ip




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--domain", dest="domain", required=True,
                        help="CloudFlare account domain")
    parser.add_argument("--email", dest="email", required=True,
                        help="CloudFlare account email")
    parser.add_argument("--token", dest="token", required=True,
                        help="CloudFlare API token")
    parser.add_argument("--subdomain", dest="subdomain",
                        help="DNS record subdomain")
    parser.add_argument("--content", dest="dest_addr",
                        help="Destination address or DNS record content")
    parser.add_argument("--cf-mode", dest="cf_mode", default="1",
                        choices=(0, 1),
                        help="CloudFlare service mode on(1)/off(0)")
    parser.add_argument("--type", dest="rec_type", default="A",
                        choices=valid_record_types,
                        help="DNS record type")
    parser.add_argument("--ip-service", dest="ip_services", nargs="+",
                        default=("http://icanhazip.com", "http://ip.appspot.com",
                                 "http://my-ip.heroku.com"), metavar="URL",
                        help="URL(s) to obtain external IP address from")
    parser.add_argument("--log-level", dest="log_level", default="INFO",
                        choices=valid_log_levels,
                        help="Logging level")
    args = parser.parse_args()

    if args.subdomain:
        subdomain = args.subdomain + "." + args.domain
    else:
        subdomain = args.domain

    try:
        if args.dest_addr:
            set_cf_record(subdomain, args.domain, args.email, args.token,
                          args.dest_addr, args.rec_type, args.cf_mode)

        else:
            ip_addr = get_external_ip(args.ip_services)
            if ip_addr:
                log.debug("Found external IP address: " + ip_addr)
                set_cf_record(subdomain, args.domain, args.email, args.token,
                              ip_addr, args.rec_type, args.cf_mode)
            else:
                log.error("Sorry, can't do anything without the external IP address. "
                          "Please specify an IP address manually or make sure the IP resolution "
                          "service(s) work as expected.")

    except cloudflare.CloudFlare.APIError as e:
        log.error("CloudFlare API responded with error: {}".format(e))
