"""
分割処理に使える関数がある
"""
import math
import sys
from logging import getLogger
from os import makedirs, path

from measure.error import SSRError
from measure.util import get_encode_type

logger = getLogger(__name__)


class SplitError(SSRError):
    """分割処理関係のエラー"""


def heating_cooling_split(
    data: list[list[float]],
    T_index: int,
    sample_and_cutout_num: tuple[int, int] = (150, 120),
    step: int = 10,
    threshold: float = None,
) -> list[list[list[float]]]:
    """heating,coolingを判断して分割する関数

    Parameters
    ----------

    data: 二次元配列
        瞬間の測定値の配列が並んだ二次元配列
    T_index: int
        温度が格納されている場所のインデックス(0始まり)
    sample_num: (int, int)
        温度変化を判断するためのサンプル数と閾値
        1つ目のintは温度変化を判定するために使用するプロット点の数
        2つ目のintは昇温降温を判断するための閾値(N個の点それぞれについて前の点より温度が上がっていれば+1,下がっていれば-1,絶対値がthreshold以下なら0で合計値がこのint以上なら昇温または降温とする)
    threshold: float
        温度変化を判断するための閾値
        直前のプロットからの温度変化がこれ以下なら温度変化を0として扱う

    Returns
    -------

    new_data: 配列の配列
        分割したかたまりごとに配列につめる
    """

    if step == 0:
        step = 1

    sample_num = sample_and_cutout_num[0]
    cutout_num = sample_and_cutout_num[1]

    def temp_judge(temp_grad):
        nonlocal threshold
        # 温度が上昇していれば1, いなければ-1を代入
        value = 1 if temp_grad > 0 else -1
        if threshold is not None and abs(temp_grad) < threshold:
            value = 0
        return value

    # サンプルを入れる配列
    samples_hc = []
    count = 0
    for i in range(sample_num):
        if count >= len(data) - step:
            logger.warning(
                "データ数が少なすぎるかsample数が多すぎます. "
                f"必要最小データ数は{sys._getframe().f_code.co_name}の引数から設定できます"
            )
            return [data]

        temp_grad = data[count + step][T_index] - data[count][T_index]

        samples_hc.append(temp_judge(temp_grad))
        count += 1

    # 一個前の昇温降温状態. 一度温度勾配がなくなった後に再び同じ方向に温度変化した場合に対応
    previous_state = -5
    # 全体としての状態, heatingなら1,coolingなら-1,どっちでもなければ0
    state = 0
    # 分割する点をいれる配列
    split_points_hc = []

    while True:
        # 温度変化のサンプルの和をとる
        sum_count = sum(samples_hc)

        # 閾値を設定してそれを超えるかどうかでheating,coolingを判定
        if sum_count > cutout_num:
            new_state = 1
        elif sum_count < cutout_num * (-1):
            new_state = -1
        else:
            new_state = 0

        # 一個前の状態と違うならsplit_points_hcに情報を入れる
        if state != new_state:
            if previous_state == new_state:
                del split_points_hc[-1]
            else:
                # 一個前の状態がheating or cooling なら 分割の終わり
                if state != 0:
                    split_points_hc.append(count)
                # 今の状態がheating or cooling なら 分割の始まり
                if new_state != 0:
                    split_points_hc.append(count - sample_num)
                    previous_state = new_state

        # countが最後まできたら終了
        if count >= len(data) - step:
            # 最後の分割範囲が閉じてなければ閉じる
            if len(split_points_hc) % 2 == 1:
                split_points_hc.append(count)
            break

        state = new_state
        temp_grad = data[count + step][T_index] - data[count][T_index]
        samples_hc[count % sample_num] = temp_judge(temp_grad)
        count += 1

    new_data = []
    # split_points_hcの情報に基づいて分割
    for i in range(0, len(split_points_hc), 2):
        new_data.append(data[split_points_hc[i] : split_points_hc[i + 1]])

    return new_data


def cyclic_split(data: list[float], cycle_num: int) -> list[list[float]]:
    """周期的に分割

    Parameters
    ----------

    data: List[float]
        分割する配列
    cycle_num: int
        分割の周期

    Returns
    -------

    new_data: 配列の配列
    """

    count = 0
    max_num = len(data)

    new_data = [[] for _ in range(cycle_num)]

    while True:
        # データを上から順番に周期的に振り分け
        for i in range(cycle_num):
            new_data[i].append(data[count])
            count += 1
            if count >= max_num:
                break
        else:
            # forループを正常に抜けたらcontinue
            continue

        # breakでforループを抜けたときだけここが実行される
        break

    return new_data


def from_num_to_10Exx(num: int | float, significant_digits=2) -> str:
    """数字を10Exx形式にして文字列として返す

    Parameters
    ----------

    num : int | float
        10Exx形式に変換させたい数字
    significant_digits: int
        変換後の有効数字. significant_digits=3なら10E3.49などが返る

    Returns
    -------

    index_txt: 10Exx形式に変換した文字列
    """

    logf = math.log10(num)  # 対数をとる
    abs_digits = significant_digits + 1 - math.ceil(math.log10(abs(logf)))
    # 有効数字におとす
    index_txt = str(round(logf, abs_digits))

    if abs_digits > 0:
        while significant_digits >= len(index_txt):
            index_txt = index_txt + "0"

    index_txt = "10E" + index_txt
    return index_txt


def file_open(filepath: str) -> tuple[list[list[float]], str, str, str]:
    """ファイルを開いて中身を二次元配列で返す

    Parameter
    ---------
    filepath : string
        見鋳込むファイルのpath(絶対パスを想定)

    Returns
    -------
    data : 二次元配列
        ファイルの中身を二次元配列に変換した物
    filename: str
        開いたファイルの名前
    dirpath: str
        開いたファイルの存在するフォルダのパス
    label: str
        ファイル中の数字以外が書いてある行のテキスト
    """

    # ファイルのpathからディレクトリ名を取得
    dirpath = path.dirname(filepath)
    # fileのpathからファイル名(拡張子抜き)を取得
    filename = path.splitext(path.basename(filepath))[0]

    # ファイルを開く
    file = open(filepath, "r", encoding=get_encode_type(filepath))

    with open(filepath, "r", encoding=get_encode_type(filepath)) as f:
        # label =file.readline()+file.readline()#最初の2行はラベルだとしてそこは抜き出す
        label = ""
        data = []
        num_label = 0
        num_data = 0
        for line in f:
            l = line.strip()

            # 空行なら次の行へ
            if l == "":
                continue

            try:
                # ","で分割して配列にする
                # 文字列からfloatに変換
                data.append([float(s) for s in l.split(",")])
                num_data += 1
            except Exception:
                label += line
                num_label += 1

    # TODO: use rich.Console
    logger.info(f"非データ行: {num_label}, データ行: {num_data}")

    if num_data == 0:
        raise SplitError("データ行が0行です. 読み取りに失敗しました.")

    return data, filename, dirpath, label


def create_file(filepath: str, data: list[list], label=""):
    """新規ファイル作成. フォルダがない場合は作る

    Parameters
    ----------

    filepath: str
        作成するファイルのパス. パスに既にファイルが存在していればエラー
    data: 配列
        ファイルに入力するデータ配列
    label: str
        ファイル冒頭のラベル
    """

    def array2d_to_text(array2d):
        text = ""
        for array1d in array2d:
            text = ",".join(map(str, array1d)) + "\n"

        return text

    dirpath = path.dirname(filepath)
    makedirs(dirpath, exist_ok=True)
    if path.isfile(filepath):
        raise SplitError(
            f"新規作成しようとしたファイル{filepath}は既に存在しています.削除してからやり直してください.\n"
            "解決できない場合はcyclic_splitの分割数などを見直してみてください"
        )

    with open(filepath, "x", encoding="utf-8") as f:
        f.write(label)
        f.write(array2d_to_text(data))


def TMR_bunkatsu(
    filepath,
    T_index,
    f_index,
    freq_num=16,
    sample_and_cutout_num=(150, 120),
    step=10,
    threshold=0,
):
    logger.warning("TMR_bunkatsuは非推奨です。TMR_splitを使用してください。")
    TMR_split(
        filepath,
        T_index,
        f_index,
        freq_num,
        sample_and_cutout_num,
        step,
        threshold,
    )


def TMR_split(
    filepath: str,
    T_index: int,
    f_index: int,
    freq_num: int = 16,
    sample_and_cutout_num: tuple[int, int] = (150, 120),
    step: int = 10,
    threshold: float = 0,
    name_temperaturesplitfolder: str = None,
    name_frequencesplitfile: str = None,
):
    """TMR用の分割関数.

    Parameter
    ---------

    filepath: str
        分割元のファイルのパス
    T_index: int
        分割元のファイルの温度値の列番号(左から0始まり)
    f_index: int
        分割元のファイルの周波数値の列番号(左から0始まり)
    freq_num: int
        周波数の分割数
    sample_and_cutout_num: (int, int)
        1つ目のintは温度変化を判定するために使用するプロット点の数
        2つ目のintは昇温降温を判断するための閾値(N個の点それぞれについて前の点より温度が上がっていれば+1,下がっていれば-1,絶対値がthreshold以下なら0で合計値がこのint以上なら昇温または降温とする)
    step: int
        昇温降温判定でstep分離れたプロットと温度比較を行う.
    threshold: float
        昇温降温判定でthreshold以下の温度変化は温度変化なしとみなす
    name_temperaturesplitfolder: str
        温度分割後のフォルダ名(Noneのときは分割前のファイル名を使う)
    name_frequencesplitfile: str
        周波数分割後のファイル名(Noneのときは分割前のファイル名を使う)
    """

    # TODO: use rich.Console
    logger.info("bunkatsu start...")

    # ファイルを開いて配列として取得
    data, filename, dirpath, label = file_open(filepath)
    count = 0
    # 昇温降温で分割
    for split_data in heating_cooling_split(
        data,
        T_index=T_index,
        sample_and_cutout_num=sample_and_cutout_num,
        step=step,
        threshold=threshold,
    ):
        displacement = split_data[len(split_data) - 1][T_index] - split_data[0][T_index]
        state = "heating" if displacement > 0 else "cooling"

        if name_temperaturesplitfolder is None:
            name_temperaturesplitfolder = filename
        if name_frequencesplitfile is None:
            name_frequencesplitfile = filename

        new_dir = path.join(
            dirpath, f"{name_temperaturesplitfolder}-{str(count)}-{state}"
        )

        new_filepath = path.join(
            new_dir, f"{name_frequencesplitfile}_{str(count)}_{state}_all.txt"
        )
        create_file(filepath=new_filepath, data=split_data, label=label)

        # 周波数でさらに分割
        for split_split_data in cyclic_split(split_data, cycle_num=freq_num):
            freq = split_split_data[0][f_index]

            freq = from_num_to_10Exx(freq, significant_digits=3)

            # ファイルのパスを設定
            new_filepath = path.join(
                new_dir, f"{ name_frequencesplitfile}_{str(count)}_{state}_{freq}Hz.txt"
            )

            create_file(filepath=new_filepath, data=split_split_data, label=label)

        count += 1

    print("file has been completely splitted!!")
