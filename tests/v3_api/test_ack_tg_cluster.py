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
    name = "tl-ack-tg"
    ackConfig =  {
         "accessKeyId":"LTAIV7Ekbp2jyeKV",
        "accessKeySecret":"70ySMFMoX6yoMmgZHUK0pKyLtIA08w",
        "cloudMonitorFlags":False,
        "clusterType":"ManagedKubernetes",
        "containerCidr":"172.20.0.0/16",
        "disableRollback":True,
        "displayName":"tl-ack-tg",
        "driverName":"aliyunkubernetescontainerservice",
        "endpointPublicAccess":True,
        "keyPair":"tlaly",
        "kubernetesVersion":"1.16.9-aliyun.1",
        "loginPassword":"",
        "masterAutoRenew":True,
        "masterAutoRenewPeriod":1,
        "masterInstanceChargeType":"PostPaid",
        "masterPeriod":1,
        "masterPeriodUnit":"",
        "masterSystemDiskCategory":"cloud_efficiency",
        "masterSystemDiskSize":120,
        "name":"tl-ack-tg",
        "nodeCidrMask":"26",
        "numOfNodes":3,
        "osType":"Linux",
        "platform":"CentOS",
        "proxyMode":"ipvs",
        "regionId":"cn-shenzhen",
        "resourceGroupId":"rg-aekznqknpufycli",
        "securityGroupId":"",
        "serviceCidr":"172.21.0.0/20",
        "snatEntry":True,
        "sshFlags":False,
        "timeoutMins":0,
        "vpcId":"vpc-wz9w3n6qo00qmrz490ox9",
        "workerAutoRenew":False,
        "workerAutoRenewPeriod":0,
        "workerDataDisk":True,
        "workerDataDiskCategory":"cloud_efficiency",
        "workerDataDiskSize":40,
        "workerInstanceChargeType":"PostPaid",
        "workerPeriod":0,
        "workerPeriodUnit":"",
        "workerSystemDiskCategory":"cloud_efficiency",
        "workerSystemDiskSize":40,
        "zoneId":"cn-shenzhen-e",
        "type":"aliyunEngineConfig",
        "addons":[
            {
                "name":"flannel"
            }
        ],
        "masterVswitchIds":[
            "vsw-wz92luxws1tw85eymhxft",
            "vsw-wz92luxws1tw85eymhxft",
            "vsw-wz92luxws1tw85eymhxft"
        ],
        "workerVswitchIds":[
            "vsw-wz92luxws1tw85eymhxft"
        ],
        "workerInstanceTypes":[
            "ecs.hfc6.large"
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
