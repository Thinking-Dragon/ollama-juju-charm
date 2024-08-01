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

import requests

from ops import InstallEvent, StartEvent, ConfigChangedEvent, ActionEvent
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
    _charm_state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.generate_action, self._on_generate_action)
        self.framework.observe(self.on.pull_action, self._on_pull_action)

        self._charm_state.set_default(installed=False, port=self.config["port"])

    def _on_install(self, _: InstallEvent):
        """ Install Ollama service """
        self.unit.status = MaintenanceStatus("Installing Ollama")

        try:
            self._install_ollama()
            self._set_ollama_port(self._charm_state.port)

            self._charm_state.installed = True
            self.unit.status = MaintenanceStatus("Ollama installed")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Ollama: {e}")
            self.unit.status = BlockedStatus("Failed to install Ollama")

    def _on_start(self, _: StartEvent):
        """ Start Ollama service """
        if not self._charm_state.installed:
            self.unit.status = BlockedStatus("Cannot start, Ollama is not installed")
            return

        self.unit.status = MaintenanceStatus("Starting Ollama service")
        try:
            self.unit.open_port("tcp", self._charm_state.port)
            self.unit.status = ActiveStatus("Ollama is running")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Ollama service: {e}")
            self.unit.status = BlockedStatus("Failed to start Ollama service")

    def _on_config_changed(self, _: ConfigChangedEvent):
        """ Apply configuration changes """
        new_port = self.config["port"]
        port_has_changed = new_port != self._charm_state.port

        if port_has_changed:
            self.unit.status = MaintenanceStatus("Updating Ollama port")
            try:
                self.unit.close_port("tcp", self._charm_state.port)
                self._set_ollama_port(new_port)
                self.unit.open_port("tcp", new_port)

                self._charm_state.port = new_port
                self.unit.status = ActiveStatus("Ollama port updated")

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to update Ollama port: {e}")
                self.unit.status = BlockedStatus("Failed to update Ollama port")

    def _on_generate_action(self, event: ActionEvent):
        """ Generate completion given a prompt """
        parameters = {
            "stream": False
        }

        if not "model" in event.params:
            event.fail("Parameter \"model\" was not provided, it is required.")
            return
        parameters["model"] = event.params["model"]

        if not "prompt" in event.params:
            event.fail("Parameter \"prompt\" was not provided, it is required.")
            return
        parameters["prompt"] = event.params["prompt"]

        event.log("Executing prompt…")
        response = requests.post(
            f"http://localhost:{self._charm_state.port}/api/generate",
            json=parameters
        ).json()

        if "error" in response:
            event.fail(response["error"])
            return

        event.set_results({
            "model": response["model"],
            "timestamp": response["created_at"],
            "response": response["response"],
        })

    def _on_pull_action(self, event: ActionEvent):
        if not "model" in event.params:
            event.fail("Parameter \"model\" was not provided, it is required.")
            return
        model = event.params["model"]

        event.log(f"Downloading model {model}…")
        requests.post(
            f"http://localhost:{self._charm_state.port}/api/pull",
            json={"name": model}
        )
        event.log("Done.")

    def _install_ollama(self):
        """ Download and install Ollama """
        run_shell("sudo snap install ollama")

    def _set_ollama_port(self, port: int):
        """ Sets the port where Ollama is served """
        run_shell(f"sudo snap set ollama host=0.0.0.0:{str(port)}")

if __name__ == "__main__":
    main(OllamaCharm)
