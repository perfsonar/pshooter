"""
Hybrid Static/DNS Resolver
"""

import pscheduler


class StaticResolver(object):
    """
    Hostname resolver based on static data
    """

    default_zone_map = {
        "arpa": {
            "in-addr": {
                "1.10.10.10": { "PTR": "abq.example.net." },
                "2.10.10.10": { "PTR": "bos.example.net." },
                "3.10.10.10": { "PTR": "chi.example.net." },
                "4.10.10.10": { "PTR": "dfw.example.net." },
                "5.10.10.10": { "PTR": "ewr.example.net." },
                "99.10.10.10": { "PTR": "url.example.net." }
            },
            "ip6": {
                "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "abqv6.example.net." },
                "2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "bosv6.example.net." },
                "3.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "chiv6.example.net." },
                "4.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "dfwv6.example.net." },
                "5.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "ewrv6.example.net." },
                "99.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f": { "PTR": "urlv6.example.net." }
            }
        },
        "net": {
            "example": {
                
                "abq":   { "A": "10.0.0.1" },
                "abqv6": { "AAAA": "fc00::1" },
                "abq-perfsonar-a": { "TXT": "{ \"pscheduler\": \"ps.abq.example.net\" }" },
                "abq-perfsonar-aaaa": { "TXT": "{ \"pscheduler\": \"ps.abq.example.net\" }" },

                "bos":   { "A": "10.0.0.2" },
                "bosv6": { "AAAA": "fc00::2" },
                "bos-perfsonar-a": { "TXT": "{ \"pscheduler\": \"ps.bos.example.net\" }" },
                "bos-perfsonar-aaaa": { "TXT": "{ \"pscheduler\": \"ps.bos.example.net\" }" },

                "chi":   { "A": "10.0.0.3" },
                "chiv6": { "AAAA": "fc00::3" },
                "chi-perfsonar-a": { "TXT": "{ \"pscheduler\": \"ps.chi.example.net\" }" },
                "chi-perfsonar-aaaa": { "TXT": "{ \"pscheduler\": \"ps.chi.example.net\" }" },

                "dfw":   { "A": "10.0.0.4" },
                "dfwv6": { "AAAA": "fc00::4" },
                "dfw-perfsonar-a": { "TXT": "{ \"pscheduler\": \"ps.dfw.example.net\" }" },
                "dfw-perfsonar-aaaa": { "TXT": "{ \"pscheduler\": \"ps.dfw.example.net\" }" },

                "ewr":   { "A": "10.0.0.5" },
                "ewrv6": { "AAAA": "fc00::5" },
                "ewr-perfsonar-a": { "TXT": "{ \"pscheduler\": \"ps.ewr.example.net\" }" },
                "ewr-perfsonar-aaaa": { "TXT": "{ \"pscheduler\": \"ps.ewr.example.net\" }" },

                "url":   { "A": "10.0.0.99" },
                "urlv6": { "AAAA": "fc00::99" },
                "url-perfsonar-a": { "TXT": "{ \"href\": \"http://www.notonthe.net/hole/ps\" }" },
                "url-perfsonar-aaaa": { "TXT": "{ \"href\": \"http://www.notonthe.net/hole/ps\" }" },
            }
        }
    }


    def __init__(
            self,
            zone_map={}
            ):
        """
        Create a static resolver

        zone_map - If a string, a pointer to a file containing a JSON
        representation of the zone maps.  If a dict, the zone map as
        an in-memory structure.  If None, use the built-in default map.
        """

        if isinstance(zone_map, basestring):
            self.zone_map = pscheduler.json_load(open(zone_map, "r"))
        elif isinstance(zone_map, dict):
            self.zone_map = zone_map
        elif zone_map is None:
            self.zone_map = self.default_zone_map
        else:
            raise ValueError("Wrong type for zone map.")


    def __call__(
            self,
            host,
            record
    ):
        """
        Resolve the host and requested record
        """

        labels_forward = host.lower().split(".")
        labels_reverse = labels_forward[::-1]

        # Remove an empty element caused by a trailing dot
        if labels_forward[-1] == '':
            del labels_forward[-1]
            del labels_reverse[0]

        zone = self.zone_map

        while labels_reverse:

            if labels_reverse[0] in zone:
                zone = zone[labels_reverse[0]]
                continue
            else:
                remaining = ".".join(labels_forward)
                if remaining in zone:
                    zone = zone[remaining]
                    break

            del labels_forward[-1]
            del labels_reverse[0]

        return zone.get(record.upper(), None)



class DNSResolver(object):
    """
    Hostname resolver based on DNS
    """

    def __init__(
            self
            ):
        """
        Create a static resolver
        """

    def __call__(
            self,
            host,
            record
    ):
        """
        Resolve a DNS record
        """
        return pscheduler.dns_resolve(host, query=record)



class HybridResolver:

    """
    Hostname resolver that tries static first and then punts to DNS
    """

    def __init__(
            self,
            zone_map={}
            ):
        """
        Create a hybrid resolver
        """

        self.static = StaticResolver(zone_map)
        self.dns = DNSResolver()


    def __call__(
            self,
            host,
            record
    ):
        """
        Resolve a DNS record
        """

        static_result = self.static(host, record)
        if static_result is not None:
            return static_result
        return self.dns(host, record)




if __name__ == "__main__":

    resolver = HybridResolver(None)
    for tup in [
            ("abq.example.EDU.", "A", None),
            ("abq.EXAMPLE.net.", "A", "10.0.0.1"),
            ("abqv6.EXAMPLE.net", "AAAA", "fc00::1"),
            ("abq-perfsonar-a.EXAMPLE.net", "TXT", "{ \"pscheduler\": \"ps.abq.example.net\" }"),
            ("abq-perfsonar-aaaa.EXAMPLE.net", "TXT", "{ \"pscheduler\": \"ps.abq.example.net\" }"),
            ("1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.c.f.ip6.arpa", "PTR", "abqv6.example.net."),
            ("a1.nv.perfsonar.net", "A", "127.0.0.1"),
            ("aaaa1.nv.perfsonar.net", "AAAA", "fc00::1"),
    ]:

        (host, record, expected) = tup
        result = resolver(host, record)
        print host, record, "  ->  ", result
        if result != expected:
            print "FAIL"
            break

