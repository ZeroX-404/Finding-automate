from research_agent.runtime_config import (
    RuntimeConfig,
)


def test_runtime_config_default():

    config = RuntimeConfig()

    assert config.max_retry == 2
    assert config.runtime_version == "4.2"



def test_runtime_config_from_dict():

    config = RuntimeConfig.from_dict(
        {
            "max_retry": 5
        }
    )

    assert config.max_retry == 5
