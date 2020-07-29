from .common import *   # NOQA
import pytest
import requests
from .entfunc import *
import subprocess
import shlex


RootDomain="stone.lb.rancher.cloud"
GlobalDnsProvider=random_test_name("global-rdns")
etcdIp = os.environ.get('RANCHER_ETCD_IP', "54.206.24.221")
#etcdUrls = os.environ.get('RANCHER_ETCD_URLS', "http://54.206.24.221:2379")
#rdnsBaserl = os.environ.get('RANCHER_RDNS_URLS', "http://54.206.24.221:9333/v1")
rootDomain = os.environ.get('RANCHER_ROOT_DOMAIN',"stone.lb.rancher.cloud")
namespace = {}
def print_object(obj):
    print('\n'.join(['%s:%s' % item for item in obj.__dict__.items()]))


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client = get_admin_client()
    clusters_local = client.list_cluster(name="local").data[0]
    clusters_k8s = client.list_cluster(name="k8s").data[0]
    create_kubeconfig(clusters_k8s)
    assert len(clusters_local) > 0 and len(clusters_k8s) > 0

    ns_name = random_test_name("rdns")
    p, ns = create_project_and_ns(ADMIN_TOKEN, clusters_k8s, random_test_name("p-rdns"), ns_name)
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)
    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["project"] = p
    namespace["client"] = client
    namespace["clusters_local"] = clusters_local
    namespace["clusters_k8s"] = clusters_k8s
    namespace["ns_name"] = ns_name

    # 配置RDNS
    set_rdns_url(client)

    def fin():
        client = get_admin_client()
        client.delete(namespace["project"])
    request.addfinalizer(fin)



def test_create_globaldnsprovider_rdns():
    create_globaldnsprovider_rdns()

def test_create_globalDnsServer_project_workload():
    create_globalDnsServer_project_workload()

def test_create_globalDnsServer_project_service():
    create_globalDnsServer_project_service()

def test_create_globalDnsServer_multiCluster():
    create_globalDnsServer_multiCluster()

def test_ingree_use_rdns_workload():
    ingree_use_rdns_workload()

def test_ingree_use_rdns_service():
    ingree_use_rdns_service()

def test_delete_globalDnsServer():
    delete_globalDnsServer()

def test_delete_globaldnsprovider_rdns():
    delete_globaldnsprovider_rdns()

def set_rdns_url(client):

    #  配置RDNS Ingress根域名
    client.update_by_id_setting(id="ingress-ip-domain", name="ingress-ip-domain", value="lb.rancher.cloud")
    # 配置RDNS 服务器地址
    rdnsBaserl = "http://" + etcdIp + ":9333/v1"
    client.update_by_id_setting(id="rdns-base-url", name="rdns-base-url", value=rdnsBaserl)

def ingree_use_rdns_workload():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    client = namespace["client"]
    # 创建workload
    wl_name, workload = create_workload_for_rdns(p_client, ns)
    # 添加ingress
    rule = {"host": "lb.rancher.cloud",
            "new": True,
            "paths":
                [{"workloadIds": [workload.id], "targetPort": "80"}]}

    ingress_name = "ingress" + "-" + wl_name
    ingress = p_client.create_ingress(
        name=ingress_name,
        namespaceId=ns.id,
        rules=[rule]
    )
    wl = wait_for_ingress_to_active(p_client, ingress)
    # 校验
    valiate_ngree_use_rdns(wl,client)

def ingree_use_rdns_service():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    client = namespace["client"]
    # 配置RDNS
    set_rdns_url(client)
    # 创建workload
    wl_name, workload = create_workload_for_rdns(p_client, ns)
    # 查看 serviceId
    services = p_client.list_service(namespaceId=ns.id).data
    service = services[0]
    # 添加ingress
    rule = {"host": "lb.rancher.cloud",
            "new": True,
            "paths":
                [{"serviceId": service.id, "targetPort": "42"}]}

    ingress_name = "ingress" + "-" + wl_name
    ingress = p_client.create_ingress(
        name=ingress_name,
        namespaceId=ns.id,
        rules=[rule]
    )
    wl = wait_for_ingress_to_active(p_client, ingress)
    # 校验
    valiate_ngree_use_rdns(wl,client)

def valiate_ngree_use_rdns(wl,client):
    hostname = wl["rules"][0]["host"]
    cluster = namespace["clusters_k8s"]
    nodes = client.list_node(clusterId=cluster.id).data
    cmd = "dig @" + etcdIp + " " + hostname + ' +short'
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    out, err = proc.communicate()
    out = str(out, encoding="utf-8")
    assert str(nodes[0]['ipAddress']) + "\n" == out



def delete_globaldnsprovider_rdns():
    # 删除globaldnsprovider
    client = namespace["client"]
    cluster = namespace["clusters_local"]
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

def delete_globalDnsServer():
    client = namespace["client"]
    cluster = namespace["clusters_local"]
    globalDns = client.list_globalDns().data
    if 0 == len(globalDns):
        create_globalDnsServer_project_workload()
    globalDnses = client.list_globalDns().data
    for globalDnsProvider in globalDnses:
        client.delete(globalDnsProvider)
    # 校验
    projects = client.list_project(clusterId=cluster.id, name='System').data
    project = projects[-1]
    assert len(projects) == 1
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    ingresses = p_client.list_ingress().data
    assert len(ingresses) == 2

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
    #create_globaldnsprovider_rdns()
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


def create_workload_for_rdns(p_client,ns):
    # 创建workload
    wl_name = random_test_name("wl-rdns")
    con = [{"name": "test1",
            "image": TEST_IMAGE}]
    workload = p_client.create_workload(name=wl_name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        deploymentConfig={})
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    return wl_name,workload

def create_globalDns_for_rdns(client):
    project = namespace["project"]
    pId = project.id
    # 添加DNS记录
    providerId = "cattle-global-data" + ":" + GlobalDnsProvider
    fqdn = random_name() + "." + RootDomain
    globalDns = {
        "ttl": 300,
        "type": "globaldns",
        "name": None,
        "projectIds": [
            pId
        ],
        "providerId": providerId,
        "fqdn": fqdn
    }
    globalDns = client.create_globalDns(globalDns)
    assert globalDns.state == "active"
    return fqdn

def create_ingress_with_workload(fqdn,workload,ns,wl_name,p_client,rule):
    # 创建Ingress规则
    annotations = {
        "rancher.io/globalDNS.hostname": fqdn
    }
    ingress_name = "ingress" + "-" + wl_name
    ingress = p_client.create_ingress(name=ingress_name,
                                      namespaceId=ns.id,
                                      rules=[rule],
                                      annotations=annotations)
    wait_for_ingress_to_active(p_client, ingress)
    return ingress_name

def validate_rdns(ingress_name,client):
    ns_name = namespace["ns_name"]
    cluster = namespace["clusters_k8s"]
    # yaml校验
    cmd = "get ingress " + ingress_name + " -n " + ns_name
    result = execute_kubectl_cmd_with_code(cmd, json_out=True, stderr=False, stderrcode=False)
    nodes = client.list_node(clusterId=cluster.id).data
    assert result["status"]["loadBalancer"]["ingress"][0]["ip"] == nodes[0]['ipAddress']

def create_globalDnsServer_project_workload():
    p_client = namespace["p_client"]
    client = namespace["client"]
    ns = namespace["ns"]
    # 创建workload
    wl_name,workload = create_workload_for_rdns(p_client,ns)
    #添加全局DNS提供商
    #create_globaldnsprovider_rdns()
    # 添加DNS记录
    fqdn = create_globalDns_for_rdns(client)

    # 创建Ingress规则
    rule = {"host": fqdn,
            "new": True,
            "paths":
                [{"workloadIds": [workload.id], "targetPort": "80"}]}
    ingress_name = create_ingress_with_workload(fqdn,workload,ns,wl_name,p_client,rule)

    validate_rdns(ingress_name,client)

def create_globalDnsServer_project_service():
    p_client = namespace["p_client"]
    client = namespace["client"]
    ns = namespace["ns"]
    # 创建workload
    wl_name,workload = create_workload_for_rdns(p_client,ns)
    #添加全局DNS提供商
    #create_globaldnsprovider_rdns()
    # 添加DNS记录
    fqdn = create_globalDns_for_rdns(client)

    # 查看 serviceId
    services = p_client.list_service(namespaceId=ns.id).data
    service = services[0]

    # 创建Ingress规则
    rule = {"host": fqdn,
            "new": True,
            "paths":
                [{"serviceId": service.id, "targetPort": "42"}]}
    annotations = {
        "rancher.io/globalDNS.hostname": fqdn
    }
    ingress_name = create_ingress_with_workload(fqdn,workload,ns,wl_name,p_client,rule)

    validate_rdns(ingress_name,client)

def create_globaldnsprovider_rdns():
    client = namespace["client"]
    clusters_local = namespace["clusters_local"]
    # 添加全局提供商
    rdnsGlobaldnsprovider = get_rdns_globaldnsprovider()
    print("globaldnsprovider rdns creation")
    client.create_globalDnsProvider(rdnsGlobaldnsprovider)
    # 校验添加的全局提供商
    projects = client.list_project(clusterId=clusters_local.id, name='System').data
    project = projects[-1]
    assert len(projects) == 1
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    appName = "systemapp" + "-" + GlobalDnsProvider
    app = wait_for_app_to_active(p_client, appName)
    assert app.state == "active"

def wait_for_app_to_active(client, app, timeout=DEFAULT_TIMEOUT):
    apps = client.list_app(name=app).data
    assert len(apps) >= 1
    application = apps[0]
    time.sleep(10)
    start = time.time()
    apps = client.list_app(uuid=application.uuid).data
    assert len(apps) == 1
    app1 = apps[0]
    while app1.state != "active":
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(10)
        apps = client.list_app(uuid=application.uuid).data
        assert len(apps) == 1
        app1 = apps[0]
    return app1

def get_rdns_globaldnsprovider():
    etcdUrls = 'http://' + etcdIp + ':2379'
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