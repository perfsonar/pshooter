"""
Path
"""

class PathStep(object):
    """
    Single step along a path
    """

    def __init__(
            self,
            host
            ):
        """
        Construct a step.  Arguments:

        host - A string containing an IP address that names the host.
        """
        self.host = host

        # TODO: Find the measurement node
        # Do resolve of host
        # If nothing resolved, check for pS on host
        # If nothing, there's nothing to do measurements.
        self.node = None


    def node(self):
        """
        Return the measurement node for the host
        """
        return self.host




if __name__ == "__main__":

    step = PathStep("10.10.10.4")
    print step.node()
