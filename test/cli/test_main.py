import io

from pytest_mock import MockFixture

from cli.main import main


def test_main_meas(monkeypatch, mocker: MockFixture):
    meas = mocker.stub("meas")
    split = mocker.stub("split")
    recalculate = mocker.stub("recalculate")

    monkeypatch.setattr("cli.main.meas", meas)
    monkeypatch.setattr("cli.main.split", split)
    monkeypatch.setattr("cli.main.recalculate", recalculate)
    monkeypatch.setattr("sys.stdin", io.StringIO("MEAS\n"))

    main()

    meas.assert_called_once()
    split.assert_not_called()
    recalculate.assert_not_called()


def test_main_split(monkeypatch, mocker: MockFixture):
    meas = mocker.stub("meas")
    split = mocker.stub("split")
    recalculate = mocker.stub("recalculate")

    monkeypatch.setattr("cli.main.meas", meas)
    monkeypatch.setattr("cli.main.split", split)
    monkeypatch.setattr("cli.main.recalculate", recalculate)
    monkeypatch.setattr("sys.stdin", io.StringIO("SPLIT\n"))

    main()

    meas.assert_not_called()
    split.assert_called_once()
    recalculate.assert_not_called()


def test_main_recalculate(monkeypatch, mocker: MockFixture):
    meas = mocker.stub("meas")
    split = mocker.stub("split")
    recalculate = mocker.stub("recalculate")

    monkeypatch.setattr("cli.main.meas", meas)
    monkeypatch.setattr("cli.main.split", split)
    monkeypatch.setattr("cli.main.recalculate", recalculate)
    monkeypatch.setattr("sys.stdin", io.StringIO("RECALCULATE\n"))

    main()

    meas.assert_not_called()
    split.assert_not_called()
    recalculate.assert_called_once()
