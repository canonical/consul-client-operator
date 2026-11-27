#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
PRINCIPAL_CHARM = "ubuntu"
APP_NAME = METADATA["name"]
CHARM_BASE = os.environ.get("CHARM_BASE", "ubuntu@24.04")


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Deploy the subordinate on the same base as its principal."""
    filename = f"{APP_NAME}_{CHARM_BASE}-amd64.charm"
    if artifact := os.environ.get("CHARM_PATH"):
        # The CI workflow passes one of the artifacts from the pack job.
        charm = Path(artifact).resolve().with_name(filename)
        assert charm.is_file(), f"Expected packed charm at {charm}"
    else:
        built_charms = await ops_test.build_charm(".", return_all=True)
        charm = next((path for path in built_charms if path.name == filename), None)
        assert charm is not None, f"Charmcraft did not produce {filename}"

    # Deploy the charm and wait for active/idle status
    await ops_test.juju("deploy", PRINCIPAL_CHARM, "--base", CHARM_BASE, check=True)
    await ops_test.model.deploy(charm, application_name=APP_NAME, base=CHARM_BASE, num_units=0)
    await ops_test.model.integrate(APP_NAME, PRINCIPAL_CHARM)
    await ops_test.model.wait_for_idle(apps=[APP_NAME], status="blocked", timeout=1000)


@pytest.mark.abort_on_fail
async def test_refresh_snap_action(ops_test: OpsTest):
    """Test the refresh-snap action runs successfully on a deployed unit."""
    app = ops_test.model.applications[APP_NAME]
    assert app is not None and len(app.units) > 0, "No units found for consul-client"

    unit = app.units[0]
    action = await unit.run_action("refresh-snap")
    await action.wait()

    assert action.status == "completed", (
        f"refresh-snap action failed with status '{action.status}': {action.results}"
    )
    assert "result" in action.results
    assert "refreshed successfully" in action.results["result"]
