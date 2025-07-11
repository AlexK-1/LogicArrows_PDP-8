# Навигация
* [README.md](README.md) - введение, характеристики, готовые программы, дополнительная литература
* [structure.md](structure.md) - комплектация компьютера, структура и характеристики его частей
* **[starting-and-floppies.md](starting-and-floppies.md) - как запустить программу, генерация дискет**
* [commands.md](commands.md) - система команд PDP-8

# Как запустить программу
Надо выполнить несколько шагов:
1. Взять уже созданную (на карте компьютера к нужным страницам памяти уже подключено несколько дискет с программами из папок `/bin` и `/asm` этого репозитория) или сгенерировать свою дискету (см. [Генерация дискет](#генерация-дискет)) или несколько дискет.
2.  1. Если вы используете память RAM 4096 A, вам надо вставить дискету с определённым номером в порт дисковода с тем же номером так, чтобы их корпуса полностью совпадали, сделайте это со всеми дискетами, далее нужно нажать на кнопку в левом верхнем углу дисковода и дождаться, пока не погасну индикаторы загрузки на всех дискетах.
    2. Если у вас RAM 128 B, вам надо подключить каждую дискету к странице памяти с тем же номером, что и у дискеты, присоединив её к проводу слева корпуса памяти, после чего надо нажать кнопку загрузки на каждой дискете и дождаться, пока не погаснут индикаторы загрузки на всех дискетах.
3. Когда все данные загрузятся в память, нужно занести в счётчик команд адрес первой команды программы, с которой должно начаться её выполнение. Для этого введите на клавишном регистре нужный адрес и нажмите кнопку "Зан. адр.". У большинства программ начальным адресом является 0200<sub>8</sub>, он предустановлен в процессоре, и если у вашей программы начало имеет этот адрес, вам ничего делать не надо.
4. Снимите блокировку между процессором и памятью, нажав на кнопку "озу вкл." в самом низу процессора у его соединения с памятью.
5. Нажмите на кнопку "Пуск" на панели управления, загорится индикатор "Работа", и компьютер начнёт выполнять программу.
6. Если вы захотите запустить другую программу, прежде чем загружать её в память, перезагрузите страницу с игрой или нажмите клавишу `N` на своей (реальной) клавиатуре, чтобы сбросить карту.

# Генерация дискет

Для того чтобы создавать дискеты я написал небольшую программу на языке программирования Python, находящуюся в файле `generator/generator.py`. Чтобы его запустить используйте команду `python generator/generator.py`.

Имеет один обязательный аргумент: исходный файл с кодом для генерации дискеты.

Необязательные аргументы:
* `--help` `-h` Выводит справку.
* `--crossaddr` `-c` Создание дискеты для памяти RAM 128 B, по умолчанию (без флага) создаётся для памяти RAM 4096 A.
* `--full` `-f` Генерация сразу всего дисковода со вставленными дискетами, важно для больших программ в дискетах для RAM 4096 A.
* `--pal` `-P` Генерация дискеты по файлу с кодом на ассемблере PAL-III, использует компилятор [mkasm](https://github.com/Rex--/mkasm).
* `--po` `-p` Создание дискеты по набору 8-ричных чисел, файл должен содержать только 8-ричные числа, находящиеся каждое на своей строке, то есть разделённые символом \n
* `--bin` `-b` генерация по двоичному файлу симулятора [simh](https://github.com/simh/simh).
* `--mkmode` `-m` Указывает на режим компиляции для mkasm, обычно его не стоит использовать.
* `--debug` `-d` Выводит отладочную информацию: адреса и значения всех ячеек памяти и выполняет некий вид упрощённого дизассемблинга

В результате программа выводит код дискеты для каждой страницы памяти, которые можно скопировать и вставить на карту в Стрелочках или сразу весь дисковод с дискетами, если был указан параметр `--full`.

## pal
Как было сказано ранее, при указании параметра `--pal` будет происходить конвертация из программы, написанной на ассемблере PAL-III в дискету, используя компилятор mkasm. При этом файл `mkasm.exe` должен находиться в папке с python файлом программы. Для этого вам понадобится самостоятельно скомпилировать mkasm из исходников.

Пример генерации для памяти RAM 4096 A программы hello_world.pal:
```shell
python generator/generator.py --pal asm/hello_world.pal
```

Та же программа, но генерация всего дисковода:
```shell
python generator/generator.py --pal --full asm/hello_world.pal
```

## po
Генерация из восьмеричных кодов. Обычные данные указываются просто как число в 8-ричной системе исчисления. Коды переходов (установки счётчика команд, в PAL-III делается оператором `*`) указываются как 6-значное число, первые две цифры которых равны 17. Например, переход к адресу 200<sub>8</sub> (в ассемблере это бы реализовывалось как `*200`) записывается как `170200`.

Пример генерации для памяти RAM 128 B программы hello_world.po (такого файла на самом деле нет, просто для примера):
```shell
python generator/generator.py --po po/hello_world.po --crossaddr
```

## bin
Создание дискеты из двоичного файла, созданного под PDP-8 симулятора simh. Он может быть, например, сгенерирован каким-нибудь компилятором или являться копией программы для реального компьютера PDP-8.

Пример генерации для памяти RAM 128 B программы hello.bin:
```shell
python generator/generator --bin bin/hello.bin --crossaddr
```

Пока я делал этот компьютер, я нашёл несколько компиляторов реальных языков программирования (не ассемблера) для симулятора simh, вы можете попробовать запустить их самостоятельно:
* [**8bc**](https://github.com/clausecker/8bc). Компилятор языка программирования [B](https://en.wikipedia.org/wiki/B_(programming_language)) для simh. У него нехватает многих функций, например ввода-вывода (в 8bc их 2, а в языке B их на самом деле гораздо больше), нет некоторых фич языка, например операторов switch и case. Но тем не менее довольно прикольно писать код на языке программирования, а потом запускать в Стрелочках, учитывая что он ещё и предок Си. Так как это язык программирования старый и в настоящий момент нигде на практике не используется, по нему нет тонны видосов на Ютубе, поэтому придётся изучать по документации, например, по [этой](https://www.thinkage.ca/gcos/expl/b/manu/manu.html). Скомпилировав программу с помощью 8bc и получив .bin файл, вы можете засунуть его в мою питоновскую программку, сделать таким образом дискету и запустить в Стрелочках. Этот компилятор я пробовал и запускал с его помощью программу Hello world, написанную на B, в Стрелочках.
* [**4K FORTRAN**](https://techtinkering.com/2009/07/14/running-4k-fortran-on-a-dec-pdp8/). Компилятор языка программирования Fortran. Он запускается на simh и под него же происходит компиляция. Вы можете на симуляторе запустить компилятор, получить двоичный файл и также сделать дискету, как с 8bc. Сам я им не пользовался, поэтому точно не могу сказать, сработает ли это.
* [**Small-C**](https://so-much-stuff.com/pdp8/C/C.php). Вроде бы является компилятором Си для PDP-8, но его я не проверял и даже не пытался с ним разобраться, просто оставлю здесь ссылку, может, кто-то захочет его потыкать.
