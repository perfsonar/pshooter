"""
Functions for resolving hostnames and IPs
"""

import multiprocessing
import multiprocessing.dummy
import threading

# See Python 2.6 workaround below.
import weakref


def parallel_run(function, args, max_threads=30):

    if len(args) == 0:
        return ()

    # Work around a bug in 2.6
    # PYTHON3: Get rid of this when 2.6 is no longer in the picture.
    if not hasattr(threading.current_thread(), "_children"):
        threading.current_thread()._children = weakref.WeakKeyDictionary()

    pool = multiprocessing.dummy.Pool(processes=min(len(args), max_threads) )

    result = list(pool.imap(function, args, chunksize=1))

    pool.close()
    return result



if __name__ == "__main__":

    def function(arg):
        return "ARG %s" % (arg)

    print parallel_run(
        function,
        [ 1, 2, 3, 4 ]
    )
