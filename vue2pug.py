import argparse
import os

from vueconverter.formatters import VueSfcFormatter
from vueconverter.vueparser import VueParser


def process_file(filename: str):
    with open(filename, 'rt', encoding='utf-8') as file:
        contents = file.read()
        result = process_template(contents)

    with open(filename, 'wt', encoding='utf-8') as outfile:
        outfile.write(result)

    print(filename)


def process_template(content: str) -> str:
    parser = VueParser()
    parser.feed(content)

    formatter = VueSfcFormatter(parser)
    return formatter.format()


def process_path(path):
    if os.path.isfile(path):
        process_file(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in files:
                process_file(os.path.join(root, name))
    else:
        raise Exception(f'Bad path: {path}')


def run():
    parser = argparse.ArgumentParser(description='Specify files or folders')
    parser.add_argument('paths', metavar='N', type=str, nargs='+',
                        help='Paths to process')

    args = parser.parse_args()
    for path in args.paths:
        process_path(path)


run()
