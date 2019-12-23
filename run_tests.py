import pathlib
import subprocess
import sys


this_file = pathlib.Path(__file__)
tests_path = this_file.parent / "tests"
mrst_path = this_file.parent / "mrst"
all_py_files = f"'{mrst_path}' '{tests_path}' '{this_file}'"


def main() -> None:
    cmds = [
        f"black {all_py_files}",
        f"flake8 {all_py_files} --ignore E203,E266,E501,W503,E231",
        f"mypy {all_py_files}",
        f"coverage run -m py.test {all_py_files}",
    ]
    for cmd in cmds:
        print(cmd)
        result = subprocess.call(cmd, shell=True)
        if result != 0:
            print("FAILED!")
            sys.exit(result)
    print("OK!")


if __name__ == "__main__":
    main()
