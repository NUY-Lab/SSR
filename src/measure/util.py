import datetime

from chardet.universaldetector import UniversalDetector


def get_encode_type(path: str) -> str:
    """テキストファイルの文字コードを判別する. ほぼコピペ"""
    detector = UniversalDetector()
    with open(path, mode="rb") as f:
        for binary in f:
            detector.feed(binary)
            if detector.done:
                break
    detector.close()
    encode_type = detector.result["encoding"]

    # 誤認識を回避するためにutf-8かSHIFT_JISの可能性があればそっちに変更
    confidence = 0
    for prober in detector._charset_probers:
        if prober.charset_name == "utf-8" or prober.charset_name == "SHIFT_JIS":
            if prober.get_confidence() > confidence:
                encode_type = prober.charset_name
                confidence = prober.get_confidence()

    # 日本語が入っていないコードはasciiもutf-8もSHIFT_JISも一緒なので
    # asciiと判断されるがasciiに日本語はないのでutf-8にする
    if encode_type == "ascii":
        encode_type = "utf-8"

    return encode_type


def get_date_text() -> str:
    """
    今日の日時を返す
    """

    dt_now = datetime.datetime.now()  # 日時取得

    # 日時をゼロ埋めしたりしてからファイル名の先頭につける
    year = str(dt_now.year)

    datelabel = (
        year[2]
        + year[3]
        + str(dt_now.month).zfill(2)
        + str(dt_now.day).zfill(2)
        + "-"
        + str(dt_now.hour).zfill(2)
        + str(dt_now.minute).zfill(2)
        + str(dt_now.second).zfill(2)
    )
    return datelabel
