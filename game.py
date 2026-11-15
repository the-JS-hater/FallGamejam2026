#!/usr/bin/env python3
 
 
import webbrowser
import subprocess
import pathlib
import os
import time
import pygame
import random
import re
 
 
TYP_FILENAME = "render_image.typ"
OUT_FILENAME = "main.pdf"
 
TYP_TEMPLATE = "#set page(height: 480pt, width: 600pt)\n"
 
ALL_SKILLS = ["interesting_fact_skill", "test1", "test2", "test3", "#lorem(50)"]
 
TEXT_WIDTH = 300
 
 
class DialogueOption:
    text = ""
    action = ""
    effect = 0.0
    font = None
    response = None
    requrement = ""
 
    def __init__(self, text, effect, response, requirement=None, font=None, action=""):
        self.text = text
        self.action = action
        self.effect = effect
        self.response = response
        if requirement: self.requrement = requirement
        if font: self.font = font
 
 
class DialogueNode:
    text = ""
    options = []
    label = None
    next = None
 
    def __init__(self, text, options, label=None):
        self.text = text
        self.options = options
        self.label = label
 
 
OPTION_RE = re.compile(r"^\[(.*?)\]\s*([+-]?\d+(?:\.\d+)?)?\s*(?:\((\w+)\))?\s*$")
 
 
def init_date2(path="revised-draft.txt", name=""):
    """Parse a dialogue script. Returns the top-level nodes in file order;
    start the date at nodes[0].
 
    Every option's .response ends up as a DialogueNode (or None at the end
    of the script). When showing a response: print its text, then show its
    options, or if it has none, move on to response.next."""
    global ALL_SKILLS
 
    # (line number, indent depth, text), skipping blanks and comments
    entries = []
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.rstrip("\r\n")
            text = raw.strip().replace("{name}", name)
            if not text or text.startswith("#"):
                continue
            depth = len(raw) - len(raw.lstrip("\t"))
            entries.append((lineno, depth, text))
 
    def error(i, msg):
        lineno, _, text = entries[i]
        raise ValueError(f"{path}:{lineno}: {msg}: {text!r}")
 
    nodes = []            # top-level nodes in order
    by_label = {}
    jumps = []            # (option, label, entry index) for "-> @label"
    leaves = {}           # node index -> response nodes with no options
    dangling = {}         # node index -> options with no "->" at all
 
    def parse_options(i, depth, owner):
        options = []
        while i < len(entries) and entries[i][1] == depth:
            m = OPTION_RE.match(entries[i][2])
            if not m:
                error(i, "expected an option like [text] +1 (skill)")
            label, effect, skill = m.groups()
            if skill and skill not in ALL_SKILLS:
                print(f"warning: line {entries[i][0]}: unknown skill {skill!r}")
            option = DialogueOption(label.strip(), float(effect) if effect else 0.0,
                                    None, requirement=skill)
            option_i = i
            i += 1
 
            actions = []
            has_response = False
            while i < len(entries) and entries[i][1] == depth + 1:
                text = entries[i][2]
                if text.startswith("->"):
                    if has_response:
                        error(i, "option already has a response")
                    has_response = True
                    target = text[2:].strip()
                    if target.startswith("@"):
                        jumps.append((option, target[1:].strip(), i))
                        i += 1
                    else:
                        i += 1
                        sub_options, i = parse_options(i, depth + 2, owner)
                        option.response = DialogueNode(target, sub_options)
                        if not sub_options:
                            leaves[owner].append(option.response)
                elif text.startswith("["):
                    error(i, "options must go under a '->' response")
                else:
                    if has_response:
                        error(i, "text after the response")
                    actions.append(text)
                    i += 1
            option.action = " ".join(actions)
            if not has_response:
                dangling[owner].append(option)
            options.append(option)
 
            if i < len(entries) and entries[i][1] > depth:
                error(i, f"unexpected indentation (option on line {entries[option_i][0]})")
        return options, i
 
    i = 0
    while i < len(entries):
        _, depth, text = entries[i]
        if depth != 0:
            error(i, "unexpected indentation")
        if text.startswith("skills:"):
            ALL_SKILLS = [s.strip() for s in text.split(":", 1)[1].split(",") if s.strip()]
            i += 1
        elif text.startswith("@"):
            label = text[1:].strip()
            if label in by_label:
                error(i, "duplicate label")
            i += 1
            node_text = ""
            if (i < len(entries) and entries[i][1] == 0
                    and not entries[i][2].startswith(("@", "skills:"))):
                node_text = entries[i][2]
                i += 1
            owner = len(nodes)
            leaves[owner], dangling[owner] = [], []
            options, i = parse_options(i, 1, owner)
            node = DialogueNode(node_text, options, label)
            nodes.append(node)
            by_label[label] = node
        else:
            error(i, "expected @label or skills:")
 
    # "continues to the next @label"
    for idx, node in enumerate(nodes):
        nxt = nodes[idx + 1] if idx + 1 < len(nodes) else None
        node.next = nxt
        for leaf in leaves[idx]:
            leaf.next = nxt
        for option in dangling[idx]:
            option.response = nxt
 
    for option, label, i in jumps:
        if label not in by_label:
            error(i, "unknown label")
        option.response = by_label[label]
 
    return nodes
 
 
def setup():
    pygame.init()
    screen = pygame.display.set_mode(size=(1, 1))
    clock = pygame.time.Clock()
 
    typ_file = os.open(TYP_FILENAME, os.O_CREAT | os.O_WRONLY | os.O_NONBLOCK)
 
    pdf_reader = subprocess.Popen(["zathura", OUT_FILENAME])
 
    return typ_file, clock, pdf_reader
 
 
def init_date():
    responseA = DialogueNode("Wow, that's rude", [])
    responseB = DialogueNode("Wow, that's so funny", [])
    responseC = DialogueNode("Wow that's interesting", [])
    root = DialogueNode("Hello, i am date\n#lorem(50)", [DialogueOption("fuck off", -5.0, responseA), DialogueOption("hello date, i am dad", 5.0, responseB), DialogueOption("Did you know _interesting fact_", 5.0, responseC, "interesting_fact_skill")])
    return root
 
 
def render_object(pos, typ_object, width = None):
    x, y = pos
    width_str = f"#box(width: {width}pt)[{typ_object}]" if width else typ_object
    return f"#place(dx: {int(x)}pt, dy: {int(y)}pt)[{width_str}]\n"
 
 
def render_sprite(pos, image_path, size = None):
    size_s = ""
    if size:
        size_s = f", width: {size[0]}pt"
        if size[1]:
            size_s += f", height: {size[1]}pt"
    return render_object(pos, f"#image(\"{image_path}\", scaling: \"pixelated\"{size_s})")
 
 
def commit_render(render_str, typst_fd):
    render_str += "\n#let ok = true"
    os.truncate(typst_fd, 0)
    os.pwrite(typst_fd, render_str.encode(), 0)
 
 
def teardown(typ_fd, pdf_reader):
    os.close(typ_fd)
    pdf_reader.terminate()
    pygame.quit()
    os._exit(0)
 
 
def splash_screen(typ_fd):
    with open("splash_screen.typ") as file:
        render_str = file.read()
    commit_render(render_str, typ_fd)
    get_input()
 
 
def get_input(num_options = None):
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if not any(keys): break
 
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: break
        if keys[pygame.K_SPACE]: return -1
        if not num_options:
            if any(keys) and not keys[pygame.K_LSUPER]: break
        else:
            for key in range(num_options):
                if keys[pygame.key.key_code(str(key+1))]:
                    return key
    return -2
 
 
def input_text(render_str, typ_fd, clock):
    pygame.key.start_text_input()
    input_string = ""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.TEXTINPUT:
                input_string += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    input_string = input_string[:-1]
                elif event.key == pygame.K_RETURN:
                    pygame.key.stop_text_input()
                    return input_string
        commit_render(render_str + render_object((100, 15), input_string, TEXT_WIDTH), typ_fd)
        clock.tick(30)
 
 
def get_skill(typ_fd, owned_skills, clock):
    skills = ALL_SKILLS.copy()
    rng = random.Random()
    while len(skills) > 3:
        index = rng.randint(0, len(skills))
        skills = skills[:index] + skills[index+1:]
 
    render_str = TYP_TEMPLATE
 
    out_str = "Choose a skill:\n"
    for option in skills:
        out_str += f"+ {option}\n"
    render_str += render_object((100, 0), out_str, TEXT_WIDTH)
 
    skills_str = "Skills:\n"
    for skill in owned_skills:
        skills_str += f"- {skill}\n"
    render_str += render_object((400, 0), skills_str, 100)
 
    commit_render(render_str, typ_fd)
    choice = get_input(3)
    while choice < 0:
        commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
        clock.tick(30)
 
        choice = get_input(3)
    return skills[choice]
 
 
def timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock):
    timewarp_counter[0] += 1
    skills.add(get_skill(typ_fd, skills, clock))
    skills_str = "Skills:\n"
    for skill in skills:
        skills_str += f"- {skill}\n"
    typ_template = template + render_object((400, 0), skills_str, 100)
    date_excitement = 5.0
    tree = root
    out_str = tree.text + "\n"
    return out_str, tree, date_excitement, typ_template
 
def main():
    typ_fd, clock, pdf_reader = setup()
 
    splash_screen(typ_fd)
 
    template = TYP_TEMPLATE
    render_str = template
 
    render_str += render_object((100, 0), "Enter your name:")
    commit_render(render_str, typ_fd)
    name = input_text(render_str, typ_fd, clock)
 
    date_excitement = 5.0
    root = init_date2(name=name)[0]
    tree = root
    skills = set()
    timewarp_counter = [0]
    template += render_sprite((0, 0), "Assets/WomanPortrait.png", (50, None))
    typ_template = template + render_object((400, 0), "Skills:\n")
    render_str = typ_template
    output_str = tree.text + "\n"
 
    while True:
        unavailable = []
        if not tree: break
        for i, option in enumerate(tree.options):
            if (option.requrement and option.requrement not in skills):
                output_str += "+ Hidden option\n"
                unavailable += [i]
            else:
                output_str += f"+ {option.text}\n"
 
        render_str += render_object((100, 0), output_str, TEXT_WIDTH)
        commit_render(render_str, typ_fd)
        clock.tick(30)
 
        choice = get_input(len(tree.options))
        while choice in unavailable:
            commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
            clock.tick(30)
 
            choice = get_input(len(tree.options))
 
        render_str = typ_template
        if choice == -1:
            output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
            render_str = typ_template
            continue
 
        if choice == -2:
            break
 
        option = tree.options[choice]
        date_excitement += option.effect
        tree = option.response
        if not tree: break
 
        output_str = ""
        if option.action:
            output_str += f"_{option.action}_\n\n"
        output_str += tree.text + "\n"
 
        # a response with no options of its own continues to the next @label
        while not tree.options and tree.next:
            tree = tree.next
            output_str += "\n" + tree.text + "\n"
 
        if date_excitement <= 0.0:
            render_str += render_object((100, 0), output_str, TEXT_WIDTH)
            render_str += render_object((100, 200), "Date got bored and you lose.\n\nTo timetravel, press space. Otherwise, press any button")
            commit_render(render_str, typ_fd)
            do_timetravel = get_input() == -1
            if do_timetravel:
                output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
                render_str = typ_template
                continue
            break
 
        if not tree.options:
            if date_excitement >= 10.0:
                output_str = output_str[:-2] + " Want to meet up again?\""
                render_str += render_object((100, 0), output_str, TEXT_WIDTH)
                render_str += render_object((100, 200), "you win date, awooga!\n\n")
                commit_render(render_str, typ_fd)
                get_input()
                break
            render_str += render_object((100, 0), output_str, TEXT_WIDTH)
            render_str += render_object((100, 200), "dialogue tree ends here\n\nTo timetravel, press space. Otherwise, press any button")
            commit_render(render_str, typ_fd)
            do_timetravel = get_input() == -1
            if do_timetravel:
                output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
                render_str = typ_template
                continue
            break
 
        # RENDER
        commit_render(render_str, typ_fd)
        render_str = typ_template
 
        clock.tick(30)
 
 
    teardown(typ_fd, pdf_reader)
 
 
if __name__ == "__main__":
    main()
 
