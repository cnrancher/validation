import pystache as pystache

from .entfunc import *  # NOQA
import pytest

ACK_ACCESS_KEY = os.environ.get('ALIYUN_ACCESS_KEY', "")
ACK_SECRET_KEY = os.environ.get('ALIYUN_SECRET_KEY', "")


ackcredential = pytest.mark.skipif(not (ACK_ACCESS_KEY and ACK_SECRET_KEY),
                                   reason='ACK Credentials not provided, '
                                          'cannot create cluster')
@ackcredential
def test_create_ack_cluster():
    client = get_admin_client()
    ackConfig = get_ack_config()
    print("Cluster creation")
    cluster = client.create_cluster(ackConfig)
    print(cluster)
    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)

    cluster_cleanup(client, cluster)

def test_get_ack_config():
    ack_config = {
        "isAlyunKubernetes": False, # False：托管集群 True：专用集群
        "accessKeyId": ACK_ACCESS_KEY,
        "accessKeySecret": ACK_SECRET_KEY,
        "clusterType": "ManagedKubernetes",
        "containerCidr": "172.20.0.0/16",
        "kubernetesVersion": "1.16.9-aliyun.1",
        "proxyMode": "ipvs",
        "serviceCidr": "172.21.0.0/20",
        "name": "ack"
    }

    path = os.getcwd() + "/v3_api/resource/ackTemplate"
    with open(path,"r") as f: # 用文件作为模板
        ackConfig = pystache.render(f.read(), ack_config)
        ackConfig = json.loads(ackConfig)
    print(ackConfig)
    return ackConfig



