import pytest
import os
import tempfile
import subprocess

from cacophonyapi.user import UserAPI

class TestUploadDownload:
    def test_upload(self, test_config):
        os.chdir('../')
        file_names = os.listdir('tests/test_data')
        for file_name in file_names:
            #os.system('python3 cptv-upload.py {0} {1} {2} {3} {4} tests/test_data/{5}'.format(
            #    test_config.api_url,
            #    test_config.admin_username,
            #    test_config.admin_password,
            #    "test-group",
            #    "test-device",
            #    file_name
            #    )
            #)
            result = subprocess.run(
                    ['python3',
                    'cptv-upload.py',
                    test_config.api_url,
                    test_config.admin_username,
                    test_config.admin_password,
                    "test-group",
                    "test-device",
                    'tests/test_data/{0}'.format(file_name)]
                )
            assert result.returncode == 0

    
    def test_download(self, test_config):
        if os.path.exists('downloads1'):
            os.system('rm -r downloads1')

        #download_command = "python3 cptv-download.py -i \"None\" -m \"any\" -s {0} {1} {2} {3}".format(
        #                                test_config.api_url,
        #                                "downloads1",
        #                                test_config.admin_username,
        #                                test_config.admin_password,
        #                       )
        os.mkdir('downloads1')
        result = subprocess.run(
                    [
                        'python3',
                        'cptv-download.py',
                        '-i',
                        'None',
                        '-m',
                        'any',
                        '-s',
                        test_config.api_url,
                        "downloads1",
                        test_config.admin_username,
                        test_config.admin_password
                    ]
                )
        #downloaded_files = os.listdir('downloads1')
        os.system('rm -r downloads1')
       
        assert result.returncode == 0


