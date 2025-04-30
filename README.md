# component-gke
Abstraction for Google Cloud K8s cluster resources.

This repo delivers a component to abstract the details related to:
- Creating a Google Cloud K8s cluster.

# Inputs

* master_version (Optional): The k8s version for the GKE cluster. Defaults to latest GKE supproted version.
* node_count (Optional): The initial node count for the GKE cluster. Defaults to 3.
* node_machine_type (Optional): The machine type for the GKE cluster. Defaults to `n1-standard-1`.


# Outputs

* cluster_name: Name of the Google Cloud cluster.
* kubeconfig: kubeconfig for accessing the cluster.

# Usage
## Specify Package in `Pulumi.yaml`

Add the following to your `Pulumi.yaml` file:
Note: If no version is specified, the latest version will be used.

```
packages:
  component-gke: https://github.com/pulumi-pequod/component-gke[@vX.Y.Z]
``` 

## Use SDK in Program

### Python
```
from pequod_gke import Cluster, ClusterArgs

k8s_cluster = Cluster(base_name[:12], ClusterArgs(
    master_version=master_version,
    node_count=node_count,
    node_machine_type=node_machine_type
))
```

### Typescript
```
import { Cluster } from "@pulumi-pequod/gke";

const k8sCluster = new Cluster(baseName, {nodeCount: 4})
```

### Dotnet
```
using PulumiPequod.Gke

var K8sCluster= new Cluster("cluster");
```

### YAML
```
  gke:
    type: gke:Cluster
    properties:
      masterVersion: ${masterVersion}
      nodeCount: ${nodeCount}
      nodeMachineType: ${nodeMachineType}
```




