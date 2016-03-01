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

import argparse
import logging
import logging.handlers
import netrc
import socket

import requests

from getpass import getpass
from os import path
from sys import stdout

try:
    import keyring
    use_keyring = True
except ImportError:
    use_keyring = False

__author__ = "Pål Nilsen (@maedox)"

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

log_stdout = logging.StreamHandler(stdout)
log_stdout.setFormatter(log_format)


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


def modify_record(subdom, domain, email, tkn, dest_addrs, rec_type, cf_mode):
    """Connect to the CloudFlare API and add or update a DNS record"""

    for dest_addr in dest_addrs:
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

        rtype = rec_type
        if not rtype:
            if is_ipv4(dest_addr):
                rtype = 'A'
            elif is_ipv6(dest_addr):
                rtype = 'AAAA'
            else:
                raise ValueError('Unable to determine record type. Please add the --type argument.')

        log.debug("""Domain: %s, subdomain: %s, email: %s, IP address: %s, record type: %s, service mode: %s""",
                  domain, subdom, email, dest_addr, rtype, cf_mode)

        cf_api = cloudflare.CloudFlare(email, tkn)
        records = get_all_records(domain, email, tkn)
        log.debug("%s records: %s", domain, records)

        rec_id = None
        rec_name = None

        for record in records:
            rec_exists = False
            if record["name"] == subdom:
                # Don't update identical record
                if record["content"] == dest_addr:
                    log.debug("Identical record already exists.")
                    rec_exists = True
                    break

                if record["type"] == rtype:
                    rec_id = record["rec_id"]
                    break

        if not rec_exists:
            if rec_id:
                log.info("Found existing record with id: %s", rec_id)
                api_resp = cf_api.rec_edit(domain, rtype, rec_id, rec_name, dest_addr, cf_mode)
                log.info("Updated record: %s %s %s",
                         subdom, rtype, dest_addr)
                log.debug("Response from CloudFlare: %s", api_resp)

            else:
                log.debug("The record doesn't exist, adding it...")
                api_resp = cf_api.rec_new(domain, rtype, dest_addr, subdom, cf_mode)
                log.info("Added new record: %s %s %s",
                         subdom, rtype, dest_addr)
                log.debug("Response from CloudFlare: %s", api_resp)


def get_external_ip(services):
    """Get the external IP address from any available web service"""
    ips = set()
    for s in services:
        try:
            ip = requests.get(s).text.strip()
            log.debug("Got external IP address '%s' from '%s'", ip, s)
            if ip:
                ips.add(ip)
        except Exception:
            pass
    return ips


def get_all_records(domain, email, tkn):
    cf_api = cloudflare.CloudFlare(email, tkn)
    records = cf_api.rec_load_all(domain)
    return records['response']['recs']['objs']


def pretty_print_records(records):
    recs = []
    for rec in records:
        recs.append({
            'id': rec['rec_id'],
            'name': rec['name'],
            'type': rec['type'],
            'content': rec['content'],
            'service_mode': rec['service_mode'],
        })

    if recs:
        name_width = max(len(r['name']) for r in recs)
        content_width = max(len(r['content']) for r in recs)
        print('  '.join((
            'Source'.ljust(name_width), 'Type ',
            'Target'.ljust(content_width), 'CF service'
        )) + '\n')
        for r in recs:
            print('  '.join((
                r['name'].ljust(name_width), r['type'].ljust(5),
                r['content'].ljust(content_width), r['service_mode']))
            )


def get_credentials(domain):
    """Get credentials via netrc
    """
    nrc = netrc.netrc()
    creds = nrc.authenticators("Cloudflare_" + domain)
    if creds is not None and len(creds) == 3:
        email, token = creds[0], creds[2]
        return email, token
    else:
        return None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    me = parser.add_mutually_exclusive_group(required=True)
    me.add_argument("--list", action='store_true',
                    help="List all existing DNS records")
    me.add_argument("--update", action='store_true',
                    help="Update a DNS record")

    parser.add_argument("--domain", dest="domain", required=True,
                        help="CloudFlare account domain")
    parser.add_argument("--token", dest="token",
                        help="CloudFlare API token. Will use the keyring module if it's installed.")

    nr = parser.add_mutually_exclusive_group(required=True)
    nr.add_argument("--email", dest="email",
                    help="CloudFlare account email")
    nr.add_argument("--use-netrc", action="store_true",
                    help="Get token from ~/.netrc.")

    parser.add_argument("--subdomain", dest="subdomain",
                        help="DNS record subdomain")
    parser.add_argument("--content", dest="dest_addr",
                        help="Destination address or DNS record content. One or more IPv4/IPv6 is allowed.")
    parser.add_argument("--cf-mode", dest="cf_mode", default="0", choices=(0, 1),
                        help="CloudFlare service mode on(1)/off(0)")
    parser.add_argument("--type", dest="rec_type", default="", choices=valid_record_types,
                        help="DNS record type")
    parser.add_argument("--ip-service", dest="ip_services", nargs="+",
                        default=("https://api.ipify.org", "https://icanhazip.com"), metavar="URL",
                        help="URL(s) to obtain external IP address from")
    parser.add_argument("--log-level", dest="log_level", default="INFO", choices=valid_log_levels,
                        help="Logging level")
    parser.add_argument("--silent", action="store_true",
                        help="Stay silent and don't print actions to stdout. Logging will still occur.")

    args = parser.parse_args()

    email = args.email
    log.setLevel(args.log_level)

    if args.use_netrc:
        use_keyring = False
        email, token = get_credentials(args.domain)

    else:
        token = args.token
        if not token:
            if use_keyring:
                service = "cf-ddns"
                token = keyring.get_password(service, email)
                if not token:
                    print("Cloudflare domain: '{0}', email: '{1}'".format(
                        args.domain, email))
                    while not token:
                        try:
                            token = getpass('API token: ')
                            keyring.set_password(service, email, token)
                        except KeyboardInterrupt:
                            exit()

    if not email:
        exit("Email is missing. Did you not set it in .netrc?")

    if not token:
        exit("API token is not set. Please use the --token argument, add it in .netrc or install the keyring module.")

    if not args.silent and stdout.isatty():
        log.addHandler(log_stdout)

    if args.list:
        pretty_print_records(get_all_records(args.domain, email, token))

    if args.update:
        if args.subdomain:
            if args.subdomain.endswith('.' + args.domain):
                subdomain = args.subdomain
            elif args.subdomain == args.domain:
                subdomain = args.subdomain
            else:
                subdomain = args.subdomain + '.' + args.domain
        else:
            subdomain = args.domain

        try:
            dest_addrs = args.dest_addr
            if not dest_addrs:
                dest_addrs = get_external_ip(args.ip_services)
                if not dest_addrs:
                    log.error("Sorry, can't do anything without the external IP address. "
                              "Please specify an IP address manually or make sure the IP resolution "
                              "service(s) work as expected.")
            modify_record(subdomain, args.domain, email, token,
                          dest_addrs, args.rec_type, args.cf_mode)

        except cloudflare.CloudFlare.APIError as e:
            log.error("CloudFlare API responded with error: {}".format(e))
