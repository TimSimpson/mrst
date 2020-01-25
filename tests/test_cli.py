import sys
import typing as t

import pytest

from mrst import cli
from mrst import build
from mrst import gen


class FakeExit(RuntimeError):
    pass


class TestCli:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: t.Any) -> None:
        self._called_method: t.Optional[str] = None
        self._cfg_arg: t.Optional[gen.Config] = None
        self._exit_code: t.Optional[int] = None

        def _record_call(name: str) -> t.Callable[[gen.Config], int]:
            def _fake_record_call(cfg: gen.Config) -> int:
                self._called_method = name
                self._cfg_arg = cfg
                return 0

            return _fake_record_call

        def _save_exit_code(code: int) -> None:
            self._exit_code = code
            raise FakeExit()

        monkeypatch.setattr(build, "build", _record_call("build"))
        monkeypatch.setattr(gen, "generate", _record_call("generate"))

        monkeypatch.setattr(sys, "exit", _save_exit_code)

        self._monkeypatch = monkeypatch

    def _call_cli(self, args: t.List[str]) -> int:
        self._monkeypatch.setattr(sys, "argv", args)
        with pytest.raises(FakeExit):
            cli.main()

        assert self._exit_code is not None
        return self._exit_code

    @pytest.mark.parametrize(
        "args",
        [
            (["prog"]),
            (["prog", "--source"]),
            (["prog", "--source", "src"]),
            (["prog", "--skip-sphinx"]),
            (["prog", "--nonsense"]),
        ],
    )
    def test_no_args(self, capsys: t.Any, args: t.List[str]) -> None:
        assert self._call_cli(args) != 0
        captured = capsys.readouterr()
        assert "" == captured.out
        assert captured.err.startswith("usage:")

    def test_build(self, capsys: t.Any) -> None:
        assert 0 == self._call_cli(
            ["prog", "--source", "src", "--output", "out"]
        )
        captured = capsys.readouterr()
        assert "" == captured.out
        assert "" == captured.err
        assert self._called_method is not None
        assert self._cfg_arg is not None
        assert "build" == self._called_method
        assert "src" == self._cfg_arg.source_dir
        assert "out" == self._cfg_arg.output_dir
        assert "out/gen" == self._cfg_arg.gen_source_dir
        assert "out/build" == self._cfg_arg.build_dir

    def test_generate(self, capsys: t.Any) -> None:
        assert 0 == self._call_cli(
            ["prog", "--source", "src", "--output", "out", "--skip-sphinx"]
        )
        captured = capsys.readouterr()
        assert "" == captured.out
        assert "" == captured.err
        assert self._called_method is not None
        assert self._cfg_arg is not None
        assert "generate" == self._called_method
        assert "src" == self._cfg_arg.source_dir
        assert "out" == self._cfg_arg.output_dir
        assert "out/gen" == self._cfg_arg.gen_source_dir
        assert "out/build" == self._cfg_arg.build_dir
