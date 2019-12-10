#!/usr/bin/python
#
# pShooter REST API Server Runner
#

import os
from pshooterapiserver import application

# PORT: Not portable outside of Unix
port = 80 if os.getuid() == 0 \
    else 29285 # Spell out "BWCTL" on a phone and this is what you get.

application.run(
    host='0.0.0.0',
    port=port,
    debug=True
    )
