from pathlib import Path

import measurement_manager as mm
import measurement_manager_support as mms


def test():
    test_file_manager()


def test_file_manager():
    file_manager = mms.FileManager(Path("test"))
    testname = "testname"
    file_manager.set_filename(testname, add_date=False)
    if file_manager.filename == testname + ".txt":
        print("file_manager.filename==testname...OK")
    else:
        raise Exception

    file_manager.set_filename(testname, add_date=True)

    file_manager.write("a")
    file_manager.create_file()

    file_manager.write("b")
    file_manager.save("c")
    file_manager.save((1, 2, 3))

    file_manager.close()

    with open(file_manager._filepath, "r") as f:
        if f.read() == "abc\n1,2,3\n":
            print("file_manager IO ...OK")


if __name__ == "__main__":
    test()
