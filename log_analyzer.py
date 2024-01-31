#!/usr/bin/env python
# -*- coding: utf-8 -*-
import statistics
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

from os import listdir, path, makedirs
from datetime import datetime
from collections import namedtuple
import re
import logging
import gzip
import argparse
import configparser
import itertools
from string import Template
import json

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERROR_LIMIT": 0.5,
}

Log = namedtuple('Log', 'name date ext')


class ParseError(Exception):
    """Raised when parse error limit exceeded or some exception occurs while reading log file"""
    pass


def to_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y%m%d")
    except ValueError:
        return None


def get_log(log_dir) -> Log:

    if not path.isdir(log_dir):
        return None

    files = (
        Log(name=f, date=dt, ext=m.groupdict()["ext"]) for f in sorted(listdir(log_dir))
        if (m := re.match(r'nginx-access-ui.log-(?P<logdate>[0-9]{8})(?P<ext>\.gz)?', f))
           and (dt := to_date(m.groupdict()['logdate'])) is not None
    )

    return max(files, default=None, key=lambda x: x.date)


def parse_log(source, error_limit):

    log_format = re.compile(r'(?:\S+) (?:\S+)  (?:\S+) ' \
                            r'(?:\[.+?\]) "(?:\S+) (?P<url>\S+) (?:\S+)" ' \
                            r'(?:\d+) (?:\d+) "(?:.+?)" ' \
                            r'"(?:.+?)" "(?:.+?)" ' \
                            r'"(?:.+?)" "(?:.+?)" (?P<request_time>\S+)')

    total_cnt = 0
    parsed_cnt = 0
    error_cnt = 0

    try:
        for line in source:
            total_cnt += 1

            if m := log_format.match(line):
                parsed_cnt += 1
                yield m.groupdict()
            else:
                error_cnt += 1
                if error_cnt < 10:
                    logging.debug(line.rstrip('\r\n'))

    except (IOError, MemoryError) as e:
        logging.exception(e)
        raise ParseError(f'System error occurred: {e}, line = {total_cnt}')

    logging.debug(f"total_cnt: {total_cnt}")
    logging.debug(f"parsed_cnt: {parsed_cnt}")
    logging.debug(f"error_cnt: {error_cnt}")

    if error_cnt > 0 and (pcnt := error_cnt / total_cnt) > error_limit:
        raise ParseError(f"Too many parse errors. Error percent: {pcnt}")


def save_report(url_stats, report_path, template_path):
    with open(template_path, mode='r', encoding='windows-1251') as rt:
        report_template = rt.read()

    template = Template(report_template)
    with open(report_path, mode='w', encoding='windows-1251') as report:
        report.write(template.safe_substitute(table_json=json.dumps(url_stats)))


def render_report(parsed, report_size):
    logging.debug("Start grouping")
    urls = itertools.groupby(sorted(parsed, key=lambda x: x['url']), key=lambda x: x['url'])
    logging.debug("Finish grouping")

    logging.debug("Process groups")
    url_groups = {url: [float(x['request_time']) for x in url_requests] for url, url_requests in urls}

    logging.debug("Calculate group stats")
    url_stats = [
        {
            "count": len(times),
            "time_avg": statistics.mean(times),
            "time_max": max(times),
            "time_sum": sum(times),
            "url": url,
            "time_med": statistics.median(times),
        }
        for url, times in url_groups.items()
    ]

    # calculate totals
    logging.debug("Calculate totals")
    total_time = sum(x['time_sum'] for x in url_stats)
    total_count = sum(x['count'] for x in url_stats)

    logging.debug(f"Total time: {total_time}")
    logging.debug(f"Total count: {total_count}")

    url_stats = sorted(url_stats, key=lambda x: x['time_sum'], reverse=True)[:report_size]
    logging.debug(f"Size of url stat: {len(url_stats)}")

    for url_stat in url_stats:
        url_stat["time_avg"] = round(url_stat["time_avg"], 3)
        url_stat["time_med"] = round(url_stat["time_med"], 3)
        url_stat["time_sum"] = round(url_stat["time_sum"], 3)
        url_stat["time_perc"] = round((url_stat["time_sum"]/total_time)*100, 3)
        url_stat["count_perc"] = round((url_stat["count"]/total_count)*100, 3)

    # write top n items of url_stats to log
    top_n = 10
    logging.debug(f"Top {top_n} urls:")
    for i in range(top_n):
        logging.debug(f"{url_stats[i]}")

    return url_stats


def process_log(config: dict, log: Log, template_path: str):
    report_name = "report-" + datetime.strftime(log.date, "%Y.%m.%d") + ".html"
    report_dir = config["REPORT_DIR"]
    logging.info(f"Start processing log {log.name}")

    report_path = path.join(report_dir, report_name)
    if path.isfile(report_path):
        logging.info(f'Report {report_path} already exists.')
        return

    if not path.exists(report_dir):
        makedirs(report_dir)
    log_path = path.join(config["LOG_DIR"], log.name)

    source = gzip.open(log_path, mode='rt', encoding='windows-1251') if log.ext == '.gz' \
        else open(log_path, encoding='windows-1251')

    try:
        logging.debug(source)

        parsed = parse_log(source, config["ERROR_LIMIT"])
        logging.debug(parsed)

        stats = render_report(parsed, config["REPORT_SIZE"])

        save_report(stats, report_path, template_path)

    finally:
        source.close()


def configure(config_path, config):
    config_parser = configparser.ConfigParser()
    config_parser.read(config_path)

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
        print(f"Errors in file {config_path}\n{e}")
        exit(1)

    # check if report template exists
    template_path = path.join(path.dirname(__file__), 'report.html')
    if not path.isfile(template_path):
        print(f"Template file {template_path} not found")
        exit(1)

    # log processing
    try:
        logging.info(f'Start log analyzer')

        log = get_log(config["LOG_DIR"])
        logging.debug(f'log = {log}')

        if log is not None:
            process_log(config, log, template_path)
        else:
            logging.info(f'No logs found')

        logging.info(f'Log analyzer successfully completed')
    except Exception as e:
        print(f'Log analyzer stopped with error: {e}')
        logging.exception(e)
        exit(1)


if __name__ == "__main__":
    main()
