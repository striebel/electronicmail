import os


def get_meta_str() -> str:

    this_file_path = __file__

    assert os.path.isfile(this_file_path)

    package_module_dir_path = os.path.dirname(this_file_path)

    assert os.path.isdir(package_module_dir_path)

    meta_sh_file_path = os.path.join(package_module_dir_path, 'meta.sh')

    assert os.path.isfile(meta_sh_file_path)

    pipefd = os.pipe()

    pid = os.fork()

    if 0 == pid:

        os.close(pipefd[0])

        os.dup2(pipefd[1], 1)

        os.close(pipefd[1])

        argv = [meta_sh_file_path]

        os.execve(argv[0], argv, os.environ)

        assert False, 'os.execve(...) returned, which is unexpected'

    assert 0 < pid

    os.close(pipefd[1])

    wait_pid, retcode_raw = os.wait()

    assert wait_pid == pid

    retcode = retcode_raw >> 8

    assert 0 == retcode

    meta_bytes = b''
    while True:
        byte = os.read(pipefd[0], 1)
        if 1 == len(byte):
            meta_bytes += byte
        else:
            assert 0 == len(byte)
            break

    meta_str = meta_bytes.decode('utf-8')

    return meta_str



