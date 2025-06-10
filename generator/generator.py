from inspect import getsourcefile
import subprocess
import argparse
import os
import math
import arrows  # https://github.com/kala-telo/arrows.py


file_dir = os.path.dirname(getsourcefile(lambda:0))

WIDTH = 4  # Ширина дискеты в 12-битных совах, лучше этот параметр не менять
MKASM_PATH = f"{file_dir}\\mkasm.exe"  # Путь к makasm компилятору

def gen_rom(width: int, data: list[int], x_: int = 0, y_: int = 0,  rev: bool = False) -> arrows.Map:
    game = arrows.Map()
    game.chunks = {}
    for y, n in enumerate(data):
        y = y*2
        bits = [(n & (1 << i)) != 0 for i in range(width)]
        if rev:
            bits = reversed(bits)
        for x, bit in enumerate(bits):
            if not bit and x % 2 == 1:
                continue
            real_x = x
            x = (x // 2)+1

            t = arrows.ArrowType.SplitterUpRight if bit else arrows.ArrowType.Arrow
            if (orig_t := game.get(x+x_, y+y_).type) == arrows.ArrowType.SplitterUpRight:
                t = arrows.ArrowType.SplitterUpRightLeft if bit else orig_t

            game.set(x+x_, y+y_, arrows.Arrow(t, arrows.Direction.West, real_x % 2 == 0))
            game.set(x+x_, y+y_+1, arrows.Arrow(arrows.ArrowType.BlueArrow, arrows.Direction.North))
    return game

def h2o(b1, b2):
    # Convert two bytes to octal word
    return ((b1 & 0x3F) << 6) | (b2 & 0x003F)

parser = argparse.ArgumentParser(description="Компиляция программ из PAL-III и bin-simh в дискету")
parser.add_argument("--mkmode", "-m", type=str, default="pobj", help="Режим компиляции в mkasm")
parser.add_argument("--crossaddr", "-c", action="store_true", help="Генерация дискеты для RAM с перекрёстной адресацией")
parser.add_argument("--full", "-f", action="store_true", help="Генерировать сразу весь дисковод со вставленными дискетами")
parser.add_argument("--pal", "-P", action="store_true", help="Генерировать дискету из PAL-III")
parser.add_argument("--po", "-p", action="store_true", help="Генерировать дискету из набора 8-ричных кодов")
parser.add_argument("--bin", "-b", action="store_true", help="Генерировать дискету из бинарика simh")
parser.add_argument("infile", type=str, help="Файл программы на ассемблере")
args = parser.parse_args()

program_asm = []

def make_floppy(program_code: list[str], page_num: int):
    # Создание дискеты из списка с восьмиричными числами
    program_code = list(filter(lambda x: 0 < len(x) <= 4 and x.isdigit(), program_code))
    program_code_2 = []
    for index, code in enumerate(program_code):
        if args.crossaddr or page_num == 0:  # Переворачивание слова
            code = oct(int(bin(int(code, 8))[2:].zfill(12)[::-1], 2))[2:]

        if len(code) < 4:
            code = code.zfill(4)

        if index % WIDTH == 0:
            program_code_2.append(code)
        else:
            program_code_2[index//WIDTH] += code

    program_code_2[-1] += "0" * (4 * WIDTH - len(program_code_2[-1]))
    program_code = list(map(lambda x: int(x, 8), program_code_2))

    if not args.crossaddr and page_num > 0:  # Дискта для памяти с длинными кольцами
        floppy = gen_rom(12 * WIDTH, program_code, 1, 5)
        # Добавление шапки и корпуса дискеты
        floppy.import_("AAAMAAAAAAACCRcAABAAMABQAHAAkACwANAA8AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwIKBiACQABgAoAAoALAAOACAQ1CAUMBRAFFAUYBRwFIAUkBSgFLAUwBTQFOAU8BAAABAAEKBwAAIAJAAGACgACgAsAA4AIJBxAAMABQAHAAkACwANAA8AAAAAIAAQoHAAAgAkAAYAKAAKACwADgAgkHEAAwAFAAcACQALAA0ADwAAAAAwABCgcAACACQABgAoAAoALAAOACCQcQADAAUABwAJAAsADQAPAAAAAEAAEKBAAAIAJAAGABYgMJEBAAMABQAGEAYwBkAGUAZgBnAGgAaQBqAGsAbABtAG4AbwABAAAACwkJAAIBAgICAwIEAgYCCAIKAgwCDgIEESABMAAhATEDIgEyAyMBMwMkATQDNQM2AysBLAE8Ay0BPQJNAwEOQAFBAUIBQwFEAUUBJgJGATcBRwFIAUkAOgJdAW8DChMFASUBBwMXAicBKAM4AQkBGQEpATkAKgNKAWoFCwMbAQ0BHQEPAx8BBwNaB0wDbABuAwsBOwNPAwwBSwIuAhABWwc+AxMBXAdeAQ4AbQQDAE4CDwBfAAEABAAACQ9gAGEAYgBjAGQAZQBmAGcAaABpAGoAawBsAG0AbgBvAAIAAAABCQ4AAmAAMQBBAFEAYQBxAIEAkQChALEAwQDRAOEA8QAKAgECEQEhAAIABAAACRFgAAEAEQAhADEAQQBRAGEAAgAiADIAUgBiAAMAIwAzAFMAYwACAAEAAAkPAQARACEAMQBBAFEAYQBxAIEAkQChALEAwQDRAOEA8QACAAIAAAkPAQARACEAMQBBAFEAYQBxAIEAkQChALEAwQDRAOEA8QACAAMAAAkZAQARACEAMQBBAFEAYQBxAIEAkQChALEAwQDRAOEA8QCSAKIAwgDSAPIAkwCjAMMA0wDzAA==")
        for i in range(len(program_code) - 1):  # Добавление фигни около каждого ряда ROM
            floppy.import_("AAABAAAAAAAHBwIQByIAFAEKASAFIwAMAAECEAARBwYAAgATABIHBQATAQECJAEVAiUB", 26, 6 + i*2)
        
        for i in range(5):  # Рисование номера дискеты по битам
            if (page_num >> i) & 1:
                floppy.set(34, 57 + i*3, arrows.Arrow(arrows.ArrowType.Source))
                floppy.set(35, 57 + i*3, arrows.Arrow(arrows.ArrowType.Source))
                floppy.set(34, 58 + i*3, arrows.Arrow(arrows.ArrowType.Source))
                floppy.set(35, 58 + i*3, arrows.Arrow(arrows.ArrowType.Source))
    elif not args.crossaddr and page_num == 0:  # Нулевая страница для памяти с длинными кольцами
        floppy = gen_rom(12 * WIDTH, program_code, 1, 14)
        # Добавление шапки и корпуса дискеты
        floppy.import_("AAAMAAAAAAALCR4AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAAEAAgADAAQABQAGAAcACAAJAAoACwAMAA0ADgAPAAsPMgBjAGQAZQBmAIYBZwBoAGkAmQFKAUsDmwEtAp0BnwAHAEIBBBdSASMBJAElAYUDJgEnAZcCpwEoAYgDmAGoAIoDmgGqAIsDjAOcAawAjQOOA64AjwMBTJIBogCyAMIA0gFDAVMCkwGjArMBwwPTAUQBVAKUAaQDtAHEA9QBRQFVApUBpQO1AcUD1QFGAVYClgKmA7YBxgPWAUcBVwK3AccD1wFIAVgCeAO4AcgD2AFJAVkCuQHJA9kBOgNaAmoBugHKA9oBKwJrAbsBywPbAUwCbAG8AcwD3AFtAb0BzQPdAW4BvgHOA94BbwG/Ac8D3wEOATMHLwcKF4QBNQM3A3cBhwMpATkDeQGpAXoDOwF7AasBfAM9AU0DfQGtAX4DngE/AU8DfwGvAQ0AiQIMAlsBXQFfARMBPAI+ABACXAIuA14CBQBOAgAAAQAACQ8AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAAAAAgAACQ8AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAAAAAwAACQ8AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAAAABAAACR4AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAPEA8gDzAPQA9QD2APcA+AD5APoA+wD8AP0A/gD/AAEAAAAMCQ8AAAEAAgADAAQABQAGAAcACAAJAAoACwAMAA0ADgAPABAOIANQAiIDUgIkA1QCJgNWAigDWAJ5A+wHXQRvBN8DEwkwAJACMgA0ADYAOAB6A+0HXgduBQUGQAJCAkQCRgJIAk4B/wEBMmABsAHAA9ABYQGxAcED0QFiAZIDsgHCA9IBYwGzAcMD0wFkAbQBxAPUAWUBtQHFA9UBZgG2AcYD1gFnAacBtwHHA9cBaAGIA7gByAPYAWkAiQC5AtkAagKbAkwDLQI9AX0ArQHuAAo3cAOAATEBQQNxAYEDoQFyA6IBMwFDA3MBgwOjAXQDlAOkATUBRQN1AaUBdgOWA6YARwN4A5gDSQOZAakAKgFKAJoDqgC6AsoASwOrAfsFLAFcAmwAfAKcA6wAvAOdAL0ALgF+Ap4CrgK+A94DLwPvAwMAoAIOBSEHIwclBycHNwVXAQwGUQGRA1MBVQHcAm0FXwcLC4IBkwKVA3cAhwOoAFkA2wBNAs4B/gOfAwQOhAOFAoYDWgJbA2sAewCLAD4BjgA/AU8BfwKPAs8BDQTJBIoDjATMAM0FBwPaAOoD6wf9AAEABAAACQ/wAPEA8gDzAPQA9QD2APcA+AD5APoA+wD8AP0A/gD/AAIAAAAICQsAAAEAAgDzAAQARABkAIQApADEAOQA9AAKEiABUAKAAPAAIQMxAeEDIgHiAzMCUwIkATQCVAB0ApQAtALUACYBCwYwAUAAMgPyAwMB0wIUAwQTYABwA5AAoAGwAMAAQQJRAmECcQKBApEDoQFCAFIAYgByAIIAkgCiABMA0AMNAOADGAOxAsEBsgLCAgEB0QPSAgMAcwMCAAQAAAkn8ADxAPIA8wAEABQAJAA0AEQAVABkAHQAhACUAKQAtADEANQA5AD0ACUANQBVAGUAhQCVALUAxQDlAPUAJgA2AFYAZgCGAJYAtgDGAOYA9gACAAEAAAkPBAAUACQANABEAFQAZAB0AIQAlACkALQAxADUAOQA9AACAAIAAAkPBAAUACQANABEAFQAZAB0AIQAlACkALQAxADUAOQA9AACAAMAAAkPBAAUACQANABEAFQAZAB0AIQAlACkALQAxADUAOQA9AA=")
        for i in range(len(program_code) - 1):  # Добавление фигни около каждого ряда ROM
            floppy.import_("AAADAAAAAAAACQEQACAAAQAAAAcKAgoEKwUuAAcDGgQbBy0AHwEMAAwGEAAcBwYADQQTAB0HBQAeAQEALwECAAAAAQEBEAIgAQkBFAAkAA==", 0, 15 + i*2)
    else:  # Для памяти с перекрёстной адрессацией
        floppy = gen_rom(12 * WIDTH, program_code, 1, 14)
        # Добавление шапки дискеты
        floppy.import_("AAADAAAAAAALCR4AABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAAEAAgADAAQABQAGAAcACAAJAAoACwAMAA0ADgAPAAsPMgBjAGQAZQBmAIYBZwBoAGkAmQFKAUsDmwEtAp0BnwAHAEIBBBdSASMBJAElAYUDJgEnAZcCpwEoAYgDmAGoAIoDmgGqAIsDjAOcAawAjQOOA64AjwMBTJIBogCyAMIA0gFDAVMCkwGjArMBwwPTAUQBVAKUAaQDtAHEA9QBRQFVApUBpQO1AcUD1QFGAVYClgKmA7YBxgPWAUcBVwK3AccD1wFIAVgCeAO4AcgD2AFJAVkCuQHJA9kBOgNaAmoBugHKA9oBKwJrAbsBywPbAUwCbAG8AcwD3AFtAb0BzQPdAW4BvgHOA94BbwG/Ac8D3wEOATMHLwcKF4QBNQM3A3cBhwMpATkDeQGpAXoDOwF7AasBfAM9AU0DfQGtAX4DngE/AU8DfwGvAQ0AiQIMAlsBXQFfARMBPAI+ABACXAIuA14CBQBOAgEAAAAMCQ8AAAEAAgADAAQABQAGAAcACAAJAAoACwAMAA0ADgAPABAOIANQAiIDUgIkA1QCJgNWAigDWAJ5A+wHXQRvBN8DEwkwAJACMgA0ADYAOAB6A+0HXgduBQUGQAJCAkQCRgJIAk4B/wEBMmABsAHAA9ABYQGxAcED0QFiAZIDsgHCA9IBYwGzAcMD0wFkAbQBxAPUAWUBtQHFA9UBZgG2AcYD1gFnAacBtwHHA9cBaAGIA7gByAPYAWkAiQC5AtkAagKbAkwDLQI9AX0ArQHuAAo3cAOAATEBQQNxAYEDoQFyA6IBMwFDA3MBgwOjAXQDlAOkATUBRQN1AaUBdgOWA6YARwN4A5gDSQOZAakAKgFKAJoDqgC6AsoASwOrAfsFLAFcAmwAfAKcA6wAvAOdAL0ALgF+Ap4CrgK+A94DLwPvAwMAoAIOBSEHIwclBycHNwVXAQwGUQGRA1MBVQHcAm0FXwcLC4IBkwKVA3cAhwOoAFkA2wBNAs4B/gOfAwQQhAOFAoYDWgJbA2sAewCLAD4BjgA/AU8BfwKPAq8BvwDPAA0EyQSKA4wEzADNBQcD2gDqA+sH/QACAAAACAkKAAABAAIABABEAGQAhACkAMQA5AD0AAoUIAFQAoAA8AAhAzEB4QMiAeIDMwJTAuMDJAE0AlQAdAKUALQC1AAmASgBCwQwAUAAMgMDARQDBBFgAHADkACgAUECUQJhAnECgQKRA6EBQgBSAGIAcgCCAJIAogATANADDQDgAxgDsQLBAbICwgIBAdED0gIDAHMD")
        for i in range(len(program_code) - 1):  # Добавление фигни около каждого ряда ROM
            floppy.import_("AAADAAAAAAAACQEQACAAAQAAAAcKAgoEKwUuAAcDGgQbBy0AHwEMAAwGEAAcBwYADQQTAB0HBQAeAQEALwECAAAAAQEBEAIgAQkBFAAkAA==", 0, 15 + i*2)
        # Добавление "дна" дискеты
        floppy.import_("AAADAAAAAAAACRAAABAAEQASABMAFAAVABYAFwAYABkAGgAbABwAHQAeAB8AAQAAAAAJDxAAEQASABMAFAAVABYAFwAYABkAGgAbABwAHQAeAB8AAgAAAAAJBRAAEQASABMABAAUAA==", 0, 14 + (len(program_code) * 2))
        
        for i in range(5):  # Рисование номера дискеты по битам
            bit = (page_num >> i) & 1
            # Декоративная фигня снизу справа
            floppy.set(37, 2 + i*3 + len(program_code)*2, arrows.Arrow(arrows.ArrowType.Source if bit else arrows.ArrowType.Pulse))
            floppy.set(38, 2 + i*3 + len(program_code)*2, arrows.Arrow(arrows.ArrowType.Source if bit else arrows.ArrowType.Pulse))
            floppy.set(37, 3 + i*3 + len(program_code)*2, arrows.Arrow(arrows.ArrowType.Source if bit else arrows.ArrowType.Pulse))
            floppy.set(38, 3 + i*3 + len(program_code)*2, arrows.Arrow(arrows.ArrowType.Source if bit else arrows.ArrowType.Pulse))

            # Номер в ПЗУ
            if bit:
                if i > 0:   floppy.set(10 - i, 4, arrows.Arrow(arrows.ArrowType.SplitterUpRight, direction=arrows.Direction.East))
                else:       floppy.set(10 - i, 4, arrows.Arrow(arrows.ArrowType.BlueSplitterUpDiagonal, direction=arrows.Direction.South, flipped=True))

    return floppy.export()

def make_floppies(oct_data: list[str]):
    # Создание дискет из списка с восьмиричными числами; разбивает программу на дискеты
    if args.full:
        if args.crossaddr:
            floppy_drive = arrows.Map()
        else:
            with open(file_dir + "\\" + "floppy_drive.txt", "r") as f:
                floppy_drive = arrows.Map(f.read())
    
    for page_num in range(math.ceil(len(oct_data)/128)):
        page_content = oct_data[page_num*128:(page_num+1)*128]

        # Пропусск, если страница пустая (особенно это важно для нулевой страницы)
        if page_content == ["0"]*128 or page_content == ["0000"]:
            continue
        if page_content[0] in ["0", "0000"] and page_content[-1] in ["0", "0000"]:
            zero = True
            for i in page_content:
                if i not in ["0", "0000"]:
                    zero = False
                    break
            if zero:
                continue

        # Удаление или добавление нулей в конец дискеты
        if ((not args.crossaddr and page_num == 0) or args.crossaddr) and page_content[-1] in ["0", "0000"]:
            for i, j in enumerate(reversed(page_content)):
                if j != "0" and j != "0000":
                    page_content = page_content[:-1*i]
                    break
        if not args.crossaddr and page_num > 0:  #  and len(page_content) < 88
            page_content.extend(["0"]*(128-len(page_content)))  # 88-len(page_content)

        if args.full:
            floppy = make_floppy(page_content, page_num)
            if args.crossaddr:
                x = 0
                y = page_num * 90
            else:
                x = (33 if page_num >= 16 else 104) + ((page_num-16) if page_num >= 16 else (15-page_num)) * (38 if page_num >= 16 else 37)
                y = (10 if page_num >= 16 else 100)
            floppy_drive.import_(floppy, x, y)

            # print("\nPAGE", page_num, "(" + bin(page_num)[2:].zfill(5) + ")")
            # print(floppy_drive.export())
        else:
            print("\nPAGE", page_num, "(" + bin(page_num)[2:].zfill(5) + ")")
            floppy = make_floppy(page_content, page_num)
            print(floppy)
    
    if args.full:
        print(floppy_drive.export())

if args.pal:
    with open(args.infile, "r", encoding="utf_8_sig") as in_file:
        with open(f"{file_dir}\\program.pa", "a") as program_file:
            while True:
                line = in_file.readline()
                if not line:
                    break
                if "/" not in line:
                    line = line.replace("\n", "/\n")
                    if "/" not in line:
                        line += "/"
                program_file.write(line)
                if line[0] not in ["/", "*"] and line != "\n":
                    program_asm.append(line.split("/", maxsplit=1)[0].replace("\n", ""))
        subprocess.run(f"{MKASM_PATH} -{args.mkmode} -dump -D {file_dir}\\program.pa {file_dir}\\program.po")  # https://github.com/Rex--/mkasm

    print()

    oct_data = []
    if not os.path.exists(f"{file_dir}\\program.po"):
        os.remove(file_dir + "\\program.pa")
        exit(0)
    for i in open(f"{file_dir}\\program.po", "r").read().split("\n"):
        if len(i) == 6 and i[:2] == "17":
            oct_data.extend(["0"] * (int(i[2:6], 8) - len(oct_data)))
        elif len(i) == 0:
            continue
        else:
            oct_data.append(i)
    
    make_floppies(oct_data)

    os.remove(file_dir + "\\program.pa")
    os.remove(file_dir + "\\program.po")
elif args.bin:
    with open(args.infile, "rb") as in_file:
        content = in_file.read()  # [239:-239]
    content = content.strip(b'\x80')
    if b'\x80'in content:
        content = content[:content.index(b'\x80')-2]
    oct_data = []

    addr = 0  # Адрес ячейки, куда надо записывать инструкцию
    for i in range(0, len(content), 2):
        byte_1 = content[i]
        byte_2 = content[i+1]

        # [ byte 1 ][ byte 2 ]
        # [ZXaaaaaa][Z0aaaaaa]
        # a - octal word bits
        # X - identifier of location counter
        # Z - identifier of empty (?)

        if byte_1 & 0x80 == 0x80:  # If the first bytes is empty 0x80
            continue
        elif byte_1 & 0x40 == 0x40:  # If the word is identifier of location counter
            address = h2o(byte_1, byte_2)
            oct_data.extend(["0"] * (address - len(oct_data)))
            addr = address-1
        else:
            oct_word = oct(h2o(byte_1, byte_2))[2:].zfill(4)
            if addr > len(oct_data)-1:
                oct_data.append(oct_word)
            else:
                oct_data[addr] = oct_word
        
        addr += 1

    make_floppies(oct_data)
elif args.po:
    oct_data = []
    for i in open(args.infile, "r").read().split("\n"):
        if len(i) == 6 and i[:2] == "17":
            oct_data.extend(["0"] * (int(i[2:6], 8) - len(oct_data)))
        else:
            oct_data.append(i)
    
    make_floppies(oct_data)