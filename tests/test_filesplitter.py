from pathlib import Path

from filesplitter import FileSplitter


def test_FileSplitter(tmp_path: Path):
    path = tmp_path / "data.txt"
    path.write_text(
        """skip
skip
1,2,3,0
4,5,6,0
7,8,9,0
1,2,3,1
4,5,6,1
7,8,9,1
1,2,3,2
4,5,6,2
7,8,9,2
"""
    )

    FileSplitter(path, 2, ",").column_value_split(3).create("\t")

    path_0 = tmp_path / "0.txt"
    path_1 = tmp_path / "1.txt"
    path_2 = tmp_path / "2.txt"

    assert path_0.is_file()
    assert path_0.read_text() == "skip\nskip\n1\t2\t3\t0\n4\t5\t6\t0\n7\t8\t9\t0\n"
    assert path_1.is_file()
    assert path_1.read_text() == "skip\nskip\n1\t2\t3\t1\n4\t5\t6\t1\n7\t8\t9\t1\n"
    assert path_2.is_file()
    assert path_2.read_text() == "skip\nskip\n1\t2\t3\t2\n4\t5\t6\t2\n7\t8\t9\t2\n"
