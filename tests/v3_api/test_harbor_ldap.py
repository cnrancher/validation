import pytest
from .entfunc import *

CATTLE_HARBOR_CONFIG_URL = (CATTLE_API_URL + '/users?action=saveharborconfig').replace('//v3','/v3')
CATTLE_HARBOR_SERVER_URL = (CATTLE_API_URL + '/settings/harbor-server-url').replace('//v3','/v3')
CATTLE_HARBOR_ADMIN_AUTH = (CATTLE_API_URL + '/settings/harbor-admin-auth').replace('//v3','/v3')
CATTLE_HARBOR_AUTH_MODE = (CATTLE_API_URL + '/settings/harbor-auth-mode').replace('//v3','/v3')
RANCHER_HARBOR_URL = os.environ.get('RANCHER_HARBOR_URL', '')
RANCHER_HARBOR_ADMIN = os.environ.get('RANCHER_HARBOR_ADMIN', 'admin')
RANCHER_HARBOR_ADMIN_PASSWORD = os.environ.get('RANCHER_HARBOR_ADMIN_PASSWORD', 'Rancher@123456')
RANCHER_LDAP_GENERAL_USER_PASSWORD = os.environ.get('RANCHER_LDAP_GENERAL_USER_PASSWORD', 'Rancher@123')
RANCHER_GENERAL_USER_TOKEN = os.environ.get('RANCHER_GENERAL_USER_TOKEN', "token-wt7tb:nfcgx29fzphjgcrhjpqbkc29xx82jz5blhbg9gldbqch4br9gjnz87")

harborcredential = pytest.mark.skipif(not RANCHER_HARBOR_URL,
                                   reason='HARBOR URL Credentials not provided, '
                                          'cannot set harbor')
namespace = {}
headers = {"cookie": "R_SESS="+ADMIN_TOKEN}
email = "tanglei@163.com"



def print_object(obj):
    print('\n'.join(['%s:%s' % item for item in obj.__dict__.items()]))



# 设置harbor配置
@harborcredential
def test_set_http_harborconfig():
    harbor_config_r = set_harbor_config(RANCHER_HARBOR_ADMIN,
                                        RANCHER_HARBOR_ADMIN_PASSWORD,
                                        RANCHER_HARBOR_URL)
    assert harbor_config_r.status_code == 200

    harbor_server_r = set_harbor_server(RANCHER_HARBOR_URL)
    assert harbor_server_r.status_code == 200
    assert harbor_server_r.json()['value'] == RANCHER_HARBOR_URL

    harbor_auth_r = set_harbor_auth(RANCHER_HARBOR_ADMIN)
    assert harbor_auth_r.status_code == 200
    assert harbor_auth_r.json()['value'] == RANCHER_HARBOR_ADMIN

    harbor_mode_r = set_harbor_mode("db_auth")
    assert harbor_mode_r.status_code == 200
    assert harbor_mode_r.json()['value'] == "db_auth"

def set_harbor_config(username, password, harbor_url, headers = headers):
    harbor_config_json = {"username": username,
                          "serverURL": harbor_url,
                          "password": password,
                          "responseType": "json",
                          "version": ""}
    r = requests.post(CATTLE_HARBOR_CONFIG_URL,
                      json=harbor_config_json, verify=False, headers=headers)
    print(r)
    return r

def set_harbor_server(harbor_url, headers = headers):
    harbor_server_json = {"value": harbor_url,
                          "responseType": "json"}
    r = requests.put(CATTLE_HARBOR_SERVER_URL,
                     json=harbor_server_json, verify=False, headers=headers)
    print(r.json())
    return r


def set_harbor_auth(admin, headers = headers):
    harbor_auth_json = {"value": admin,
                        "responseType": "json"}
    r = requests.put(CATTLE_HARBOR_ADMIN_AUTH,
                                 json=harbor_auth_json, verify=False, headers=headers)
    print(r.json())
    return r


def set_harbor_mode(mode, headers = headers):
    harbor_mode_json = {"value": mode,
                        "responseType": "json"}
    r = requests.put(CATTLE_HARBOR_AUTH_MODE,
                                 json=harbor_mode_json, verify=False, headers=headers)
    print(r.json())
    return r

# 普通用户Harbor账号同步
@harborcredential
def test_harbor_accout_sync():
    # 普通用户Harbor账号同步
    client = namespace["general_client"]
    user = namespace["general_user"]
    client.action(user,action_name="setharborauth",email=email)
    # 校验
    re = get_haroborConfig()
    assert email in re.text

def get_haroborConfig():
    reUrl = CATTLE_TEST_URL + "/meta/harbor/" + RANCHER_HARBOR_URL.replace('//','/') + "/api/users/current"
    re = requests.get(reUrl, verify=False, headers={"cookie": "R_SESS="+RANCHER_GENERAL_USER_TOKEN})
    return re

# 普通用户修改密码
@harborcredential
def test_general_user_change_password():
    client = namespace["general_client"]
    user = namespace["general_user"]
    change_harbor_password(client,user,"Rancher@1234",RANCHER_LDAP_GENERAL_USER_PASSWORD)
    # 校验
    re = get_haroborConfig()
    assert email in re.text
    # 修改回原密码
    change_harbor_password(client,user,RANCHER_LDAP_GENERAL_USER_PASSWORD,"Rancher@1234")
    re = get_haroborConfig()
    assert email in re.text

def change_harbor_password(client,user,newPassword,oldPassword):
    re = client.action(user, action_name="updateharborauth", newPassword=newPassword,
                  oldPassword=oldPassword)
    print(re)

@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client, cluster = get_admin_client_and_cluster()
    # p, ns = create_project_and_ns(
    #     ADMIN_TOKEN, cluster, random_test_name("testharbor"))
    # p_client = get_project_client_for_token(p, ADMIN_TOKEN)

    general_p, general_ns = create_project_and_ns(
        RANCHER_GENERAL_USER_TOKEN, cluster, random_test_name("testharbor"))
    general_p_client = get_project_client_for_token(general_p, RANCHER_GENERAL_USER_TOKEN)

    general_client = get_admin_client_byToken(url=CATTLE_API_URL, token=RANCHER_GENERAL_USER_TOKEN)
    general_user = general_client.list_user().data[0]
    namespace["client"] = client
    namespace["cluster"] = cluster
    namespace["general_client"] = general_client
    namespace["general_user"] = general_user
    # namespace["p_client"] = p_client
    # namespace["ns"] = ns
    # namespace["project"] = p
    namespace["general_p"] = general_p
    namespace["general_ns"] = general_ns
    namespace["general_p_client"] = general_p_client
    def fin():
        client = get_admin_client()
        general_client = get_admin_client_byToken(url=CATTLE_API_URL, token=RANCHER_GENERAL_USER_TOKEN)
        time.sleep(30)
        general_client.delete(namespace["general_p"])
    request.addfinalizer(fin)


def get_harbor_host():
    if "https" in RANCHER_HARBOR_URL:
        harborHost = RANCHER_HARBOR_URL.replace("https://","")
    else:
        harborHost = RANCHER_HARBOR_URL.replace("http://","")
    return harborHost

def get_harbor_private_image():
    harborHost = get_harbor_host()
    return harborHost + '/autotest-private/nginx'

@harborcredential
def test_private_image_with_dockercredential():
    general_p_client = namespace["general_p_client"]
    general_ns = namespace["general_ns"]

    name = random_test_name("registry")
    registries = {get_harbor_host(): {}}
    harbor_dockercredential_label = {"rancher.cn/registry-harbor-auth": "true",
                                     "rancher.cn/registry-harbor-admin-auth": "true"}
    general_p_client.create_dockerCredential(registries=registries, name=name, labels=harbor_dockercredential_label)

    privateImage = get_harbor_private_image()
    wl = create_workload(general_p_client, general_ns, privateImage)
    assert wl.state == 'active'

def create_workload(p_client, ns, image):
    workload_name = random_test_name("harbor")
    con = [{"name": "test",
            "image": image,
            "runAsNonRoot": False,
            "stdin": True,
            "imagePullPolicy": "Always",
            }]
    workload = p_client.create_workload(name=workload_name,
                                        containers=con,
                                        namespaceId=ns.id)
    workload = wait_for_wl_to_active(p_client, workload, timeout=90)
    return workload

# 移除harbor配置
def test_remove_harborconfig():
    client = namespace["client"]
    re = client.update_by_id_setting(id="harbor-server-url", name="harbor-server-url", value="")
    # 校验
    re = get_haroborConfig()
    assert "admin" in re.text