
import shutil


def recalc(macro,filepath):
    filepath=str(filepath)
    old_filepath=filepath+".old"
    shutil.move(filepath, old_filepath)
    old_file=open(old_filepath,"r",encoding="utf-8")
    new_file=open(filepath+".recalc","x",encoding="utf-8")
    
    skip_line_num=int(input("skip_line_num > "))
    for i in range(skip_line_num):
        new_file.write(old_file.readline())
    for l in old_file.readlines():
        data=[float(n) for n in l.split(",")]
        new_file.write(macro.recalculate(data)+"\n")

    old_file.close()
    new_file.close()

    print("recalculate completed...")