
from event_provider import check_config, ConfigurationException
import pytest

def test_check_config(mocker):
    mocker.patch('event_provider.config', {})
    with pytest.raises(ConfigurationException):
        check_config()
