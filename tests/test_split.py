from pathlib import Path

from split import (
    create_file,
    cyclic_split,
    file_open,
    from_num_to_10Exx,
    heating_cooling_split,
)


def test_heating_cooling_split_1():
    data = [
        [0], [1], [2], [3], [4], [5], [6], [7], [8], [9],
        [9], [9], [9], [9], [9], [9], [9], [9], [9], [9],
        [9], [8], [7], [6], [5], [4], [3], [2], [1], [0],
    ]  # fmt: skip

    # 1つ先のデータとの差の絶対値が1以上の場合は昇温(+1)、それ以外は降温(-1)と判定
    # 3点分計算して点数の合計の絶対値が2以上の場合には昇温または降温と判定して分割する
    res = heating_cooling_split(data, 0, (3, 2), 1)

    print(res)
    assert res[0] == [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]
    assert res[1] == [[9], [9], [9], [9], [9], [9], [9], [9], [9], [9],
                      [9], [8], [7], [6], [5], [4], [3], [2], [1], [0]]  # fmt: skip


def test_heating_cooling_split_2():
    data = [
        [0], [1], [2], [3], [4], [5], [6], [7], [8], [9],
        [9], [9], [9], [9], [9], [9], [9], [9], [9], [9],
        [9], [8], [7], [6], [5], [4], [3], [2], [1], [0],
    ]  # fmt: skip

    # 1つ先のデータとの差の絶対値が1以上の場合は昇温(+1)または降温(-1)と判定、それ以外は一定(0)
    # 3点分計算して点数の合計の絶対値が2以上の場合には昇温または降温と判定して分割する
    res = heating_cooling_split(data, 0, (3, 2), 1, 1)

    print(res)
    assert res[0] == [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]
    assert res[1] == [[9], [8], [7], [6], [5], [4], [3], [2], [1], [0]]


def test_cyclic_split():
    data = [
        [0], [1], [2], [0], [1], [2], [0], [1], [2],
        [0], [1], [2], [0], [1], [2], [0], [1], [2],
        [0], [1], [2], [0], [1], [2], [0], [1], [2],
    ]  # fmt: skip

    res = cyclic_split(data, 3)

    assert res[0] == [[0], [0], [0], [0], [0], [0], [0], [0], [0]]
    assert res[1] == [[1], [1], [1], [1], [1], [1], [1], [1], [1]]
    assert res[2] == [[2], [2], [2], [2], [2], [2], [2], [2], [2]]


def test_from_num_to_10Exx():
    res = from_num_to_10Exx(2e10, 5)

    assert res == "10E10.301"


def test_file_open(tmp_path: Path):
    path = tmp_path / "data.txt"
    path.write_text("1,2,3\n4,5,6\n7,8,9\n")

    data, filename, dirpath, label = file_open(str(path))

    assert data == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert filename == path.stem
    assert dirpath == str(path.parent)


def test_create_file(tmp_path: Path):
    path = tmp_path / "data.txt"

    create_file(str(path), [[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    assert path.read_text() == "1,2,3\n4,5,6\n7,8,9\n"


def test_TMR_split(tmp_path: Path):
    pass
