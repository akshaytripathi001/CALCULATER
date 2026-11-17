"""A responsive scientific calculator with explanations and online voice recognition."""

import array
import ast
import cmath
import math
import operator
import queue
import re
import threading
import tkinter as tk


THEMES = {
    "night": {
        "background": "#0b1220",
        "panel": "#111c2f",
        "button": "#1b2940",
        "text": "#eef4ff",
        "muted": "#9eafc8",
        "accent": "#48d6b5",
        "button_active": "#293b57",
        "accent_active": "#62e5c4",
        "border": "#34445e",
        "insert": "#eef4ff",
    },
    "day": {
        "background": "#edf2f8",
        "panel": "#ffffff",
        "button": "#dce5f0",
        "text": "#17243a",
        "muted": "#52647c",
        "accent": "#087f69",
        "button_active": "#c7d5e6",
        "accent_active": "#07977b",
        "border": "#aab9cb",
        "insert": "#17243a",
    },
}

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def describe_node(node):
    """Explain a valid calculator expression in plain language."""
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return str(node.value)

    if isinstance(node, ast.Name):
        return {"pi": "pi (about 3.14159)", "e": "e (about 2.71828)"}.get(
            node.id, node.id
        )

    if isinstance(node, ast.UnaryOp):
        value = describe_node(node.operand)
        if isinstance(node.op, ast.USub):
            return f"make {value} negative"
        if isinstance(node.op, ast.UAdd):
            return f"keep {value} positive"

    if isinstance(node, ast.BinOp):
        left = describe_node(node.left)
        right = describe_node(node.right)
        actions = {
            ast.Add: f"add {left} and {right}",
            ast.Sub: f"subtract {right} from {left}",
            ast.Mult: f"multiply {left} by {right}",
            ast.Div: f"divide {left} by {right}",
            ast.Pow: f"raise {left} to the power of {right}",
            ast.Mod: f"find the remainder when {left} is divided by {right}",
        }
        for operation, description in actions.items():
            if isinstance(node.op, operation):
                return description

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if len(node.args) != 1 or node.keywords:
            raise ValueError("Functions take exactly one number.")
        value = describe_node(node.args[0])
        explanations = {
            "sqrt": f"find the square root of {value}",
            "sin": f"convert {value} degrees to radians, then find its sine",
            "cos": f"convert {value} degrees to radians, then find its cosine",
            "tan": f"convert {value} degrees to radians, then find its tangent",
            "log": f"find the natural logarithm of {value}",
            "ln": f"find the natural logarithm of {value}",
            "fact": f"multiply the whole numbers from 1 through {value}",
            "abs": f"find the distance of {value} from zero",
        }
        if node.func.id in explanations:
            return explanations[node.func.id]

    raise ValueError("Use numbers, arithmetic operators, and calculator functions.")


def evaluate_node(node):
    """Evaluate only the numeric syntax and functions supported by the calculator."""
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value

    if isinstance(node, ast.Name):
        constants = {"pi": math.pi, "e": math.e}
        if node.id in constants:
            return constants[node.id]
        raise ValueError(f"Unknown value: {node.id}")

    if isinstance(node, ast.UnaryOp):
        value = evaluate_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value

    if isinstance(node, ast.BinOp):
        operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }
        for operation, calculate in operations.items():
            if isinstance(node.op, operation):
                return calculate(evaluate_node(node.left), evaluate_node(node.right))

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if len(node.args) != 1 or node.keywords:
            raise ValueError("Functions take exactly one number.")
        value = evaluate_node(node.args[0])
        functions = {
            "sqrt": math.sqrt,
            "sin": lambda angle: math.sin(math.radians(angle)),
            "cos": lambda angle: math.cos(math.radians(angle)),
            "tan": lambda angle: math.tan(math.radians(angle)),
            "log": math.log,
            "ln": math.log,
            "abs": abs,
            "fact": math.factorial,
        }
        if node.func.id == "fact":
            if not isinstance(value, (int, float)) or value < 0 or not float(value).is_integer():
                raise ValueError("Factorial requires a non-negative whole number.")
            value = int(value)
        if node.func.id in functions:
            return functions[node.func.id](value)
        raise ValueError(f"Unknown function: {node.func.id}")

    raise ValueError("That expression is not supported.")


def parse_expression(expression):
    return ast.parse(expression, mode="eval").body


def _count_math_operations(node):
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return 0
    if isinstance(node, ast.Name) and node.id in {"pi", "e"}:
        return 0
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return 1 + _count_math_operations(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
    ):
        return 1 + _count_math_operations(node.left) + _count_math_operations(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id not in {"sqrt", "sin", "cos", "tan", "log", "ln", "fact"}:
            raise ValueError("Use a supported calculator function.")
        if len(node.args) != 1 or node.keywords:
            raise ValueError("A scientific function takes one number.")
        return 1 + _count_math_operations(node.args[0])
    raise ValueError("Use numbers and one calculator operation only.")


def _spoken_number(tokens, start):
    total = 0
    current = 0
    index = start
    fractional_digits = ""
    decimal = False
    consumed = False

    while index < len(tokens):
        word = tokens[index]
        if word == "and" and consumed:
            index += 1
            continue
        if word == "point" and consumed and not decimal:
            decimal = True
            index += 1
            continue
        if decimal and word in NUMBER_WORDS and NUMBER_WORDS[word] < 10:
            fractional_digits += str(NUMBER_WORDS[word])
            index += 1
            consumed = True
            continue
        if word in NUMBER_WORDS and not decimal:
            value = NUMBER_WORDS[word]
            if value >= 20:
                current += value
            else:
                current += value
            index += 1
            consumed = True
            continue
        if word == "hundred" and not decimal:
            current = max(current, 1) * 100
            index += 1
            consumed = True
            continue
        if word == "thousand" and not decimal:
            total += max(current, 1) * 1000
            current = 0
            index += 1
            consumed = True
            continue
        break

    if not consumed:
        return None, start
    number = str(total + current)
    if decimal and fractional_digits:
        number += "." + fractional_digits
    return number, index


def spoken_to_expression(phrase):
    """Convert one spoken math operation into a validated calculator expression."""
    text = phrase.lower().replace("what's", "what is")
    text = text.replace("×", " * ").replace("÷", " / ")
    text = re.sub(
        r"^\s*(?:(?:what is|calculate|compute|please|tell me|the answer to)\s+)+",
        "",
        text,
    )
    text = re.sub(r"[?!,]", " ", text)
    text = re.sub(r"\b(?:degrees?|equal to|equals)\b", " ", text)
    command_forms = (
        (r"\badd\s+(.+?)\s+and\s+(.+)$", r"\1 plus \2"),
        (r"\bsubtract\s+(.+?)\s+from\s+(.+)$", r"\2 minus \1"),
        (r"\bmultiply\s+(.+?)\s+by\s+(.+)$", r"\1 times \2"),
        (r"\bdivide\s+(.+?)\s+by\s+(.+)$", r"\1 divided by \2"),
    )
    for pattern, replacement in command_forms:
        text = re.sub(pattern, replacement, text)
    substitutions = (
        (r"\braised to the power of\b|\bto the power of\b|\bpower of\b", " ** "),
        (r"\bmultiplied by\b|\btimes\b|\bx\b", " * "),
        (r"\bdivided by\b|\bdivide by\b|\bover\b|\bslash\b", " / "),
        (r"\bplus\b", " + "),
        (r"\bminus\b", " - "),
        (r"\bsquare root of\b|\bsquare root\b", " sqrt "),
        (r"\bsine of\b|\bsine\b", " sin "),
        (r"\bcosine of\b|\bcosine\b", " cos "),
        (r"\btangent of\b|\btangent\b", " tan "),
        (r"\bnatural logarithm of\b|\blogarithm of\b|\blog of\b", " log "),
        (r"\bfactorial of\b", " fact "),
        (r"\bfactorial\b", " fact "),
    )
    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text)

    tokens = text.split()
    normalized = []
    index = 0
    while index < len(tokens):
        number, next_index = _spoken_number(tokens, index)
        if number is not None:
            normalized.append(number)
            index = next_index
        else:
            normalized.append(tokens[index])
            index += 1

    text = " ".join(normalized)
    text = re.sub(r"\b(sqrt|sin|cos|tan|log|fact)\s+(-?\d+(?:\.\d+)?|pi|e)\b", r"\1(\2)", text)
    text = re.sub(r"\b(-?\d+(?:\.\d+)?)\s+fact\b", r"fact(\1)", text)
    text = re.sub(r"\s+", " ", text).strip().rstrip(".;:")
    try:
        operation_count = _count_math_operations(parse_expression(text))
    except (SyntaxError, ValueError) as error:
        raise ValueError(
            "Say one calculation, for example 'seven plus three' or 'square root of sixteen'."
        ) from error
    if operation_count != 1:
        raise ValueError(
            "Speak exactly one math operation at a time, with no extra words or calculations."
        )
    return text


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AKSHAY | Scientific Calculator")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = max(340, min(940, screen_width - 48))
        height = max(480, min(820, screen_height - 80))
        root.geometry(f"{width}x{height}")
        root.minsize(340, 480)

        self.theme_name = "night"
        self.colors = THEMES[self.theme_name]
        root.configure(bg=self.colors["background"])
        self.expression = tk.StringVar()
        self.result = tk.StringVar(value="Ready")
        self.sound_enabled = True
        self.speech_enabled = True
        self.voice_events = queue.Queue()
        self.speech_queue = queue.Queue()
        self.voice_stop = None
        self._build_interface()
        self.expression.trace_add("write", self._update_explanation)
        self.root.bind("<Configure>", self._on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        threading.Thread(target=self._speech_worker, daemon=True).start()
        self.root.after(100, self._poll_voice_events)

    def _build_interface(self):
        self.outer = tk.Frame(self.root, bg=self.colors["background"])
        self.outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            self.outer,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        self.scrollbar = tk.Scrollbar(
            self.outer,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.container = tk.Frame(
            self.canvas,
            bg=self.colors["background"],
            padx=24,
            pady=18,
        )
        self.content_window = self.canvas.create_window(
            (0, 0), window=self.container, anchor="nw"
        )
        self.container.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.content_window, width=event.width),
        )
        self.canvas.bind_all("<MouseWheel>", self._scroll_page)

        self.header = tk.Frame(self.container, bg=self.colors["background"])
        self.header.pack(fill="x", pady=(0, 14))
        self.brand = tk.Frame(self.header, bg=self.colors["background"])
        self.brand.grid(row=0, column=0, sticky="w")
        self.header.grid_columnconfigure(0, weight=1)
        self.brand_title = tk.Label(
            self.brand,
            text="AKSHAY",
            font=("Segoe UI", 22, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["background"],
        )
        self.brand_title.pack(side="left")
        tk.Label(
            self.brand,
            text="SCIENTIFIC CALCULATOR",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(side="left", padx=12, pady=(8, 0))

        self.controls = tk.Frame(self.header, bg=self.colors["background"])
        self.controls.grid(row=0, column=1, sticky="e")
        self.theme_button = self._make_button(
            self.controls, "Day mode", self.toggle_theme, "utility"
        )
        self.theme_button.pack(side="left", padx=3)
        self.sound_button = self._make_button(
            self.controls, "Sound on", self.toggle_sound, "utility"
        )
        self.sound_button.pack(side="left", padx=3)
        self.speech_button = self._make_button(
            self.controls, "Voice on", self.toggle_speech, "utility"
        )
        self.speech_button.pack(side="left", padx=3)
        self.voice_button = self._make_button(
            self.controls, "Speak", self.toggle_voice_input, "utility"
        )
        self.voice_button.pack(side="left", padx=3)

        self.display_panel = tk.Frame(
            self.container, bg=self.colors["panel"], padx=18, pady=14
        )
        self.display_panel.pack(fill="x", pady=(0, 12))
        tk.Label(
            self.display_panel,
            text="EXPRESSION",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        self.display = tk.Entry(
            self.display_panel,
            textvariable=self.expression,
            font=("Consolas", 24),
            fg=self.colors["text"],
            insertbackground=self.colors["insert"],
            bg=self.colors["panel"],
            relief="flat",
            justify="right",
        )
        self.display.pack(fill="x", pady=(4, 2), ipady=7)
        self.display.bind("<Return>", lambda _event: self.calculate())
        tk.Label(
            self.display_panel,
            textvariable=self.result,
            font=("Segoe UI", 15, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["panel"],
            anchor="e",
        ).pack(fill="x")

        keypad = tk.Frame(self.container, bg=self.colors["background"])
        keypad.pack(fill="x", pady=(0, 12))
        keys = [
            [("AC", "clear"), ("DEL", "delete"), ("(", "input"), (")", "input"), ("pi", "input"), ("e", "input")],
            [("7", "input"), ("8", "input"), ("9", "input"), ("/", "input"), ("sqrt", "function"), ("sin", "function")],
            [("4", "input"), ("5", "input"), ("6", "input"), ("*", "input"), ("cos", "function"), ("tan", "function")],
            [("1", "input"), ("2", "input"), ("3", "input"), ("-", "input"), ("log", "function"), ("ln", "function")],
            [("0", "input"), (".", "input"), ("**", "input"), ("+", "input"), ("fact", "function"), ("=", "equals")],
        ]
        for column in range(6):
            keypad.grid_columnconfigure(column, weight=1, uniform="key")
        for row, row_keys in enumerate(keys):
            keypad.grid_rowconfigure(row, weight=1)
            for column, (label, action) in enumerate(row_keys):
                command = lambda value=label, kind=action: self._press(value, kind)
                self._make_button(
                    keypad,
                    label,
                    command,
                    "equals" if action == "equals" else "key",
                    font=("Segoe UI", 12, "bold"),
                ).grid(row=row, column=column, sticky="nsew", padx=4, pady=4)

        self.guide = tk.Frame(
            self.container, bg=self.colors["panel"], padx=16, pady=12
        )
        self.guide.pack(fill="x", pady=(0, 12))
        tk.Label(
            self.guide,
            text="HOW IT WORKS",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        self.explanation = tk.Label(
            self.guide,
            text="",
            font=("Segoe UI", 11),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            justify="left",
            anchor="w",
            wraplength=850,
        )
        self.explanation.pack(fill="x", pady=(5, 0))

        self.voice_status = tk.Label(
            self.container,
            text="Online voice recognition uses Google; microphone audio is sent to Google.",
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["background"],
            anchor="w",
        )
        self.voice_status.pack(fill="x", pady=(0, 8))

        self.equations = tk.Frame(self.container, bg=self.colors["background"])
        self.equations.pack(fill="x")
        self.equations.grid_columnconfigure(0, weight=1)
        self.equations.grid_columnconfigure(1, weight=1)
        self.equation_frames = []
        self.equation_frames.append(
            self._build_equation_solver(
                self.equations,
                "LINEAR EQUATION",
                "Solve ax + b = 0",
                ("a", "b"),
                self.solve_linear,
            )
        )
        self.equation_frames.append(
            self._build_equation_solver(
                self.equations,
                "QUADRATIC EQUATION",
                "Solve ax^2 + bx + c = 0",
                ("a", "b", "c"),
                self.solve_quadratic,
            )
        )
        self._arrange_equation_solvers(940)

    def _make_button(self, parent, text, command, style="key", font=None):
        color = self.colors["accent"] if style == "equals" else self.colors["button"]
        foreground = self.colors["background"] if style == "equals" else self.colors["text"]
        button = tk.Button(
            parent,
            text=text,
            command=lambda: self._button_action(command),
            font=font or ("Segoe UI", 9, "bold"),
            fg=foreground,
            bg=color,
            activebackground=(
                self.colors["accent_active"] if style == "equals" else self.colors["button_active"]
            ),
            activeforeground=foreground,
            relief=tk.RAISED,
            bd=3,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            cursor="hand2",
            padx=7,
            pady=5,
        )
        button.bind("<ButtonPress-1>", lambda _event: button.configure(relief=tk.SUNKEN))
        button.bind("<ButtonRelease-1>", lambda _event: button.configure(relief=tk.RAISED))
        return button

    def _build_equation_solver(self, parent, title, formula, names, callback):
        frame = tk.Frame(
            parent,
            bg=self.colors["panel"],
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=formula,
            font=("Segoe UI", 10),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w", pady=(2, 8))
        fields = tk.Frame(frame, bg=self.colors["panel"])
        fields.pack(fill="x")
        entries = {}
        for name in names:
            field = tk.Frame(fields, bg=self.colors["panel"])
            field.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(
                field, text=name, font=("Segoe UI", 9),
                fg=self.colors["muted"], bg=self.colors["panel"]
            ).pack(anchor="w")
            entry = tk.Entry(
                field,
                font=("Segoe UI", 11),
                fg=self.colors["text"],
                insertbackground=self.colors["insert"],
                bg=self.colors["background"],
                relief="flat",
                justify="center",
            )
            entry.pack(fill="x", ipady=5)
            entries[name] = entry
        self._make_button(
            frame, "Solve", lambda: callback(entries), "equals"
        ).pack(fill="x", pady=(10, 0), ipady=2)
        return frame

    def _button_action(self, command):
        if self.sound_enabled:
            self._play_click()
        command()

    def _play_click(self):
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_OK)
        except (ImportError, RuntimeError):
            self.root.bell()

    def _press(self, value, action):
        if action == "clear":
            self.expression.set("")
            self.result.set("Ready")
        elif action == "delete":
            self.expression.set(self.expression.get()[:-1])
        elif action == "equals":
            self.calculate()
        elif action == "function":
            self.expression.set(self.expression.get() + value + "(")
            self.display.focus_set()
        else:
            self.expression.set(self.expression.get() + value)
            self.display.focus_set()

    def toggle_theme(self):
        self.theme_name = "day" if self.theme_name == "night" else "night"
        previous = self.colors
        self.colors = THEMES[self.theme_name]
        reverse = {value: key for key, value in previous.items()}
        self._recolor_widget(self.root, reverse)
        self.theme_button.configure(
            text="Night mode" if self.theme_name == "day" else "Day mode"
        )

    def _recolor_widget(self, widget, reverse):
        for option in (
            "bg",
            "fg",
            "activebackground",
            "activeforeground",
            "insertbackground",
            "highlightbackground",
            "highlightcolor",
        ):
            try:
                old_color = widget.cget(option)
                if old_color in reverse:
                    widget.configure(**{option: self.colors[reverse[old_color]]})
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._recolor_widget(child, reverse)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.sound_button.configure(text=f"Sound {'on' if self.sound_enabled else 'off'}")

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        self.speech_button.configure(text=f"Voice {'on' if self.speech_enabled else 'off'}")

    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        width = max(340, event.width)
        self.container.configure(padx=14 if width < 600 else 24)
        self.explanation.configure(wraplength=max(260, width - 90))
        self._arrange_equation_solvers(width)
        if width < 660:
            self.controls.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        else:
            self.controls.grid(row=0, column=1, columnspan=1, sticky="e", pady=0)

    def _arrange_equation_solvers(self, width):
        stacked = width < 700
        for index, frame in enumerate(self.equation_frames):
            frame.grid(
                row=index if stacked else 0,
                column=0 if stacked else index,
                sticky="nsew",
                padx=(0, 0) if stacked else ((0, 7) if index == 0 else (7, 0)),
                pady=(0, 8) if stacked and index == 0 else 0,
            )

    def _scroll_page(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _update_explanation(self, *_args):
        expression = self.expression.get().strip()
        if not expression:
            message = (
                "Enter a calculation or use the equation solvers below. "
                "Sine, cosine, and tangent take angles in degrees."
            )
        else:
            try:
                operation = describe_node(parse_expression(expression))
                message = f"Next, {operation}. Press = to see the answer."
            except (SyntaxError, ValueError):
                message = self._describe_incomplete_expression(expression)
        self.explanation.configure(text=message)

    @staticmethod
    def _describe_incomplete_expression(expression):
        for symbol, description in (
            ("+", "add the next number"),
            ("-", "subtract the next number"),
            ("*", "multiply by the next number"),
            ("/", "divide by the next number"),
            ("**", "raise the current number to the next power"),
        ):
            if expression.endswith(symbol):
                return f"Next, {description}. Enter the number, then press =."
        for function, description in (
            ("sqrt(", "enter a number to find its square root"),
            ("sin(", "enter an angle in degrees to find its sine"),
            ("cos(", "enter an angle in degrees to find its cosine"),
            ("tan(", "enter an angle in degrees to find its tangent"),
            ("log(", "enter a positive number to find its natural logarithm"),
            ("ln(", "enter a positive number to find its natural logarithm"),
            ("fact(", "enter a non-negative whole number for its factorial"),
        ):
            if expression.endswith(function):
                return f"Next, {description}, then close the bracket and press =."
        return "Finish the expression with numbers and brackets, then press =."

    def calculate(self):
        try:
            expression = self.expression.get().strip()
            if not expression:
                raise ValueError("Enter an expression first.")
            tree = parse_expression(expression)
            explanation = describe_node(tree)
            answer = evaluate_node(tree)
            self.result.set(f"= {answer}")
            self.explanation.configure(
                text=f"To calculate {expression}, {explanation}. The answer is {answer}."
            )
            self._speak(answer)
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, TypeError) as error:
            self.result.set("Error")
            self.explanation.configure(text=f"Calculation stopped: {error}")

    def solve_linear(self, fields):
        try:
            a, b = (float(fields[name].get()) for name in ("a", "b"))
            if a == 0:
                if b == 0:
                    answer = "Every value of x is a solution."
                    explanation = "Both coefficients are zero, so 0x + 0 equals zero for every x."
                else:
                    answer = "No solution"
                    explanation = f"The x term is zero, but the equation still says {b:g} = 0, which is impossible."
            else:
                root = -b / a
                answer = f"x = {root:g}"
                explanation = (
                    f"To solve {a:g}x + {b:g} = 0, subtract {b:g} from both sides, "
                    f"then divide by {a:g}. This gives x = {root:g}."
                )
            self.result.set(answer)
            self.explanation.configure(text=explanation)
            self._speak(answer)
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            self.result.set("Error")
            self.explanation.configure(text=f"Enter a number in each coefficient box. {error}")

    def solve_quadratic(self, fields):
        try:
            a, b, c = (float(fields[name].get()) for name in ("a", "b", "c"))
            if a == 0:
                if b == 0:
                    answer = "Every x is a solution." if c == 0 else "No solution"
                    explanation = (
                        "All coefficients are zero, so every x works."
                        if c == 0
                        else f"With a = 0 and b = 0, the equation becomes {c:g} = 0, so there is no solution."
                    )
                else:
                    root = -c / b
                    answer = f"x = {root:g}"
                    explanation = (
                        "Since a is zero, this is linear. Move the constant to the other side "
                        f"and divide by b: x = {-c:g} / {b:g} = {root:g}."
                    )
            else:
                discriminant = b**2 - 4 * a * c
                square_root = math.sqrt(discriminant) if discriminant >= 0 else cmath.sqrt(discriminant)
                first = (-b + square_root) / (2 * a)
                second = (-b - square_root) / (2 * a)
                answer = f"x1 = {first},   x2 = {second}"
                explanation = (
                    f"First find the discriminant b^2 - 4ac = {discriminant:g}. "
                    "Then use the quadratic formula: take -b plus and minus the square "
                    "root of the discriminant, and divide each result by 2a."
                )
            self.result.set(answer)
            self.explanation.configure(text=explanation)
            self._speak(answer)
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            self.result.set("Error")
            self.explanation.configure(text=f"Enter a number in each coefficient box. {error}")

    def toggle_voice_input(self):
        if self.voice_stop is not None:
            self.voice_stop.set()
            self.voice_status.configure(text="Stopping the microphone...")
            return
        self.voice_stop = threading.Event()
        self.voice_button.configure(text="Stop")
        self.voice_status.configure(
            text="Starting microphone. Audio will be sent to Google for recognition..."
        )
        threading.Thread(
            target=self._listen_for_command,
            args=(self.voice_stop,),
            daemon=True,
        ).start()

    def _listen_for_command(self, stop_event):
        try:
            import speech_recognition as sr
            import sounddevice as sd
        except ImportError as error:
            self.voice_events.put(("error", f"Install voice packages with pip install -r requirements.txt. {error}"))
            self.voice_events.put(("stopped", ""))
            return

        try:
            audio = queue.Queue()

            def receive_audio(indata, _frames, _time, _status):
                try:
                    audio.put_nowait(bytes(indata))
                except queue.Full:
                    pass

            chunks = []
            speech_started = False
            quiet_time = 0.0
            elapsed = 0.0
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=1600,
                dtype="int16",
                channels=1,
                callback=receive_audio,
            ):
                self.voice_events.put(
                    ("status", "Listening. Say one calculation in English; audio is sent to Google.")
                )
                while not stop_event.is_set() and elapsed < 8:
                    try:
                        chunk = audio.get(timeout=0.15)
                    except queue.Empty:
                        continue
                    samples = array.array("h")
                    samples.frombytes(chunk)
                    duration = len(samples) / 16000
                    elapsed += duration
                    level = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
                    if level > 450:
                        speech_started = True
                        quiet_time = 0
                        chunks.append(chunk)
                    elif speech_started:
                        chunks.append(chunk)
                        quiet_time += duration
                        if quiet_time >= 0.6:
                            break
            if not chunks:
                self.voice_events.put(("error", "No speech detected. Click Speak and try again."))
                return

            recognizer = sr.Recognizer()
            recording = sr.AudioData(b"".join(chunks), 16000, 2)
            self.voice_events.put(("status", "Recognizing speech online with Google..."))
            heard = recognizer.recognize_google(recording, language="en-US")
            self.voice_events.put(("heard", heard))
        except sr.UnknownValueError:
            self.voice_events.put(("error", "Google could not understand that. Please try again."))
        except sr.RequestError as error:
            self.voice_events.put(
                ("error", f"Google speech recognition failed. Check your internet connection. {error}")
            )
        except Exception as error:
            self.voice_events.put(("error", f"Voice recognition unavailable: {error}"))
        finally:
            self.voice_events.put(("stopped", ""))

    def _poll_voice_events(self):
        while True:
            try:
                event, value = self.voice_events.get_nowait()
            except queue.Empty:
                break
            if event == "status":
                self.voice_status.configure(text=value)
            elif event == "heard":
                if value:
                    try:
                        expression = spoken_to_expression(value)
                        self.voice_status.configure(text=f"I heard: “{value}”")
                        self.expression.set(expression)
                        self.calculate()
                    except (SyntaxError, ValueError) as error:
                        self.result.set("Could not understand")
                        self.explanation.configure(text=f"I heard “{value}”, but {error}")
                else:
                    self.voice_status.configure(text="No speech was recognized. Try again.")
            elif event == "error":
                self.voice_status.configure(text=f"Voice error: {value}")
            elif event == "stopped":
                self.voice_stop = None
                self.voice_button.configure(text="Speak")
        self.root.after(100, self._poll_voice_events)

    def _speak(self, text):
        if not self.speech_enabled:
            return
        self.speech_queue.put(str(text))

    def _speech_worker(self):
        engine = None
        while True:
            text = self.speech_queue.get()
            if text is None:
                return
            try:
                if engine is None:
                    import pyttsx3

                    engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except Exception as error:
                self.voice_events.put(("error", f"Speech output unavailable: {error}"))
                engine = None

    def _close(self):
        if self.voice_stop is not None:
            self.voice_stop.set()
        self.speech_queue.put(None)
        self.root.destroy()


def main():
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
