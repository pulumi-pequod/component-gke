# component-gke
Abstraction for Google Cloud K8s cluster resources.

This repo delivers a component to abstract the details related to:
- Creating a Google Cloud K8s cluster.

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
    node_machine_type=node_machine_type,
    autopilot=False  # set to True to create an Autopilot cluster
))
```

### Typescript
```
import { Cluster } from "@pulumi-pequod/gke";

const k8sCluster = new Cluster(baseName, { nodeCount: 4, autopilot: false })
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
      autopilot: false
```




