from research_agent.policy import Capability, Decision, ScopePolicy


def test_v1_denies_active_testing():
    policy = ScopePolicy.load("policy/scope.yaml")
    assert policy.decision(Capability.TARGET_TEST) == Decision.DENY
    assert policy.decision(Capability.REPO_WRITE) == Decision.DENY
    assert policy.decision(Capability.EXTERNAL_SUBMIT) == Decision.DENY


def test_v1_allows_static_analysis():
    policy = ScopePolicy.load("policy/scope.yaml")
    assert policy.decision(Capability.REPO_READ) == Decision.ALLOW
    assert policy.decision(Capability.STATIC_SCAN) == Decision.ALLOW
