from pathlib import Path

from measurement_manager_support import FileManager, PlotAgency


def test_FileManager(tmp_path: Path):
    file_path = tmp_path / "data.txt"

    file = FileManager()

    assert file.filepath is None

    file.write("before file create\n")
    file.set_file(file_path)
    file.write("after file create\n")
    file.save((1, 2, 3))
    file.save("save text")
    file.close()

    except_txt = """before file create
after file create
1\t2\t3
save text
"""

    assert file_path.read_text() == except_txt


def test_PlotAgency():
    plot = PlotAgency()

    info = plot.plot_info
    assert info["line"] is False
    assert info["xlog"] is False
    assert info["ylog"] is False
    assert info["renew_interval"] == 1
    assert info["legend"] is False
    assert info["flowwidth"] == 0

    plot.set_plot_info(True, True, True, 2, True, 3)

    info = plot.plot_info
    assert info["line"] is True
    assert info["xlog"] is True
    assert info["ylog"] is True
    assert info["renew_interval"] == 2
    assert info["legend"] is True
    assert info["flowwidth"] == 3
