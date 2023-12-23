import unittest
import log_analyzer
from datetime import datetime
from os import path, makedirs, remove
import shutil


class TestHelperFunctions(unittest.TestCase):
    """Class for testing helper functions: to_date, get_log, configure"""
    def setUp(self) -> None:
        """Create temp directory"""
        self.dir = path.join("./", "test_tmp")
        makedirs(self.dir)

    def tearDown(self) -> None:
        """Remove temp directory with all contents if any"""
        shutil.rmtree(self.dir)

    def test_to_date(self):
        """Test converting string in 'YYYYMMDD' format to date, in case of invalid date None is expected"""
        self.assertEqual(log_analyzer.to_date('20231222'), datetime(2023, 12, 22))
        self.assertIsNone(log_analyzer.to_date('20231332'))

    def test_get_log(self):
        """Test get_log function, it should return instance of Log class for file with the latest date in filename.
        Files with incorrect date if filename (e.g. nginx-access-ui.log-20170635 ) should be ignored.
        If no files found or log directory doesn't exist get_log should return None.
        """

        # check selection between text and gzip
        open(path.join(self.dir, 'nginx-access-ui.log-20170630'), 'a').close()
        open(path.join(self.dir, 'nginx-access-ui.log-20170630.gz'), 'a').close()
        try:
            log = log_analyzer.Log(name='nginx-access-ui.log-20170630', date=datetime(2017, 6, 30, 0, 0), ext=None)
            self.assertEqual(log_analyzer.get_log(self.dir), log)
        finally:
            remove(path.join(self.dir, 'nginx-access-ui.log-20170630'))
            remove(path.join(self.dir, 'nginx-access-ui.log-20170630.gz'))

        # check for file with invalid datetime in filename
        open(path.join(self.dir, 'nginx-access-ui.log-20170635.gz'), 'a').close()
        try:
            self.assertIsNone(log_analyzer.get_log(self.dir))
        finally:
            remove(path.join(self.dir, 'nginx-access-ui.log-20170635.gz'))

        # check selection of file with the latest date in filename
        open(path.join(self.dir, 'nginx-access-ui.log-20170701'), 'a').close()
        open(path.join(self.dir, 'nginx-access-ui.log-20170630'), 'a').close()
        open(path.join(self.dir, 'nginx-access-ui.log-20170630.gz'), 'a').close()
        open(path.join(self.dir, 'nginx-access-ui.log-20180635.gz'), 'a').close()
        try:
            log = log_analyzer.Log(name='nginx-access-ui.log-20170701', date=datetime(2017, 7, 1, 0, 0), ext=None)
            self.assertEqual(log_analyzer.get_log(self.dir), log)
        finally:
            remove(path.join(self.dir, 'nginx-access-ui.log-20170701'))
            remove(path.join(self.dir, 'nginx-access-ui.log-20170630'))
            remove(path.join(self.dir, 'nginx-access-ui.log-20170630.gz'))
            remove(path.join(self.dir, 'nginx-access-ui.log-20180635.gz'))

        # check non-existent log directory
        self.assertIsNone(log_analyzer.get_log(path.join(self.dir, '1')))

    def test_configure(self):
        """test configure function, read configuration file and updates config dictionary"""
        config_path = path.join(self.dir, 'config.ini')

        # all parameters updated from configuration file
        conf = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "ERROR_LIMIT": 0.5,
        }

        with open(config_path, 'w') as ini:
            ini.write("[config]\n")
            ini.write("REPORT_SIZE=50\n")
            ini.write("REPORT_DIR=./r\n")
            ini.write("LOG_DIR=./l\n")
            ini.write("ERROR_LIMIT=0.1\n")

        conf_expected = {
            "REPORT_SIZE": 50,
            "REPORT_DIR": "./r",
            "LOG_DIR": "./l",
            "ERROR_LIMIT": 0.1,
        }

        log_analyzer.configure(config_path, conf)
        self.assertEqual(conf, conf_expected)

        remove(config_path)

        # some parameters updated from configuration file

        conf = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "ERROR_LIMIT": 0.5,
        }

        with open(config_path, 'w') as ini:
            ini.write("[config]\n")
            ini.write("REPORT_DIR=./r\n")
            ini.write("ERROR_LIMIT=0.1\n")

        conf_expected = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./r",
            "LOG_DIR": "./log",
            "ERROR_LIMIT": 0.1,
        }

        log_analyzer.configure(config_path, conf)
        self.assertEqual(conf, conf_expected)

        remove(config_path)

        # invalid format of configuration file, exception expected
        with open(config_path, 'w') as ini:
            ini.write("REPORT_DIR=./r\n")
            ini.write("ERROR_LIMIT=0.1\n")

        conf = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "ERROR_LIMIT": 0.5,
        }

        with self.assertRaises(Exception):
            log_analyzer.configure(config_path, conf)

        remove(config_path)


if __name__ == "__main__":
    unittest.main()
