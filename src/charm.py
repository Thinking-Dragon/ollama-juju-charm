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

import requests

from ops import InstallEvent, StartEvent, ConfigChangedEvent, ActionEvent
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

from charms.operator_libs_linux.v2 import snap

logger = logging.getLogger(__name__)

def run_shell(cmd: str) -> str:
    """ Shorthand to run a shell command """
    return subprocess.run(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    ).stdout.decode("utf-8")

class PulledModel:
    """ Information about a model that has been pulled locally by Ollama """
    def __init__(self, name: str, model_id: str, size: str, modified: str):
        self.name = name
        self.id = model_id
        self.size = size
        self.modified = modified

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

        pulled_models = self._get_pulled_models()
        if "model" in event.params:
            model_parameter = event.params["model"]

            for model in pulled_models:
                if self._strip_channel_of_model_if_exists(model.name) == model_parameter:
                    model_parameter = model.name

            if (not any(model.name == model_parameter for model in pulled_models)):
                event.fail(textwrap.dedent(f"""
                    The model you provided ({model_parameter}) was not pulled by Ollama.
                    Make sure that {model_parameter} exists in https://ollama.com/library.
                    Then pull it using `juju run {self.unit.name} pull model="{model_parameter}"`
                """))
                return
            parameters["model"] = model_parameter

        elif pulled_models:
            picked_model = pulled_models[0].name
            event.log(f"Since you have not provided a model, we are using \"{picked_model}\".")
            parameters["model"] = picked_model

        else:
            event.fail(textwrap.dedent(f"""
                No model was pulled on Ollama.
                You must pull at least one model before running the generate action.
                You can find all available models at https://ollama.com/library.
                Use `juju run {self.unit.name} pull model="<model_name>"`.
            """))
            return

        if not "prompt" in event.params:
            event.fail("Parameter \"prompt\" was not provided, it is required.")
            return
        parameters["prompt"] = event.params["prompt"]

        event.log("Executing prompt…")
        try:
            response = requests.post(
                f"http://localhost:{self._charm_state.port}/api/generate",
                json=parameters
            )
            response_content = response.json()

            if "error" in response_content:
                error_message = response_content["error"]
                event.fail(f"Could not generate text: \"{error_message}\"")
                return

            if not response.ok:
                event.fail(f"Could not generate text: \"{response.reason}\"")
                return

            event.set_results({
                "model": response_content["model"],
                "timestamp": response_content["created_at"],
                "response": response_content["response"],
            })

        except Exception as error:
            event.fail(f"Could not generate text: \"{error}\"")

    def _on_pull_action(self, event: ActionEvent):
        if not "model" in event.params:
            event.fail("Parameter \"model\" was not provided, it is required.")
            return
        model = event.params["model"]

        event.log(f"Downloading model {model}…")

        try:
            response = requests.post(
                f"http://localhost:{self._charm_state.port}/api/pull",
                json={"name": model, "stream": False}
            )
            response_content = response.json()

            if "error" in response_content:
                error_message = response_content["error"]
                event.fail(f"Could not pull model {model}: \"{error_message}\"")
                return

            if not response.ok:
                event.fail(f"Could not pull model {model}: \"{response.reason}\"")
                return

            event.log("Done.")
        except Exception as error:
            event.fail(f"Could not pull model {model}: \"{error}\"")

    def _install_ollama(self):
        """ Download and install Ollama """
        snap_cache = snap.SnapCache()
        ollama_snap = snap_cache["ollama"]
        ollama_snap.ensure(state=snap.SnapState.Present)
        ollama_snap.hold()

    def _set_ollama_port(self, port: int):
        """ Sets the port where Ollama is served """
        snap_cache = snap.SnapCache()
        ollama_snap = snap_cache["ollama"]
        
        if not ollama_snap.present:
            raise snap.SnapError(f"Ollama is not installed.")
        
        ollama_snap.set({"host": f"0.0.0.0:{str(port)}"})

    def _get_pulled_models(self) -> list[PulledModel]:
        """ Returns all models that have been pulled by Ollama """
        models_list = run_shell("ollama list")

        lines = [
            [
                row.strip()
                for row in line.split("\t")
                if row != ""
            ]
            for line in models_list.split("\n")
        ]
        lines = [line for line in lines if len(line) == len(lines[0])]

        return [
            PulledModel(
                model_raw[0],
                model_raw[1],
                model_raw[2],
                model_raw[3],
            )
            for model_raw in lines[1:]
        ]

    def _strip_channel_of_model_if_exists(self, raw_model_name: str) -> str:
        colon_id = raw_model_name.find(":")
        if colon_id != -1:
            return raw_model_name[:colon_id]
        else:
            return raw_model_name

if __name__ == "__main__":
    main(OllamaCharm)
