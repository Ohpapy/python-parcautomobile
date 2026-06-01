import pytest
import yaml
import time
from kubernetes import client, config
from kubernetes.stream import stream


class KubernetesBase:

    def setup_method(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.namespace = "test-auto"
        self.pod_name = "nginx-healthcheck"
class TestSetup(KubernetesBase):

    def wait_pod_ready(self, timeout=60):
        for _ in range(timeout // 2):
            pod = self.v1.read_namespaced_pod(name=self.pod_name, namespace=self.namespace)
            if pod.status.conditions:
                for c in pod.status.conditions:
                    if c.type == "Ready" and c.status == "True":
                        return True
            time.sleep(2)
        return False
    
    def test_create_pod(self):
        with open("teste2e.yaml") as f:
            manifest = yaml.safe_load(f)

        # si un Pod traine d'un run precedent, on le supprime pour repartir propre
        try:
            self.v1.delete_namespaced_pod(name=self.pod_name, namespace=self.namespace)
            # attendre la suppression effective (404)
            for _ in range(30):
                try:
                    self.v1.read_namespaced_pod(name=self.pod_name, namespace=self.namespace)
                    time.sleep(1)
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        break
        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise

        # creer le Pod neuf (config d'origine : httpGet path / port 80)
        self.v1.create_namespaced_pod(namespace=self.namespace, body=manifest)

        # attendre qu'il soit Ready (condition Ready == True, pas la phase)
        assert self.wait_pod_ready(), "Le Pod n'est pas devenu Ready"
        print(f"Pod {self.pod_name} cree et Ready")

    def test_pod_ready(self):
        assert self.wait_pod_ready(), "Pod pas Ready"
        print("Pod est Ready")
        
class TestQEtatCluster(KubernetesBase):

    def test_api_acces(self):
        response = self.v1.get_api_resources()
        assert response is not None, "API non acces"
        print("API acces")

    def test_node_ready(self):
        nodes = self.v1.list_node().items
        assert len(nodes) > 0, "Aucun noeud"
        for node in nodes:
            for i in node.status.conditions:
                if i.type == "Ready":
                    assert i.status == "True", \
                        f"Noeud {node.metadata.name} pas Ready"
                    print(f"Noeud {node.metadata.name} Ready")
class TestEtatPod(KubernetesBase):

    def get_pod(self):
        return self.v1.read_namespaced_pod(
            name=self.pod_name,
            namespace=self.namespace
        )

    def test_list_pods(self):
        pod = self.get_pod()
        assert pod is not None, f"Pod {self.pod_name} non trouve"
        print(f"Pod {pod.metadata.name} trouve dans le namespace {self.namespace}")

    def test_pod_running(self):
        pod = self.get_pod()
        assert pod.status.phase == "Running", \
            f"Pod {pod.metadata.name} n'est pas Running"
        print(f"Pod {pod.metadata.name} est Running")
class TestHealthChecksPod(TestEtatPod):

    def test_probes(self):
        pod = self.get_pod()
        container = pod.spec.containers[0]
        assert container.liveness_probe is not None, "Pas de liveness probe"
        assert container.readiness_probe is not None, "Pas de readiness probe"
        print("Liveness et Readiness probes ok")

    def test_pod_ready(self):
        pod = self.get_pod()
        for i in pod.status.conditions:
            if i.type == "Ready":
                assert i.status == "True", "Pod pas Ready"
                print("Pod est Ready")
    
    def test_liveness_probe_works(self):
        pod = self.get_pod()
        container = pod.spec.containers[0]
        liveness = container.liveness_probe
        assert liveness.http_get.path == "/", "Mauvais path liveness"
        assert liveness.http_get.port == 80, "Mauvais port liveness"
        print(f"Liveness probe ok → path={liveness.http_get.path} port={liveness.http_get.port}")
class TestFailLivenessProbe(TestEtatPod):

    def test_liveness_fail(self):
        with open("teste2e.yaml") as f:
            manifest = yaml.safe_load(f)
        manifest["spec"]["containers"][0]["livenessProbe"] = {
            "exec": {"command": ["cat", "/usr/share/nginx/html/index.html"]},
            "initialDelaySeconds": 5,
            "periodSeconds": 10,
        }

        self.v1.delete_namespaced_pod(name=self.pod_name, namespace=self.namespace)
        time.sleep(10)
        self.v1.create_namespaced_pod(namespace=self.namespace, body=manifest)

        time.sleep(15)
        restarts_avant = self.get_pod().status.container_statuses[0].restart_count

        stream(
            self.v1.connect_get_namespaced_pod_exec,
            self.pod_name, self.namespace,
            command=["rm", "/usr/share/nginx/html/index.html"],
            stderr=True, stdout=True, stdin=False, tty=False,

        )

        time.sleep(50)

        restarts_apres = self.get_pod().status.container_statuses[0].restart_count
        assert restarts_apres > restarts_avant, "Le Pod n'a pas redemarre"
        print(f"Liveness probe en echec -> Pod redemarre (restart_count: {restarts_avant} -> {restarts_apres})")
class TestCleanup(KubernetesBase):

    def test_delete_pod(self):
        self.v1.delete_namespaced_pod(name=self.pod_name, namespace=self.namespace)
        # confirmer la suppression
        for _ in range(30):
            try:
                self.v1.read_namespaced_pod(name=self.pod_name, namespace=self.namespace)
                time.sleep(1)
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    break
        print(f"Pod {self.pod_name} supprime")