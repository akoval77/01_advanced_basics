#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

from os import listdir, path
from datetime import datetime
from collections import namedtuple
import re
import logging
import gzip
import argparse
import configparser
import itertools

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERROR_LIMIT": 0.5,

}

Log = namedtuple('Log', 'name date ext')


def to_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y%m%d")
    except ValueError:
        return None


def get_log(config: dict) -> Log:
    log_dir = config["LOG_DIR"]

    if not path.isdir(log_dir):
        return None

    files = (
                Log(name=f, date=dt, ext=m.groupdict()["ext"]) for f in listdir(log_dir)
                if (m := re.match(r'nginx-access-ui.log-(?P<logdate>[0-9]{8})(?P<ext>\.gz)?', f))
                and (dt := to_date(m.groupdict()['logdate'])) is not None
            )

    return max(files, default=None, key=lambda x: x.date)


def parse_log(source, error_limit):
    # log_format = re.compile(b'(?P<remote_addr>\S+) (?P<remote_user>\S+)  (?P<http_x_real_ip>\S+) '\
    #     b'(?P<time_local>\[.+?\]) "(?P<method>\S+) (?P<url>\S+) (?P<http>\S+)" ' \
    #     b'(?P<status>\d+) (?P<body_bytes_sent>\d+) "(?P<http_referer>.+?)" ' \
    #     b'"(?P<http_user_agent>.+?)" "(?P<http_x_forwarded_for>.+?)" ' \
    #     b'"(?P<http_X_REQUEST_ID>.+?)" "(?P<http_X_RB_USER>.+?)" (?P<request_time>\S+)')

    # log_format = re.compile(b'(?:\S+) (?:\S+)  (?:\S+) ' \
    #                         b'(?:\[.+?\]) "(?:\S+) (?P<url>\S+) (?:\S+)" ' \
    #                         b'(?P<status>\d+) (?P<body_bytes_sent>\d+) "(?:.+?)" ' \
    #                         b'"(?:.+?)" "(?:.+?)" ' \
    #                         b'"(?:.+?)" "(?:.+?)" (?P<request_time>\S+)')

    log_format = re.compile(r'(?:\S+) (?:\S+)  (?:\S+) ' \
                            r'(?:\[.+?\]) "(?:\S+) (?P<url>\S+) (?:\S+)" ' \
                            r'(?P<status>\d+) (?P<body_bytes_sent>\d+) "(?:.+?)" ' \
                            r'"(?:.+?)" "(?:.+?)" ' \
                            r'"(?:.+?)" "(?:.+?)" (?P<request_time>\S+)')

    total_cnt = 0
    parsed_cnt = 0
    error_cnt = 0

    for line in source:
        total_cnt += 1

        if m := log_format.match(line):
            parsed_cnt += 1
            yield m.groupdict()
        else:
            error_cnt += 1
            if error_cnt < 10:
                logging.debug(line.rstrip('\r\n'))

    logging.debug(f"total_cnt: {total_cnt}")
    logging.debug(f"parsed_cnt: {parsed_cnt}")
    logging.debug(f"error_cnt: {error_cnt}")

    if error_cnt > 0 and (pcnt := error_cnt/total_cnt) > error_limit:
        raise Exception(f"Too many parse errors. Error percent: {pcnt}")


def render_report(parsed, report_path, report_size):
    url_stats = itertools.groupby(sorted(parsed, key = lambda x: x['url']), key=lambda x: x['url'])
    print(len(url_stats))

    # stats = dict()
    # for rec in parsed:
    #     if stats.get(rec['url']) is None:
    #         stat = {''}
    #         stats[rec['url']] = float(rec['request_time'])


def process_log(config: dict, log: Log):
    report_name = "report-" + datetime.strftime(log.date, "%Y.%m.%d") + ".html"
    report_dir = config["REPORT_DIR"]
    logging.info(f"Start processing log {log.name}")

    report_path = path.join(report_dir, report_name)
    if path.isfile(report_path):
        logging.info(f'Report {report_path} already exists.')
        return

    log_path = path.join(config["LOG_DIR"], log.name)

    source = gzip.open(log_path, mode='rt', encoding='windows-1251') if log.ext == '.gz' \
        else open(log_path, encoding='windows-1251')

    try:
        logging.debug(source)

        parsed = parse_log(source, config["ERROR_LIMIT"])
        logging.debug(parsed)

        render_report(parsed, report_path, config["REPORT_SIZE"])

    finally:
        source.close()




def configure(config_path, config):
    config_parser = configparser.ConfigParser()
    try:
        config_parser.read(config_path)
    except Exception as e:
        print(f"Configuration file read error: {e}")
        exit(1)

    # update configuration from config file
    if 'config' in config_parser:
        config_section = config_parser['config']
        config["REPORT_SIZE"] = config_section.getint("REPORT_SIZE", config["REPORT_SIZE"])
        config["REPORT_DIR"] = config_section.get("REPORT_DIR", config["REPORT_DIR"])
        config["LOG_DIR"] = config_section.get("LOG_DIR", config["LOG_DIR"])
        config["ERROR_LIMIT"] = config_section.getfloat("ERROR_LIMIT", config["ERROR_LIMIT"])

    # setup logging configuration
    logging_filename = None
    logging_level = logging.INFO

    if 'logging' in config_parser:
        logging_section = config_parser['logging']
        logging_filename = logging_section.get('filename', None)
        logging_level = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'ERROR': logging.ERROR
        }.get(logging_section.get('level', 'INFO'), 'INFO')

    logging.basicConfig(filename=logging_filename,
                        level=logging_level,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.ini', help='Path to configuration file')
    args = parser.parse_args()

    # get configuration filename
    config_path = path.join(path.dirname(__file__), args.config) \
        if path.dirname(args.config) == "" else args.config

    # check if configuration file exists
    if not path.isfile(config_path):
        print(f"Configuration file {config_path} not found")
        exit(1)

    # read and parse configuration file
    try:
        configure(config_path, config)
    except Exception as e:
        print(f"Error {e} in file {config_path}")
        exit(1)

    # log processing
    try:
        logging.info(f'Start log analyzer')
        log = get_log(config)
        logging.debug(f'log = {log}')

        if log is not None:
            process_log(config, log)
        else:
            logging.info(f'No logs found')

        logging.info(f'Log analyzer successfully completed')
    except Exception as e:
        print(f'Log analyzer stopped with error: {e}')
        logging.exception(e)
        exit(1)


if __name__ == "__main__":
    main()
