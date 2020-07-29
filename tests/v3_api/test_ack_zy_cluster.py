from .entfunc import *  # NOQA
import pytest



def test_create_ack_cluster():

    client = get_admin_client()
    ackConfig = get_ack_config()

    print("Cluster creation")
    cluster = client.create_cluster(ackConfig)
    print(cluster)
    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)

    cluster_cleanup(client, cluster)


def get_ack_config():

    # name = random_test_name("test-auto-ack")
    name = "k8s1"
    ackConfig =  {
        "accessKeyId": "LTAI4G9tfi9ukE4exEXtVvkh",
        "accessKeySecret": "Y2yIncYq1F0FZ3fRPhvVnlsGRpi6sB",
        "cloudMonitorFlags": False,
        "clusterType": "ManagedKubernetes",
        "containerCidr": "172.20.0.0/16",
        "disableRollback": True,
        "displayName": "k8s1",
        "driverName": "aliyunkubernetescontainerservice",
        "endpointPublicAccess": True,
        "keyPair": "stonealy",
        "kubernetesVersion": "1.16.9-aliyun.1",
        "loginPassword": "",
        "masterAutoRenew": True,
        "masterAutoRenewPeriod": 1,
        "masterInstanceChargeType": "PostPaid",
        "masterPeriod": 1,
        "masterPeriodUnit": "",
        "masterSystemDiskCategory": "cloud_efficiency",
        "masterSystemDiskSize": 120,
        "name": "k8s1",
        "nodeCidrMask": "26",
        "numOfNodes": 3,
        "osType": "Linux",
        "platform": "CentOS",
        "proxyMode": "ipvs",
        "regionId": "cn-hangzhou",
        "resourceGroupId": "rg-aekznqknpufycli",
        "securityGroupId": "",
        "serviceCidr": "172.21.0.0/20",
        "snatEntry": False,
        "sshFlags": False,
        "timeoutMins": 0,
        "vpcId": "vpc-bp1jq37z2uky1mvyoi9up",
        "workerAutoRenew": False,
        "workerAutoRenewPeriod": 0,
        "workerDataDisk": True,
        "workerDataDiskCategory": "cloud_efficiency",
        "workerDataDiskSize": 40,
        "workerInstanceChargeType": "PostPaid",
        "workerPeriod": 0,
        "workerPeriodUnit": "",
        "workerSystemDiskCategory": "cloud_efficiency",
        "workerSystemDiskSize": 40,
        "zoneId": "cn-hangzhou-i",
        "type": "aliyunEngineConfig",
        "addons": [
            {
                "name": "flannel"
            }
        ],
        "masterVswitchIds": [
            "vsw-bp1syuluufo4mb4foxr2q",
            "vsw-bp1syuluufo4mb4foxr2q",
            "vsw-bp1syuluufo4mb4foxr2q"
        ],
        "workerVswitchIds": [
            "vsw-bp1syuluufo4mb4foxr2q"
        ],
        "workerInstanceTypes": [
            "ecs.c6.large"
        ]
    }

    # Generate the config for CCE cluster
    ackConfig = {

        "aliyunEngineConfig": ackConfig,
        "name": name,
        "type": "cluster"
    }
    print("\nACK Configuration")
    print(ackConfig)

    return ackConfig
