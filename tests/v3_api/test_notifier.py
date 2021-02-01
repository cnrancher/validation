import pytest
from .entfunc import *

namespace = {"client": None, "cluster": None}

DingTalk = os.environ.get('RANCHER_DingTalk',
                          'https://oapi.dingtalk.com/robot/send?access_token=afcb0c030a9b7413890326060e5dc30aaeb27b4f1ae27280ee71d42429db5814')
DingTalk_Labled = os.environ.get('RANCHER_DingTalk',
                          'https://oapi.dingtalk.com/robot/send?access_token=4b4de1354b290410523dcdf3ab04a5b3775f799e8d54949e7952ec437ba2cfdb')
DingTalk_Labled_Secret = os.environ.get('RANCHER_DingTalk_Labled_Secret',
                          'SEC7a1502d28db92604b2ec1271f75add31976e8fa4670f073efff7586be6024b83')

Aliyun_Access_Key = os.environ.get('RANCHER_Aliyun_Access_Key', None)
Aliyun_Secret_Key = os.environ.get('RANCHER_Aliyun_Secret_Key', None)
Aliyun_Template_Code = os.environ.get('RANCHER_Aliyun_Template_Code', None)
Aliyun_Sign_Name = os.environ.get('RANCHER_Aliyun_Sign_Name', None)
Aliyun_To_Phone = os.environ.get('RANCHER_Aliyun_To_Phone', None)

ServiceNow_BasicAuth = os.environ.get('RANCHER_ServiceNow_BasicAuth', 'https://dev94611.service-now.com/api/597508/webhook/aaa')
ServiceNow_Admin = os.environ.get('RANCHER_ServiceNow_Admin', 'admin')
ServiceNow_Password = os.environ.get('RANCHER_ServiceNow_Password', 'UiAeXisKc9N3')
ServiceNow_NoAuth = os.environ.get('RANCHER_ServiceNow_NoAuth', 'https://dev94611.service-now.com/api/597508/webhook/bbb')

aliyunecscredential = pytest.mark.skipif(not (Aliyun_Access_Key and Aliyun_Secret_Key and Aliyun_Template_Code and Aliyun_Sign_Name),
                                   reason='ALIYUN ECS Credentials not provided, '
                                          'cannot create cluster')


def test_dingTalk():
    client = namespace['client']
    cluster = namespace['cluster']

    dingtalkConfig = {
        "type": "dingtalkConfig",
        "url": DingTalk
    }
    notifier = client.create_notifier(name=random_test_name("dingTalk"),
                                      clusterId=cluster.id,
                                      dingtalkConfig=dingtalkConfig)

    client.action(notifier, "send")
    client.delete(notifier)


def test_dingTalk_labeled():
    client = namespace['client']
    cluster = namespace['cluster']

    dingtalkConfig = {
        "type": "dingtalkConfig",
        "url": DingTalk_Labled,
        "secret": DingTalk_Labled_Secret
    }
    notifier = client.create_notifier(name=random_test_name("dingTalk-labled"),
                                      clusterId=cluster.id,
                                      dingtalkConfig=dingtalkConfig)

    client.action(notifier, "send")
    client.delete(notifier)


@aliyunecscredential
def test_aliyunSMS():
    client = namespace['client']
    cluster = namespace['cluster']

    aliyunsmsConfig = {
        "type": "aliyunsmsConfig",
        "accessKeyID": Aliyun_Access_Key,
        "accessKeySecret": Aliyun_Secret_Key,
        "templateCode": Aliyun_Template_Code,
        "signName": Aliyun_Sign_Name,
        "to": [
            Aliyun_To_Phone
        ]
    }
    notifier = client.create_notifier(name=random_test_name("aliyunSMS"),
                                      clusterId=cluster.id,
                                      aliyunsmsConfig=aliyunsmsConfig)

    client.action(notifier, "send")
    client.delete(notifier)


def test_serviceNow_basicAuth():
    client = namespace['client']
    cluster = namespace['cluster']

    servicenowConfig = {
        "type": "servicenowConfig",
        "basic_auth": {
            "username": ServiceNow_Admin,
            "password": ServiceNow_Password
        },
        "url": ServiceNow_BasicAuth,
        "username": ServiceNow_Admin,
        "password": ServiceNow_Password
    }
    notifier = client.create_notifier(name=random_test_name("serviceNow-auth"),
                                      clusterId=cluster.id,
                                      servicenowConfig=servicenowConfig)

    client.action(notifier, "send")
    client.delete(notifier)


def test_serviceNow_noAuth():
    client = namespace['client']
    cluster = namespace['cluster']

    servicenowConfig = {
        "type": "servicenowConfig",
        "basic_auth": {},
        "url": ServiceNow_NoAuth
    }
    notifier = client.create_notifier(name=random_test_name("serviceNow"),
                                      clusterId=cluster.id,
                                      servicenowConfig=servicenowConfig)

    client.action(notifier, "send")
    client.delete(notifier)


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client, cluster = get_admin_client_and_cluster()
    create_kubeconfig(cluster)

    namespace["client"] = client
    namespace["cluster"] = cluster

    def fin():
        pass
    request.addfinalizer(fin)