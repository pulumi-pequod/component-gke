import json
from typing import Optional, TypedDict


from pulumi import Inputs, ResourceOptions
from pulumi_gcp import container
from pulumi_gcp.config import project, zone
import pulumi

class ClusterArgs(TypedDict):

    master_version: pulumi.Input[str] 
    """The k8s version for the GKE cluster."""
    node_count: pulumi.Input[int]
    """The initial node count for the GKE cluster."""
    node_machine_type: pulumi.Input[str]
    """The machine type for the GKE cluster."""
    location: Optional[pulumi.Input[str]]
    """The location (region or zone) for the GKE cluster. If not specified, defaults to the provider's configured zone. If zone is configured, cluster is zonal and only deployed in that zone."""
    autopilot: pulumi.Input[bool]
    """Whether to create an Autopilot GKE cluster (defaults to False)."""

class Cluster(pulumi.ComponentResource):
    """
    Creates Google Cloud K8s cluster.
    """
    cluster_name: pulumi.Output[str]
    """
    Name of the Google Cloud cluster.
    """
    kubeconfig: pulumi.Output[str]
    """
    kubeconfig for accessing the cluster.
    """

    def __init__(
            self,
            name: str,
            args: ClusterArgs,
            opts: Optional[ResourceOptions] = None
    ):

        super().__init__('pequod:gke:Cluster', name, {}, opts)

        latest_gke_version = container.get_engine_versions().latest_master_version
        autopilot_enabled = bool(args.get("autopilot") or False)

        # Note: Autopilot clusters manage nodes and versioning automatically; avoid setting fields
        # that are incompatible in Autopilot mode (initial_node_count, remove_default_node_pool,
        # min_master_version, and any NodePools).
        if autopilot_enabled:
            k8s_cluster = container.Cluster(
                f"{name}-cluster",
                enable_autopilot=True,
                deletion_protection=False,
                opts=ResourceOptions(parent=self),
            )
        else:
            master_version = args.get("master_version") or latest_gke_version
            node_count = args.get("node_count") or 3
            node_machine_type = args.get("node_machine_type") or "n1-standard-1"

            k8s_cluster = container.Cluster(
                f"{name}-cluster",
                location=args.get("location"), 
                initial_node_count=1,
                remove_default_node_pool=True,
                min_master_version=master_version,
                deletion_protection=False,
                opts=ResourceOptions(parent=self),
            )

            _node_pool = container.NodePool(
                f"{name}-primary-node-pool",
                cluster=k8s_cluster.name,
                initial_node_count=node_count,
                location=k8s_cluster.location,
                node_config=container.NodePoolNodeConfigArgs(
                    preemptible=True,
                    machine_type=node_machine_type,
                    oauth_scopes=[
                        "https://www.googleapis.com/auth/compute",
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring",
                    ],
                ),
                version=master_version,
                management=container.NodePoolManagementArgs(
                    auto_repair=True,
                    auto_upgrade=True,
                ),
                opts=ResourceOptions(parent=self, depends_on=[k8s_cluster]),
            )

        # Manufacture a GKE-style Kubeconfig. Note that this is slightly "different" because of the way GKE requires
        # gcloud to be in the picture for cluster authentication (rather than using the client cert/key directly).
        k8s_info = pulumi.Output.all(k8s_cluster.name, k8s_cluster.endpoint, k8s_cluster.master_auth)

        k8s_config = k8s_info.apply(
            lambda info: """apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {0}
    server: https://{1}
  name: {2}
contexts:
- context:
    cluster: {2}
    user: {2}
  name: {2}
current-context: {2}
kind: Config
preferences: {{}}
users:
- name: {2}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
            """.format(info[2]['cluster_ca_certificate'], info[1], '{0}_{1}_{2}'.format(project, zone, info[0])))

        self.kubeconfig = pulumi.Output.secret(k8s_config)

        self.cluster_name = k8s_cluster.name

        self.register_outputs({
            'cluster_name': self.cluster_name,
            'kubeconfig': self.kubeconfig
        })
