import sys
import os
import importlib.metadata
import argparse

from . import meta


def main():

    assert 'NAME' not in globals()

    exec(meta.get_meta_str())

    assert 'NAME' in globals()


    this_file_path = __file__

    assert '__main__.py' == os.path.basename(this_file_path)

    package_module_dir_path = os.path.dirname(this_file_path)


    metadata = None
    try:
        metadata = importlib.metadata.metadata(NAME)
    except importlib.metadata.PackageNotFoundError:
        pass

    name    = metadata['Name']    if metadata else 'name_not_available'
    summary = metadata['Summary'] if metadata else 'summary_not_available'
    version = metadata['Version'] if metadata else 'version_not_available'


    arg_parser = argparse.ArgumentParser(
        prog                  = name,
        description           = summary,
        formatter_class       = argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars = '@'
    )
    
    arg_parser.add_argument(
        '-V', '--version',
        action  = 'version',
        version = f'{name} {version}'
    )
    
    args = arg_parser.parse_args()


    data_dir_path = os.path.join(package_module_dir_path, 'data')

    assert os.path.isdir(data_dir_path)

    quote_file_path = os.path.join(data_dir_path, 'quote.txt')

    assert os.path.isfile(quote_file_path)

    with open(quote_file_path, 'r') as quote_file:

        quote_str = quote_file.read().strip()

    print(quote_str)
    
    return 0


if '__main__' == __name__:
    sys.exit(main())


