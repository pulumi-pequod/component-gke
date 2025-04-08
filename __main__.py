from pulumi.provider.experimental import component_provider_host

from cluster import Cluster

if __name__ == "__main__":
    component_provider_host(name="gke", components=[Cluster])
