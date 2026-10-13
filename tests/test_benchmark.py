import pytest
from makma.benchmark import retrieval_metrics,paired_bootstrap,validation_gate,BASELINE
from makma.sandbox import DockerSandbox,validate_code


def test_known_ranking_metrics():
    m=retrieval_metrics([["b","a","c"]],[["a"]],3)
    assert m["recall"]==1 and m["precision"]==pytest.approx(1/3)
    assert m["mrr"]==.5 and m["ndcg"]==pytest.approx(1/1.584962500721156)


def test_paired_bootstrap_is_reproducible():
    assert paired_bootstrap([0,.1,.5],[.1,.2,.6])==paired_bootstrap([0,.1,.5],[.1,.2,.6])
    assert paired_bootstrap([1,1],[1,1])["ci95"]==[0,0]


def test_no_results_never_pass_validation():
    assert not validation_gate([],True)["eligible"]


@pytest.mark.parametrize("code",["import os\ndef retrieve(d,q,k): return os.listdir('/')","def retrieve(d,q,k): return open('/etc/passwd').read()","def retrieve(d,q,k): return eval('1+1')","import subprocess\ndef retrieve(d,q,k): pass","def retrieve(d,q,k): return d.__class__"])
def test_generated_code_policy(code):
    with pytest.raises(PermissionError):
        validate_code(code)


def test_sandbox_command_has_no_host_mounts_and_is_constrained():
    args=DockerSandbox().command("makma_test")
    for flag in ["--network=none","--read-only","--cap-drop=ALL","--user=65534:65534","--cpus=1","--memory=256m","--memory-swap=256m","--pids-limit=32","--pull=never","--log-driver=none"]:
        assert flag in args
    assert "--volume" not in args and "--mount" not in args
    validate_code(BASELINE)

