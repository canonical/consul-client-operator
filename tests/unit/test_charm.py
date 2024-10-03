# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import json
from unittest.mock import patch

import pytest
from ops.model import ActiveStatus, BlockedStatus
from ops.testing import Harness

from charm import ConsulCharm


@pytest.fixture()
def harness():
    harness = Harness(ConsulCharm)
    harness.add_network("10.10.0.10")
    yield harness
    harness.cleanup()


@pytest.fixture()
def snap():
    with patch("charm.snap") as p:
        yield p


@pytest.fixture()
def read_config():
    with patch.object(ConsulCharm, "_read_configuration") as p:
        yield p


@pytest.fixture()
def write_config():
    with patch.object(ConsulCharm, "_write_configuration") as p:
        yield p


def test_start(harness: Harness[ConsulCharm], snap):
    harness.begin_with_initial_hooks()
    assert harness.model.unit.status == BlockedStatus("Integration consul-cluster missing")


def test_consul_cluster_relation(harness: Harness[ConsulCharm], snap, read_config, write_config):
    datacenter = "test-dc"
    join_server_addresses = ["10.20.0.10:8301"]
    read_config.return_value = {
        "bind_addr": "10.10.0.10",
        "datacenter": datacenter,
        "ports": {
            "dns": -1,
            "http": -1,
            "https": -1,
            "grpc": -1,
            "grpc_tls": -1,
            "serf_lan": 8301,
            "serf_wan": -1,
            "server": 8300,
        },
        "retry_join": [join_server_addresses],
    }

    harness.add_relation(
        "consul-cluster",
        "consul-server",
        app_data={
            "datacenter": datacenter,
            "internal_gossip_endpoints": json.dumps(None),
            "external_gossip_endpoints": json.dumps(join_server_addresses),
            "internal_http_endpoint": json.dumps(None),
            "external_http_endpoint": json.dumps(None),
        },
    )
    harness.begin_with_initial_hooks()
    assert harness.model.unit.status == ActiveStatus()


def test_consul_config_changed(harness: Harness[ConsulCharm], snap, read_config, write_config):
    datacenter = "test-dc"
    join_server_addresses = ["10.20.0.10:8301"]
    serf_lan_port = 9301

    harness.update_config({"serf-lan-port": serf_lan_port})
    harness.add_relation(
        "consul-cluster",
        "consul-server",
        app_data={
            "datacenter": datacenter,
            "internal_gossip_endpoints": json.dumps(None),
            "external_gossip_endpoints": json.dumps(join_server_addresses),
            "internal_http_endpoint": json.dumps(None),
            "external_http_endpoint": json.dumps(None),
        },
    )
    harness.begin_with_initial_hooks()
    assert harness.model.unit.status == ActiveStatus()

    config = write_config.mock_calls[0].args[1]
    config = json.loads(config)
    assert config.get("ports", {}).get("serf_lan") == serf_lan_port
