import json
from typing import Optional

from pulumi import Inputs, ResourceOptions
from pulumi_gcp import container
from pulumi_gcp.config import project, zone
import pulumi


class ClusterArgs:

    master_version: pulumi.Input[str] 
    """The k8s version for the GKE cluster."""
    node_count: pulumi.Input[int]
    """The initial node count for the GKE cluster."""
    node_machine_type: pulumi.Input[str]
    """The machine type for the GKE cluster."""

    @staticmethod
    def from_inputs(inputs: Inputs) -> 'ClusterArgs':
        return ClusterArgs(master_version=inputs['masterVersion'], 
                           node_count=inputs['nodeCount'], 
                           node_machine_type=inputs['nodeMachineType'])

    def __init__(self, 
                 master_version: Optional[pulumi.Input[str]] = None,
                 node_count: Optional[pulumi.Input[int]] = None,
                 node_machine_type: Optional[pulumi.Input[str]] = None
                 ) -> None:

        self.master_version = master_version
        self.node_count = node_count
        self.node_machine_type = node_machine_type


class Cluster(pulumi.ComponentResource):
    cluster_name: pulumi.Output[str]
    kubeconfig: pulumi.Output[str]

    def __init__(self,
                 name: str,
                 args: ClusterArgs,
                 props: Optional[dict] = None,
                 opts: Optional[ResourceOptions] = None) -> None:

        super().__init__('pequod:gke:Cluster', name, props, opts)

        latest_gke_version = container.get_engine_versions().latest_master_version
        master_version = args.master_version or latest_gke_version
        node_count = args.node_count or 3
        node_machine_type = args.node_machine_type or "n1-standard-1"

        k8s_cluster = container.Cluster(f"{name}-cluster", 
                                        initial_node_count=1,
                                        remove_default_node_pool=True,
                                        min_master_version=master_version,
                                        deletion_protection=False,
                                        opts=ResourceOptions(parent=self))

        node_pool = container.NodePool(f"{name}-primary-node-pool", 
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
                                          ]
                                        ),
                                        version=master_version,
                                        management=container.NodePoolManagementArgs(
                                          auto_repair=True,
                                          auto_upgrade=True,
                                        ),
                                        opts=ResourceOptions(parent=self, depends_on=[k8s_cluster]))

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
