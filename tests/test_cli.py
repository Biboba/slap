import os
from unittest import TestCase
from mock import MagicMock, patch, call
from slap import cli

mock_arcpy = MagicMock()
module_patcher = patch.dict('sys.modules', {'arcpy': mock_arcpy})
module_patcher.start()


class TestInitCli(TestCase):
    def test_default_args(self):
        with patch('slap.cli.config_builder.create_config') as mock:
            cli.main(['init'])
            mock.assert_called_once_with(
                directories=[os.getcwd()],
                filename='config.json',
                hostname='hostname',
                register_data_sources=False
            )

    def test_inputs(self):
        with patch('slap.cli.config_builder.create_config') as mock:
            cli.main(['init', 'foo', 'bar', 'baz'])
            mock.assert_called_once_with(
                directories=['foo', 'bar', 'baz'],
                filename='config.json',
                hostname='hostname',
                register_data_sources=False
            )


@patch('slap.publisher.ConfigParser.load_config')
class TestPublishCli(TestCase):

    def setUp(self):
        self.required_args = ['publish', '-u', 'user', '-p', 'pass']

    def test_throws_if_no_username(self, mock_config):
        with self.assertRaises(SystemExit):
            cli.main(['publish', '-c', 'config.json', '-p', 'pass'])

    def test_throws_if_no_password(self, mock_config):
        with self.assertRaises(SystemExit):
            cli.main(['publish', '-u', 'user', '-c', 'config.json'])

    def test_uses_git_if_both_git_and_inputs_specified(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        expected = 'bar'
        with patch('slap.publisher.Publisher.publish_input') as mock_publish:
            with patch('slap.git.get_changed_mxds') as mock_changed:
                mock_changed.return_value = [expected]
                cli.main(['publish', '-u', 'user', '-p', 'pass', '-g', 'some-hash', 'foo'])
                mock_changed.assert_called_once_with('some-hash')
                mock_publish.assert_called_once_with(expected)

    def test_uses_default_config(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        with patch('slap.cli.Publisher') as mock_publisher:
            cli.main(['publish', '-u', 'user', '-p', 'pass'])
            mock_publisher.assert_called_once_with('user', 'pass', 'config.json', None)

    def test_set_hostname(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        with patch('slap.cli.Publisher') as mock_publisher:
            cli.main(self.required_args + ['-n', 'host'])
            mock_publisher.assert_called_once_with('user', 'pass', 'config.json', 'host')

    def test_register_data_sources(self, mock_config):
        mock_config.return_value = {
            'agsUrl': 'ags/url',
            'mapServices': {'services': []},
            'gpServices': {'services': []},
            'imageServices': {'services': []}
        }
        with patch('slap.publisher.Publisher.register_data_sources') as mock_register:
            cli.main(self.required_args)
            mock_register.assert_called_once()

    def test_publish_all(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        with patch('slap.publisher.Publisher.publish_all') as mock_publish:
            cli.main(self.required_args)
            mock_publish.assert_called_once()

    def test_create_site(self , mock_config):
        mock_config.return_value = {
            'agsUrl': 'ags/url',
            'mapServices': {'services': []},
            'gpServices': {'services': []},
            'imageServices': {'services': []}
        }
        with patch('slap.api.Api.create_site') as mock_create_site:
            cli.main(self.required_args + ['-s'])
            mock_create_site.assert_called_once()

    def test_publish_inputs(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        with patch('slap.publisher.Publisher.publish_input') as mock_publish:
            input_files = ['foo', 'bar', 'baz']
            cli.main(self.required_args + input_files)
            calls = [call('foo'), call('bar'), call('baz')]
            mock_publish.assert_has_calls(calls)

    def test_publish_git(self, mock_config):
        mock_config.return_value = {'agsUrl': 'ags/url'}
        with patch('slap.cli.Publisher.publish_input') as mock_publisher:
            with patch('slap.git.get_changed_mxds') as mock_git:
                sha = 'some-hash'
                file = 'some/file'
                mock_git.return_value = [file]
                cli.main(self.required_args + ['-g', sha])
                mock_git.assert_called_once_with(sha)
                mock_publisher.assert_called_once_with(file)
