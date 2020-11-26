import pytest
import os

from cacophonyapi.user import UserAPI

class TestUploadDownload:
    def test_upload(self, test_config):
        os.chdir('../')
        file_names = os.listdir('tests/test_data')
        for file_name in file_names:
            os.system('python3 cptv-upload.py {0} {1} {2} {3} {4} tests/test_data/{5}'.format(
                test_config.api_url,
                test_config.admin_username,
                test_config.admin_password,
                "test-group",
                "test-device",
                file_name
                )
            )

