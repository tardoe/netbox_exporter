import pynetbox, os, time
from prometheus_client.core import REGISTRY, GaugeMetricFamily
from prometheus_client import start_http_server

NETBOX_HOST = os.environ.get("NETBOX_HOST")
NETBOX_TOKEN = os.environ.get("NETBOX_TOKEN")


class NetboxDeviceCollector(object):
    def __init__(self):
        self.nb = pynetbox.api(NETBOX_HOST, token=NETBOX_TOKEN)

    def collect(self):
        devices = list(self.nb.dcim.devices.all())
        d_metric = GaugeMetricFamily(
            "netbox_devices",
            "All netbox devices.",
            labels=[
                "device",
                "device_type",
                "manufacturer",
                "device_role",
                "region",
                "site",
                "location",
                "rack",
            ],
        )

        for d in devices:
            d_metric.add_metric(
                [
                    d.name,
                    d.device_type.slug,
                    d.device_type.manufacturer.slug,
                    d.device_role.slug,
                    d.site.region.slug,
                    d.site.slug,
                    d.rack.location.slug,
                    d.rack.name,
                ],
                1,
            )

        yield d_metric


class NetboxInterfaceCollector(object):
    def __init__(self):
        self.nb = pynetbox.api(NETBOX_HOST, token=NETBOX_TOKEN)

    def collect(self):
        connected_interfaces = [i for i in self.nb.dcim.interfaces.all() if i.cable]

        i_device_metric = GaugeMetricFamily(
            "netbox_interfaces",
            "All connected interfaces.",
            labels=[
                "interface_name",
                "device",
                "connected_device",
                "connected_device_interface",
            ],
        )

        i_circuit_metric = GaugeMetricFamily(
            "netbox_interfaces",
            "All connected interfaces.",
            labels=[
                "interface_name",
                "device",
                "connected_circuit_id",
                "connected_circuit_type",
                "connected_circuit_provider",
            ],
        )

        # use trace() instead
        # i.trace()[-1][-1][0] gives the connected type
        # i.trace()[-1][-1][0].__class__.__name__ == Interface / CircuitTermination

        for i in connected_interfaces:
            if i.link_peers_type == "dcim.interface":
                i_device_metric.add_metric(
                    [
                        i.name,
                        i.device.name,
                        i.link_peers[0].device.name,
                        i.link_peers[0].name,
                    ],
                    1,
                )

            elif i.link_peers_type == "circuits.circuittermination":
                i_circuit_metric.add_metric(
                    [
                        i.name,
                        i.device.name,
                        i.link_peers[0].circuit.cid,
                        i.link_peers[0].circuit.type.slug,
                        i.link_peers[0].circuit.provider.slug,
                    ],
                    1,
                )

        yield i_device_metric
        yield i_circuit_metric


if __name__ == "__main__":
    start_http_server(9000)
    REGISTRY.register(NetboxDeviceCollector())
    REGISTRY.register(NetboxInterfaceCollector())
    while True:
        # period between collection
        time.sleep(60)
