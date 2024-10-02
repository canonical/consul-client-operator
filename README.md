# Consul Machine Operator

This [Juju](https://juju.is) charmed operator deploys and manages [Consul](https://www.consul.io/) on a machine.
The consul can run as an agent and connect to external consul servers to join the cluster.

## Usage

```sh
juju deploy ./consul_ubuntu-24.04-amd64.charm consul-server
juju integrate consul-client:consul-cluster <consul-server offer>
```

## Configurations

* `snap-channel` consul-client snap channel version to use.
* `serf-lan-port` allows user to set serf port for gossip protocol communication.

## Relations

### Consuming Consul cluster config

* `consul-cluster`: Integrate with consul-server providing consul config to get
the consul cluster server join addresses.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
charm following best practice guidelines, and
[CONTRIBUTING.md](https://github.com/canonical/catalogue-k8s-operator/blob/main/CONTRIBUTING.md) for developer
guidance.
