import pytest
from .entfunc import *

namespace = {"client": None, "p_client": None, "ns": None, "cluster": None, "project": None}
TEST_IMAGE = os.environ.get('RANCHER_TEST_IMAGE','jianghang8421/https-test')
HTTPS_PORT = os.environ.get('RANCHER_CON_HTTPS_PORT', 8443)
HTTP_PORT = os.environ.get('RANCHER_CON_HTTP_PORT', 8080)
headers = {"cookie": "R_SESS=" + ADMIN_TOKEN}


def test_lifecycle_postStart():
    p_client = namespace['p_client']
    postStart = {
                "type": "lifecycle",
                "tcp": False,
                "httpHeaders": [],
                "path": "/",
                "scheme": "HTTPS",
                "command": None,
                "port": HTTPS_PORT
            }
    workload, yaml = create_workload_lifecycle_hooks(postStart, None)

    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == 'active'

    con = yaml.json()['spec']['template']['spec']['containers'][0]
    lifecycle = {
              "postStart": {
                "httpGet": {
                  "path": "/",
                  "port": HTTPS_PORT,
                  "scheme": "HTTPS"
                }
              }
            }
    assert con['lifecycle'] == lifecycle


def test_lifecycle_preStop():
    p_client = namespace['p_client']
    preStop = {
                "type": "lifecycle",
                "tcp": False,
                "httpHeaders": [],
                "path": "/",
                "scheme": "HTTP",
                "command": None,
                "port": HTTP_PORT
            }
    workload, yaml = create_workload_lifecycle_hooks(None, preStop)

    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == 'active'

    con = yaml.json()['spec']['template']['spec']['containers'][0]
    lifecycle = {
              "preStop": {
                "httpGet": {
                  "path": "/",
                  "port": HTTP_PORT,
                  "scheme": "HTTP"
                }
              }
            }
    assert con['lifecycle'] == lifecycle


def test_lifecycle_http():
    p_client = namespace['p_client']
    postStart = {
                  "type": "lifecycle",
                  "tcp": False,
                  "httpHeaders": [],
                  "path": "/",
                  "scheme": "HTTP",
                  "command": None,
                  "port": HTTP_PORT
              }
    preStop = {
                "type": "lifecycle",
                "tcp": False,
                "httpHeaders": [
                    {
                        "name": "Host",
                        "value": "test.com"
                    },
                    {
                        "name": "content-type",
                        "value": "application/json"
                    }
                ],
                "path": "/",
                "scheme": "HTTP",
                "command": None,
                "port": HTTP_PORT
            }
    workload, yaml = create_workload_lifecycle_hooks(postStart, preStop)

    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == 'active'

    con = yaml.json()['spec']['template']['spec']['containers'][0]
    lifecycle = {
              "postStart": {
                "httpGet": {
                  "path": "/",
                  "port": HTTP_PORT,
                  "scheme": "HTTP"
                }
              },
              "preStop": {
                "httpGet": {
                  "path": "/",
                  "port": HTTP_PORT,
                  "scheme": "HTTP",
                  "httpHeaders": [
                    {
                      "name": "Host",
                      "value": "test.com"
                    },
                    {
                      "name": "content-type",
                      "value": "application/json"
                    }
                  ]
                }
              }
            }
    assert con['lifecycle'] == lifecycle


def test_lifecycle_https():
    p_client = namespace['p_client']
    postStart = {
                  "type": "lifecycle",
                  "tcp": False,
                  "httpHeaders": [
                      {
                          "name": "Host",
                          "value": "https.com"
                      },
                      {
                          "name": "accept",
                          "value": "application/json"
                      },
                      {
                          "name": "content-type",
                          "value": "application/json"
                      }
                  ],
                  "path": "/",
                  "scheme": "HTTPS",
                  "command": None,
                  "port": HTTPS_PORT
              }
    preStop = {
                "type": "lifecycle",
                "tcp": False,
                "httpHeaders": [],
                "path": "/",
                "scheme": "HTTPS",
                "command": None,
                "port": HTTPS_PORT
            }
    workload, yaml = create_workload_lifecycle_hooks(postStart, preStop)

    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == 'active'

    con = yaml.json()['spec']['template']['spec']['containers'][0]
    lifecycle = {
                  "postStart": {
                    "httpGet": {
                      "path": "/",
                      "port": HTTPS_PORT,
                      "scheme": "HTTPS",
                      "httpHeaders": [
                        {
                          "name": "Host",
                          "value": "https.com"
                        },
                        {
                          "name": "accept",
                          "value": "application/json"
                        },
                        {
                          "name": "content-type",
                          "value": "application/json"
                        }
                      ]
                    }
                  },
                  "preStop": {
                    "httpGet": {
                      "path": "/",
                      "port": HTTPS_PORT,
                      "scheme": "HTTPS"
                    }
                  }
                }
    assert con['lifecycle'] == lifecycle


def test_lifecycle_cmd():
    p_client = namespace['p_client']
    postStart = {
                  "type": "lifecycle",
                  "tcp": False,
                  "path": None,
                  "httpHeaders": None,
                  "command": [
                      "/bin/sh",
                      "-c",
                      "echo haha > postStart.txt"
                  ]
              }
    preStop = {
                "type": "lifecycle",
                "tcp": False,
                "path": None,
                "httpHeaders": None,
                "command": [
                    "/bin/sh",
                    "-c",
                    "echo hehe > preStop.txt"
                ]
            }
    workload, yaml = create_workload_lifecycle_hooks(postStart, preStop, 'busybox:musl')

    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == 'active'

    con = yaml.json()['spec']['template']['spec']['containers'][0]
    lifecycle = {
              "postStart": {
                "exec": {
                  "command": [
                    "/bin/sh",
                    "-c",
                    "echo haha > postStart.txt"
                  ]
                }
              },
              "preStop": {
                "exec": {
                  "command": [
                    "/bin/sh",
                    "-c",
                    "echo hehe > preStop.txt"
                  ]
                }
              }
            }
    assert con['lifecycle'] == lifecycle


def create_workload_lifecycle_hooks(postStart, preStop, image=TEST_IMAGE):
    p_client = namespace['p_client']
    ns = namespace['ns']
    name = random_test_name("lifecycle-hooks")
    con = [{"name": name,
            "image": image,
            "postStart": postStart,
            "preStop": preStop,
            "tty": True}]
    workload = p_client.create_workload(name=name,
                                            containers=con,
                                            namespaceId=ns.id,
                                            deploymentConfig={})

    yaml_url = workload['links']['yaml']
    yaml_data = requests.get(yaml_url, verify=False, headers=headers)

    return workload, yaml_data


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client, cluster = get_admin_client_and_cluster()
    create_kubeconfig(cluster)
    p, ns = create_project_and_ns(
        ADMIN_TOKEN, cluster, random_test_name("test-lifecycle-hooks"))
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)

    namespace["client"] = client
    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["cluster"] = cluster
    namespace["project"] = p

    def fin():
        client = namespace["client"]
        client.delete(namespace["project"])
    request.addfinalizer(fin)