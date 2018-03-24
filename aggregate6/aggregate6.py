#!/usr/bin/env python
# Copyright (C) 2014-2017 Job Snijders <job@instituut.net>
#
# This file is part of aggregate6
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from __future__ import unicode_literals

try:
    from builtins import str as text
except:
    # Python2.7 compatibility
    from __builtin__ import unicode as text

from ipaddress import ip_network, ip_interface

import aggregate6
import sys


def aggregate(l):
    """Aggregate a `list` of prefixes.

    Keyword arguments:
    l -- a python list of prefixes

    Example use:
    >>> aggregate(["10.0.0.0/8", "10.0.0.0/24"])
    ['10.0.0.0/8']
    """
    return list(_aggregate_set(sorted(l)))


def _aggregate_set(l):
    nets = set()
    for prefix in l:
        net = ip_network(prefix, strict = False)
        thisnet = net
        subnet = None
        while thisnet != subnet:
            if thisnet in nets:
                break
            else:
                subnet = thisnet
                thisnet = thisnet.supernet()
        else:
            add_net(nets, net)
    return nets


def add_net(nets, net):
    supernet = net.supernet()
    the_other = next(x for x in supernet.subnets() if x != net)
    if the_other in nets:
        nets.remove(the_other)
        add_net(nets,supernet)
    else:
        nets.add(net)


def parse_args(args):
    import argparse
    p = argparse.ArgumentParser(description="Aggregate lists of IP prefixes",
                                epilog="""
Copyright 2014-2017 Job Snijders <job@instituut.net>
Project website: https://github.com/job/aggregate6
""", formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('-v', dest='verbose', action='store_true',
                   help="Display verbose information about the optimisations.")
    p.add_argument('-t', dest='truncate', action='store_true',
                   help="truncate IP/mask to network/mask")
    p.add_argument('-m', dest='max_length', metavar='N', type=int,
                   default=0, help="Sets the maximum prefix length for \
entries read. Longer prefixes will be discarded prior to processing.")
    p.add_argument('-V', dest='version', action='store_true',
                   help="Display aggregate6 version")
    afi_group = p.add_mutually_exclusive_group()
    afi_group.add_argument('-4', dest='ipv4_only', action='store_true',
                           default=False,
                           help="Only output IPv4 prefixes")
    afi_group.add_argument('-6', dest='ipv6_only', action='store_true',
                           default=False,
                           help="Only output IPv6 prefixes")
    p.add_argument('args', nargs=argparse.REMAINDER,
                   help='[file ...] or STDIN')
    return p.parse_args(args)


def main():
    import fileinput

    args = parse_args(sys.argv[1:])

    if args.version: # pragma: no cover
        print("aggregate6 %s" % aggregate6.__version__)
        sys.exit()

    input = set()

    for line in fileinput.input(args.args):
        if not line.strip(): # pragma: no cover
            continue
        for elem in line.strip().split():
            try:
                if args.truncate:
                    prefix_obj = ip_interface(text(elem.strip())).network
                else:
                    prefix_obj = ip_network(text(elem.strip()))
                prefix = text(prefix_obj)
            except (ValueError) as err:
                sys.stderr.write("ERROR: '%s' is not a valid IP network, \
ignoring.\n" % elem.strip())
                continue

            if args.max_length > 0:
                if prefix_obj.prefixlen > args.max_length:
                    continue

            if args.ipv4_only and prefix_obj.version == 4:
                input.add(prefix)
            elif args.ipv6_only and prefix_obj.version == 6:
                input.add(prefix)
            elif not args.ipv4_only and not args.ipv6_only:
                input.add(prefix)

    if args.verbose:
        output = _aggregate_set(sorted(input))
        for p in sorted(set(input + output)):
            if p in input and p not in output:
                print("- ", end='')
            elif p in output and p not in input:
                print("+ ", end='')
            else:
                print("  ", end='')
            print(p)
    else:
        for prefix in sorted(aggregate(input)):
            print(prefix)
