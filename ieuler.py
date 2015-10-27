import json
import modules.ieuler.parser as parser
import modules.latex.parser
import mathlib as ml
import modules.tools.plot2d as plot2d


def conf(os):
    if os is "win":
        __settings__ = {
            "frink": "C:/Program Files (x86)/Frink/frink.jar",
            "maple": "C:/Program Files/Maple 2015/bin.X86_64_WINDOWS/cmaple",
            "pdflatex": "pdflatex"
        }
    elif os is "osx":
        __settings__ = {
            "frink": "/Applications/Frink/frink.jar",
            "maple":
            "/Library/Frameworks/Maple.framework/Versions/2015/bin/maple",
            "pdflatex": "/usr/local/texlive/2015/bin/x86_64-darwin/pdftex"
        }
    with open('settings.conf', 'w') as f:
        json.dump(__settings__, f)


def run(argv=None):
    gui_mode = False
    if argv and "-gui" in argv:
        gui_mode = True
        worksheet = {}

    parser.init()
    modules.latex.parser.init()

    if not gui_mode:
        print("Welcome to iEuler v0.1!")

    while True:

        do_save = False
        if gui_mode:
            inp = input("")
            try:
                index = int(inp)
            except ValueError:
                if inp == "save":
                    path = input("")
                    save_worksheet(worksheet, path)
                elif inp == "load":
                    path = input("")
                    worksheet = load_worksheet(path)
                else:
                    raise ValueError('Expected index or command')
                prompt = None
            else:
                evaluate = "evaluate" in input("")
                prompt = input("")
                add_to_worksheet(worksheet, index, prompt)

        else:
            prompt = input("iEuler> ")
            evaluate = True

        if prompt:
            send_result(inde, prompt, evaluate, gui_mode)


def send_result(index, command, evaluate, gui_mode):
    result = parser.parse(command, evaluate, gui_mode)

    if type(result) is ml.Plot:
        plot2d.plot(result)

    if gui_mode:
        print('{} {}'.format(index, modules.latex.parser.convert_expr(result)))
    else:
        print(result)
        print(parser.generate(result))


def add_to_worksheet(worksheet, index, command):
    worksheet[index] = {"command": command}


def save_worksheet(worksheet, path):
    f = open(path, 'w')
    for key in worksheet:
        f.write(worksheet[key]["command"] + "\n")
    f.close()


def load_worksheet(path, gui_mode=True):
    worksheet = {}
    f = open(path, 'r')
    for i, line in enumerate(f):
        worksheet[i] = {"command": line}
        send_result(i, line, False, gui_mode)
    f.close()
    return worksheet


def frink_query(query_string, proc, queue, thread):
    proc.stdin.write(query_string)
    return_string = procio.process_input(proc, queue, thread, 20)
    return_string = return_string.strip("\n")
    print(return_string)
    return return_string

# def generate_latex(output_string):
#     with open("modules/latex/preamble.tex", "r") as f:
#         output_string = f.read().replace("%content", output_string)
#     with open("mathnotes.tex", "w") as f:
#         f.write(output_string)
