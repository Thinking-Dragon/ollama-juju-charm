#!/usr/bin/env python3

# Copyright 2024 Clément Gassmann-Prince
# See LICENSE file for licensing details.

"""
    Charm for deploying and managing Ollama.
    For more information about Ollama:
        Homepage: https://ollama.com/
        Github: https://github.com/ollama/ollama
"""

import logging
import subprocess
import textwrap

from ops import InstallEvent, StartEvent, ConfigChangedEvent
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

logger = logging.getLogger(__name__)

def run_shell(cmd: str):
    """ Shorthand to run a shell command """
    subprocess.run(cmd.split(), check=True)

class OllamaCharm(CharmBase):
    """ Machine charm for Ollama """

    def __init__(self, *args):
        super().__init__(*args)

if __name__ == "__main__":
    main(OllamaCharm)
