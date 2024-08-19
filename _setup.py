#!/usr/bin/env python
#
# This script is used to generate
#     * pyproject.toml
#     * setup.cfg
#     * MANIFEST.in
#
#
import sys
import os
import textwrap
import datetime


def add_line_if_needed(file_path, line_str):

    assert isinstance(file_path, str)
    assert isinstance(line_str, str)
    assert 1 == line_str.count('\n')
    assert '\n' == line_str[-1]

    add_line_is_needed = True

    old_file_str = ''

    if os.path.isfile(file_path):

        old_file = open(file_path, 'r')
        old_file_str = old_file.read()
        old_file.close()

        if line_str in old_file_str:

            add_line_is_needed = False

    if add_line_is_needed:

        if not os.path.isfile(file_path):

            assert '' == old_file_str

            new_file_str = line_str

        else:
            assert 0 < len(old_file_str)
            assert line_str not in old_file_str

            if '\n' != old_file_str[-1]:
                line_str = '\n' + line_str

            new_file_str = old_file_str + line_str

        new_file = open(file_path, 'w')
        new_file.write(new_file_str)
        new_file.close()

        sys.stderr.write(
            textwrap.dedent(
                f'''\
                add_line_if_needed: addition WAS performed:
                    {file_path} did not previously contain line:
                        {line_str}'''
            )
        )

    else:
        sys.stderr.write(
            textwrap.dedent(
                f'''\
                add_line_if_needed: addition NOT needed: {file_path} already contains line:
                    {line_str}'''
            )
        )


def update_if_needed(file_path, new_file_str):
    '''
    If the file either does not exist or exists but its contents are
    not equal to new_file_str, truncate the file and rewrite it as
    new_file_str; otherwise, do nothing.
    '''

    assert isinstance(file_path, str)
    assert isinstance(new_file_str, str)

    update_is_needed = True

    if os.path.isfile(file_path):

        old_file = open(file_path, 'r')
        old_file_str = old_file.read()
        old_file.close()

        if old_file_str == new_file_str:

            update_is_needed = False

    if update_is_needed:

        new_file = open(file_path, 'w')
        new_file.write(new_file_str)
        new_file.close()

        sys.stderr.write(f'update_if_needed: rewrote {file_path}\n')

    else:
        sys.stderr.write(
            f'update_if_needed: checked and did NOT modify {file_path}\n'
        )


def get_readme_rst_str(name_str, github_user_str, long_desc_str):

    assert isinstance(name_str, str)
    assert isinstance(github_user_str, str)
    assert isinstance(long_desc_str, str)

    repo_url_str = f'https://github.com/{github_user_str}/{name_str}'
    pypi_url_str = f'https://pypi.org/project/{name_str}'
    docs_url_str = f'https://{github_user_str}.github.io/{name_str}'
    
    return textwrap.dedent(
        f'''\
        .. image:: https://img.shields.io/pypi/v/{name_str}
           :alt: PyPI
           :target: https://pypi.org/project/{name_str}

        .. image:: https://static.pepy.tech/badge/{name_str}
           :alt: Downloads
           :target: https://pepy.tech/project/{name_str}

        .. image:: https://img.shields.io/github/license/{github_user_str}/{name_str}
           :alt: License
           :target: https://github.com/{github_user_str}/{name_str}/blob/master/LICENSE 

        .. image:: https://img.shields.io/badge/python_3-gray
           :alt: Python 3
           :target: https://docs.python.org/3/

        .. image:: https://img.shields.io/badge/linux-gray
           :alt: Linux
           :target: https://kernel.org/

        {long_desc_str}

        Project links
        -------------

        * Repo: `{repo_url_str}
          <{repo_url_str}>`_
        * PyPI: `{pypi_url_str}
          <{pypi_url_str}>`_
        * Docs: `{docs_url_str}
          <{docs_url_str}>`_
        '''
    ).replace('\\n', '\n')


def get_index_rst_str(
    name_str,
    readme_rst_str,
    docs_source_dir_path
):
    assert isinstance(name_str, str)
    assert 0 < len(name_str)
    assert isinstance(readme_rst_str, str)
    assert 0 < len(readme_rst_str)
    assert isinstance(docs_source_dir_path, str)
    assert os.path.isdir(docs_source_dir_path)

    index_body_rst_file_path = \
        os.path.join(docs_source_dir_path, 'index_body.rst')
    assert os.path.isfile(index_body_rst_file_path), index_body_rst_file_path

    index_body_rst_file = open(index_body_rst_file_path, 'r')
    index_body_rst_str = index_body_rst_file.read()
    index_body_rst_file.close()

    return '\\\n\n' + readme_rst_str + index_body_rst_str


def get_sphinx_conf_py_str(
    name_str,
    first_copyright_year_str,
    author_str,
    version_str,
    docs_source_dir_path
):
    first_copyright_year_int = int(first_copyright_year_str)

    current_year_int = datetime.datetime.now().year
    assert isinstance(current_year_int, int)

    if (
        current_year_int < first_copyright_year_int
        or (current_year_int < 2000 or 2100 < current_year_int)
        or (first_copyright_year_int < 2000 or 2100 < first_copyright_year_int)
    ):
        assert False, \
            textwrap.dedent(
                f'''\
                first_copyright_year_int : {first_copyright_year_int}
                current_year_int         : {current_year_int}'''
            )
    elif first_copyright_year_int == current_year_int:

        copyright_str = f'{current_year_int} {author_str}'

    else:
        assert first_copyright_year_int < current_year_int

        copyright_str = f'{first_copyright_year_int}-{current_year_int} {author_str}'


    assert os.path.isdir(docs_source_dir_path), docs_source_dir_path 

    templates_dir_path = os.path.join(docs_source_dir_path, '_templates')
    if not os.path.isdir(templates_dir_path):
        os.mkdir(templates_dir_path)

    html_static_dir_path = os.path.join(docs_source_dir_path, '_static')
    if not os.path.isdir(html_static_dir_path):
        os.mkdir(html_static_dir_path)


    return textwrap.dedent(
        f'''\
        project          = '{name_str}'
        copyright        = '{copyright_str}'
        author           = '{author_str}'
        version          = '{version_str}'
        release          = '{version_str}'

        extensions       = ['sphinx.ext.autodoc']

        templates_path   = ['{os.path.basename(templates_dir_path)}']
        exclude_patterns = ['index_body.rst']

        html_theme       = 'furo'
        html_static_path = ['{os.path.basename(html_static_dir_path)}']
        '''
    )


def main():

    VERSION                   = os.environ['VERSION'                  ] 
    NAME                      = os.environ['NAME'                     ] 
    DESCRIPTION               = os.environ['DESCRIPTION'              ]
    LONG_DESC                 = os.environ['LONG_DESC'                ]
    GITHUB_USER               = os.environ['GITHUB_USER'              ] 
    AUTHOR                    = os.environ['AUTHOR'                   ] 
    AUTHOR_EMAIL              = os.environ['AUTHOR_EMAIL'             ]
    FIRST_COPYRIGHT_YEAR      = os.environ['FIRST_COPYRIGHT_YEAR'     ]
    BUILD_REQUIRES            = os.environ['BUILD_REQUIRES'           ]
    REQUIRES                  = os.environ['REQUIRES'                 ] 
    INCLUDE_FILES             = os.environ['INCLUDE_FILES'            ]
    DEFAULT_LOGGING_LEVEL_STR = os.environ['DEFAULT_LOGGING_LEVEL_STR']
    
    
    gitignore_file_path  = '.gitignore'
    docs_source_dir_path = 'docs_source'
    docs_build_dir_path  = 'docs_build'
    
    
    assert os.path.isfile(gitignore_file_path), gitignore_file_path
    assert os.path.isdir(docs_source_dir_path), docs_source_dir_path
    if not os.path.isdir(docs_build_dir_path):
        os.mkdir(docs_build_dir_path)
    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = docs_build_dir_path + '\n'
    )
    
    
    root_module_dir_name = NAME.replace('-', '_')

    root_module_dir_path = os.path.join(
        'src',
        root_module_dir_name
    )

    assert os.path.isdir(root_module_dir_path), \
        f'root_module_dir_path : {root_module_dir_path}'
    

    readme_file_path = 'README.rst'

    assert os.path.isfile(readme_file_path), \
        f'readme_file_path : {readme_file_path}'


    readme_rst_str = get_readme_rst_str(
        name_str        = NAME,
        github_user_str = GITHUB_USER,
        long_desc_str   = LONG_DESC
    )
    update_if_needed(
        file_path    = readme_file_path,
        new_file_str = readme_rst_str
    )


    index_rst_file_path = os.path.join(docs_source_dir_path, 'index.rst')
    index_rst_str = get_index_rst_str(
        name_str             = NAME,
        readme_rst_str       = readme_rst_str,
        docs_source_dir_path = docs_source_dir_path
    )
    update_if_needed(
        file_path    = index_rst_file_path,
        new_file_str = index_rst_str
    )
    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = index_rst_file_path + '\n'
    )


    sphinx_conf_py_file_path = os.path.join(docs_source_dir_path, 'conf.py')
    sphinx_conf_py_str = get_sphinx_conf_py_str(
        name_str                 = NAME,
        first_copyright_year_str = FIRST_COPYRIGHT_YEAR,
        author_str               = AUTHOR,
        version_str              = VERSION,
        docs_source_dir_path     = docs_source_dir_path
    )
    update_if_needed(
        file_path    = sphinx_conf_py_file_path,
        new_file_str = sphinx_conf_py_str
    )
    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = sphinx_conf_py_file_path + '\n'
    )

            
    pyproject_toml_file_path = 'pyproject.toml'
    pyproject_toml_str = textwrap.dedent(
        f'''\
        [build-system]
            requires      = [{BUILD_REQUIRES}]
            build-backend = "setuptools.build_meta"

        [project]
            name         = "{NAME}"
            version      = "{VERSION}"
            dynamic      = ["authors"] # specified in setup.cfg
            description  = "{DESCRIPTION}"
            license      = {{text = "MIT"}}
            dependencies = [{REQUIRES}]
            readme       = "{readme_file_path}"

        [project.scripts]
            "{root_module_dir_name}" = "{root_module_dir_name}.__main__:main"

        [project.urls]
            "Homepage" = "https://github.com/{GITHUB_USER}/{NAME}"
        '''
    )
    update_if_needed(
        file_path    = pyproject_toml_file_path,
        new_file_str = pyproject_toml_str
    )
    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = pyproject_toml_file_path + '\n'
    )


    setup_cfg_file_path = 'setup.cfg'
    setup_cfg_str = textwrap.dedent(
        f'''\
        [metadata]
            # This "url" field will be used as the "Home-page" field when
            #     "pip show <package>" is executed.
            #     There appears to be no way to set "Home-page" in pyproject.toml
            url = https://github.com/{GITHUB_USER}/{NAME}

            # Providing author and email in this file also fills in the
            #     fields more properly that are displayed with "pip show <package>"
            author       = {AUTHOR}
            author_email = {AUTHOR_EMAIL}
        [options]
            packages = find:
        [options.packages.find]
            where = src
            exclude =
                {docs_source_dir_path}
                {docs_build_dir_path}
        '''
    )
    update_if_needed(
        file_path    = setup_cfg_file_path,
        new_file_str = setup_cfg_str
    )
    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = setup_cfg_file_path + '\n'
    )


    manifest_in_file_path = 'MANIFEST.in'

    manifest_in_str = ''

    for data_file_path_suffix in INCLUDE_FILES.split(':'):

        data_file_path = os.path.join(
            root_module_dir_path,
            data_file_path_suffix
        )

        assert os.path.isfile(os.path.join('.', data_file_path))

        manifest_in_str += f'include {data_file_path}\n'

    #manifest_in_str += f'prune {docs_source_dir_path}\n'
    #manifest_in_str += f'prune {docs_build_dir_path}\n'

    update_if_needed(
        file_path    = manifest_in_file_path,
        new_file_str = manifest_in_str
    )

    add_line_if_needed(
        file_path = gitignore_file_path,
        line_str  = manifest_in_file_path + '\n'
    )


    return 0



if '__main__' == __name__:
    sys.exit(main())


