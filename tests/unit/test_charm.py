# Copyright 2024 thinking-dragon
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import subprocess
import unittest
from unittest.mock import patch

import ops
import ops.testing
from charm import OllamaCharm

from unittest.mock import patch, MagicMock
from charms.operator_libs_linux.v2 import snap


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = ops.testing.Harness(OllamaCharm)
        self.addCleanup(self.harness.cleanup)

    @patch('charm.snap.SnapCache')
    def test_start(self, mock_snap_cache):
        # Arrange
        mock_ollama_snap = MagicMock()
        mock_snap_cache.return_value = {"ollama": mock_ollama_snap}

        # Act
        self.harness.begin_with_initial_hooks()

        # Assert
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus("Ollama is running"))
        mock_ollama_snap.ensure.assert_called_once_with(state=snap.SnapState.Present)
        mock_ollama_snap.hold.assert_called_once()

    @patch('charm.snap.SnapCache')
    @patch('ops.model.Unit.open_port')
    @patch('ops.model.Unit.close_port')
    def test_config_changed_port(self, mock_close_port, mock_open_port, mock_snap_cache):
        # Arrange
        self.harness.begin()

        mock_ollama_snap = MagicMock()
        mock_ollama_snap.present = True
        mock_snap_cache.return_value = {"ollama": mock_ollama_snap}

        initial_port = 11434
        self.harness.update_config({"port": initial_port})

        # Act
        new_port = 8080
        self.harness.update_config({"port": new_port})

        # Assert
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus("Ollama port updated"))

        mock_close_port.assert_called_once_with("tcp", initial_port)
        mock_open_port.assert_called_once_with("tcp", new_port)

        mock_ollama_snap.set.assert_called_once_with({"host": f"0.0.0.0:{new_port}"})

        self.assertEqual(self.harness.charm._charm_state.port, new_port)

    @patch('charm.snap.SnapCache')
    def test_config_changed_port_failure(self, mock_snap_cache):
        # Arrange
        self.harness.begin()

        mock_ollama_snap = MagicMock()
        mock_ollama_snap.present = True
        mock_ollama_snap.set.side_effect = subprocess.CalledProcessError(1, 'snap set')
        mock_snap_cache.return_value = {"ollama": mock_ollama_snap}

        initial_port = 11434
        self.harness.update_config({"port": initial_port})

        # Act
        new_port = 8080
        self.harness.update_config({"port": new_port})

        # Assert
        self.assertEqual(self.harness.model.unit.status, ops.BlockedStatus("Failed to update Ollama port"))        
        self.assertEqual(self.harness.charm._charm_state.port, initial_port)
