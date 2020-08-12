from jsonpath import jsonpath

from .common import *   # NOQA
import pytest
import requests
from .entfunc import *

RootDomain="stone.lb.rancher.cloud"
GlobalDnsProvider=random_test_name("global-rdns")
etcdUrls = os.environ.get('RANCHER_ETCD_URLS', "http://3.34.241.83:2379")
rootDomain = os.environ.get('RANCHER_ROOT_DOMAIN',"stone.lb.rancher.cloud")


def test_create_globaldnsprovider_rdns():
    create_globaldnsprovider_rdns()

def test_create_globalDnsServer_project():
    create_globalDnsServer_project()

def test_create_globalDnsServer_multiCluster():
    create_globalDnsServer_multiCluster()

def test_delete_globalDnsServer():
    delete_globalDnsServer()

def test_delete_globaldnsprovider_rdns():
    delete_globalDnsServer()
    delete_globaldnsprovider_rdns()

def delete_globalDnsServer():
    client, cluster = get_admin_client_and_cluster(clusterName="local")
    globalDns = client.list_globalDns().data
    if 0 == len(globalDns):
        create_globalDnsServer_project()
    globalDnses = client.list_globalDns().data
    for globalDnsProvider in globalDnses:
        client.delete(globalDnsProvider)
    # 校验
    projects = client.list_project(clusterId=cluster.id, name='System').data
    project = projects[-1]
    assert len(projects) == 1
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    ingresses = p_client.list_ingress().data
    assert len(ingresses) == 0

def delete_globaldnsprovider_rdns():
    # 删除globaldnsprovider
    client,cluster= get_admin_client_and_cluster(clusterName="local")
    globalDnsProviders = client.list_globalDnsProvider().data
    if 0 == len(globalDnsProviders):
        create_globaldnsprovider_rdns()
    globalDnsProviders = client.list_globalDnsProvider().data
    for globalDnsProvider in globalDnsProviders:
        client.delete(globalDnsProvider)
    # 校验
    projects = client.list_project(clusterId=cluster.id, name='System').data
    project = projects[-1]
    assert len(projects) == 1
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    wait_for_app_to_remove(p_client)
    apps = p_client.list_app().data
    assert len(apps)==0

def wait_for_app_to_remove(client, timeout=DEFAULT_TIMEOUT):
    apps = client.list_app().data
    appsCount = len(apps)
    start = time.time()
    while appsCount != 0:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        apps = client.list_app().data
        appsCount = len(apps)

def create_globalDnsServer_multiCluster():
    # 创建项目和空间
    client = get_admin_client()
    clusters = client.list_cluster().data
    assert len(clusters) > 1
    targets = []
    p_clients = []
    nodesAddress = []
    for cluster in clusters:
        if cluster.id == "local":
            create_kubeconfig(cluster)
            continue
        nodesAddress.append(client.list_node(clusterId=cluster.id).data[0]['ipAddress'])
        ns_name = random_test_name("rdns")
        project, namespace = create_project_and_ns(ADMIN_TOKEN, cluster, random_test_name("p-rdns"), ns_name)
        p_client = get_project_client_for_token(project, ADMIN_TOKEN)
        p_clients.append(p_client)
        target = {"type":"target","projectId":project.id}
        targets.append(target)
    assert len(nodesAddress) > 0
    # 创建多集群应用
    answers = [
        {
            "type":"answer",
            "clusterId":None,
            "projectId":None,
            "values":{
                "defaultImage":"true",
                "wordpressUsername":"user",
                "wordpressPassword":"",
                "wordpressEmail":"user@example.com",
                "mariadb.enabled":"true",
                "mariadb.db.name":"wordpress",
                "mariadb.db.user":"wordpress",
                "mariadb.db.password":"",
                "mariadb.rootUser.password":"",
                "mariadb.master.persistence.enabled":"false",
                "persistence.enabled":"false",
                "ingress.enabled":"true",
                "ingress.hostname":"xip.io"
            }
        }
    ]
    multiClusterAppName = random_test_name("mywordpress")
    roles = ["project-member"]
    client.create_multiClusterApp(
        answers=answers,
        targets=targets,
        roles=roles,
        templateVersionId="cattle-global-data:library-wordpress-9.0.3",
        name=multiClusterAppName
    )
    # 等待多集群应用部署完成
    app = wait_for_multiClusterApp_to_active(client,multiClusterAppName)
    assert app.state == "active"
    # 添加全局DNS提供商
    create_globaldnsprovider_rdns()
    # 添加DNS记录
    providerId = "cattle-global-data" + ":" + GlobalDnsProvider
    multiClusterAppId = "cattle-global-data" + ":" + multiClusterAppName
    fqdn = random_name() + "." + RootDomain
    globalDns = {
        "ttl": 300,
        "type": "globaldns",
        "name": None,
        "multiClusterAppId": multiClusterAppId,
        "providerId": providerId,
        "fqdn": fqdn
    }
    globalDns = client.create_globalDns(globalDns)
    assert globalDns.state == "active"
    # 创建Ingress规则
    for (p_client,target) in zip(p_clients,app['targets']):
        workloadId = "deployment" + ":" + target['appId'] + ":" + target['appId']
        rule = {"host": fqdn,
                "new": True,
                "paths":
                    [{"workloadIds": [workloadId], "targetPort": "80"}]}
        annotations = {
            "rancher.io/globalDNS.hostname": fqdn
        }
        ingress_name = "ingress" + "-" + target['appId']
        ingress = p_client.create_ingress(name=ingress_name,
                                          namespaceId=target['appId'],
                                          rules=[rule],
                                          annotations=annotations)
        wait_for_ingress_to_active(p_client, ingress)

    # yaml校验
    cmd = "get ingress -A "
    result = execute_kubectl_cmd_with_code(cmd, json_out=True, stderr=False, stderrcode=False)
    publicEndpoints = []
    for item in  result['items']:
        publicEndpoint = item['metadata']['annotations']['field.cattle.io/publicEndpoints']
        publicEndpoint = publicEndpoint[1:-1]
        publicEndpoint = json.loads(publicEndpoint)
        if publicEndpoint['hostname'] == fqdn:
            publicEndpoints = publicEndpoint['addresses']
    assert len(set(publicEndpoints)-set(nodesAddress))==0 and len(publicEndpoints) > 0
    # nodes = client.list_node(clusterId=cluster.id).data
    # assert result["status"]["loadBalancer"]["ingress"][0]["ip"] == nodes[0]['ipAddress']



def wait_for_multiClusterApp_to_active(client,multiClusterAppName,timeout=DEFAULT_TIMEOUT):
    apps = client.list_multiClusterApp(name=multiClusterAppName).data
    assert len(apps) >= 1
    application = apps[0]

    start = time.time()
    apps = client.list_multiClusterApp(uuid=application.uuid).data
    assert len(apps) == 1
    app1 = apps[0]
    active_count = 0
    while app1.state != "active" or active_count <= 1:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        apps = client.list_multiClusterApp(uuid=application.uuid).data
        assert len(apps) == 1
        app1 = apps[0]
        if app1.state == "active":
            active_count += 1
    return app1


def create_globaldnsprovider_rdns():
    # 添加全局提供商
    client,cluster= get_admin_client_and_cluster(clusterName="local")
    #create_kubeconfig(cluster)
    rdnsGlobaldnsprovider = get_rdns_globaldnsprovider()
    print("globaldnsprovider rdns creation")
    client.create_globalDnsProvider(rdnsGlobaldnsprovider)
    # 校验添加的全局提供商
    projects = client.list_project(clusterId=cluster.id, name='System').data
    project = projects[-1]
    assert len(projects) == 1
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    appName = "systemapp" + "-" + GlobalDnsProvider
    app = wait_for_app_to_active(p_client, appName)
    assert app.state == "active"

def get_admin_client_and_cluster(clusterName):
    client = get_admin_client()
    clusters = client.list_cluster(name=clusterName).data
    assert len(clusters) > 0
    cluster = clusters[0]
    return client,cluster

def create_globalDnsServer_project():
    # 创建项目和空间
    client, cluster = get_admin_client_and_cluster(clusterName="k8s")
    create_kubeconfig(cluster)
    ns_name = random_test_name("rdns")
    project, namespace = create_project_and_ns(ADMIN_TOKEN, cluster, random_test_name("p-rdns"), ns_name)
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    pId = project.id
    #创建workload
    wl_name = random_test_name("wl-rdns")
    con = [{"name": "test1",
            "image": TEST_IMAGE}]
    workload = p_client.create_workload(name=wl_name,
                                        containers=con,
                                        namespaceId=namespace.id,
                                        deploymentConfig={})
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    #添加全局DNS提供商
    create_globaldnsprovider_rdns()
    # 添加DNS记录
    providerId = "cattle-global-data" + ":" + GlobalDnsProvider
    fqdn = random_name() + "." + RootDomain
    globalDns = {
        "ttl":300,
        "type":"globaldns",
        "name":None,
        "projectIds":[
            pId
        ],
        "providerId":providerId,
        "fqdn":fqdn
    }
    globalDns = client.create_globalDns(globalDns)
    assert globalDns.state == "active"

    # 创建Ingress规则
    rule = {"host": fqdn,
            "new" : True,
            "paths":
                [{"workloadIds": [workload.id], "targetPort": "80"}]}
    annotations = {
        "rancher.io/globalDNS.hostname": fqdn
    }
    ingress_name = "ingress" + "-" + wl_name
    ingress = p_client.create_ingress(name=ingress_name,
                                      namespaceId=namespace.id,
                                      rules=[rule],
                                      annotations=annotations)
    wait_for_ingress_to_active(p_client, ingress)

    # yaml校验
    cmd = "get ingress " + ingress_name + " -n " + ns_name
    result = execute_kubectl_cmd_with_code(cmd, json_out=True, stderr=False, stderrcode=False)
    nodes = client.list_node(clusterId=cluster.id).data
    assert result["status"]["loadBalancer"]["ingress"][0]["ip"]==nodes[0]['ipAddress']



def wait_for_app_to_active(client, app, timeout=DEFAULT_TIMEOUT):
    apps = client.list_app(name=app).data
    assert len(apps) >= 1
    application = apps[0]

    start = time.time()
    apps = client.list_app(uuid=application.uuid).data
    assert len(apps) == 1
    app1 = apps[0]
    while app1.state != "active":
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        apps = client.list_app(uuid=application.uuid).data
        assert len(apps) == 1
        app1 = apps[0]
    return app1

def prn_obj(obj):
  print('\n'.join(['%s:%s' % item for item in obj.__dict__.items()]))


def get_rdns_globaldnsprovider():
    rdnsGlobaldnsprovider = {
        "type":"globaldnsprovider",
        "providerName":"rdns",
        "provider":"rdns",
        "rdnsProviderConfig":{
            "etcdUrls":etcdUrls,
            "type":"rdnsProviderConfig"
        },
        "config":{
            "isDescriptor":True,
            "enumerable":True,
            "configurable":True,
            "altKey":"rdnsProviderConfig",
            "_dependentKeys":[
                "rdnsProviderConfig"
            ]
        },
        "name":GlobalDnsProvider,
        "rootDomain": rootDomain
    }
    return rdnsGlobaldnsprovider

