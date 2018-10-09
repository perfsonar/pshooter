"""
DNS Resolver class for pShooter
"""


class Resolver(object):
    """
    Hostname Resolver
    """

    def __init__(
            self,
            manual_hosts=__default_hosts
            ):
        """
        Construct a filter.  Arguments:

        manual_
        """

        self.output_raw = output_raw

        if type(filter_spec) == dict:
            self.output_raw = filter_spec.get("output-raw", output_raw)
            filter_spec = filter_spec.get("script", ".")

        if isinstance(filter_spec, list):
            filter_spec = "\n".join([str(line) for line in filter_spec])

        if not isinstance(filter_spec, basestring):
            raise ValueError("Filter spec must be plain text, list or dict")

        self.script = pyjq.compile(filter_spec, args)


    def __call__(
            self,
            json={}
    ):
        """
        Filter 'json' according to the script.  If output_raw is True,
        join everything that comes out of the filter into a a single
        string and return that.
        """

        try:

            result = self.script.all(json)

            if isinstance(result, list) and self.output_raw:
                return "\n".join([str(item) for item in result])

            elif isinstance(result, dict) or isinstance(result, list):
                return result

            else:
                raise ValueError("No idea what to do with %s result", type(result))

        except ScriptRuntimeError as ex:
            raise JQRuntimeError(str(ex))




if __name__ == "__main__":

    # TODO:  Write a few examples.

    filter = JQFilter(".")
    print filter('{ "foo": 123, "bar": 456 }')

    pass
