"""Pair rounds where two people each add a function to a small app."""

from __future__ import annotations

from .round_types import Beat, Challenge, Fact, Part, Samples


def _round(
    *,
    id: str,
    title: str,
    brief: str,
    hint: str,
    ask: str,
    index: str,
    files: tuple[tuple[str, str], ...],
    solutions: tuple[tuple[str, str], ...],
    check: str,
    file_a: str,
    fn_a: str,
    job_a: str,
    gate_a: str,
    file_b: str,
    fn_b: str,
    job_b: str,
    gate_b: str,
    rule: str,
    adequate: str,
    bare: str,
    partial: str,
    vague: str,
    reply: str,
) -> Challenge:
    return Challenge(
        id=id,
        title=title,
        brief=brief,
        hint=hint,
        files=files,
        solutions=solutions,
        check=check,
        gates=((file_a, (gate_a,)), (file_b, (gate_b,))),
        beats=(
            Beat(
                ask=ask,
                fixture_title="Project files",
                fixture=index.strip(),
                facts=(
                    Fact(
                        "file",
                        f"Which file: {file_a} or {file_b}",
                        ((rf"{file_a.replace('.', r'\.')}", rf"{file_b.replace('.', r'\.')}"),),
                    ),
                    Fact(
                        "function",
                        f"Which function: {fn_a} or {fn_b}",
                        ((rf"\b{fn_a}\b", rf"\b{fn_b}\b"),),
                    ),
                    Fact(
                        "rule",
                        rule,
                        ((gate_a, gate_b),),
                    ),
                ),
                simulated_reply=reply,
                samples=Samples(adequate=adequate, bare=bare, partial=partial, vague=vague),
                parts=(
                    Part("Your job", file_a, job_a, fn_a),
                    Part("Your job", file_b, job_b, fn_b),
                ),
            ),
        ),
    )


_CHAT_FILES = (
    (
        "rooms.py",
        "def list_rooms():\n    return ['general']\n",
    ),
    (
        "users.py",
        "def list_users():\n    return ['Ada', 'Sam']\n",
    ),
    (
        "messages.py",
        "MESSAGES = []\n\n\ndef send_message(room, user, text):\n    raise NotImplementedError\n",
    ),
    (
        "presence.py",
        "ROOMS = {'general': ['Sam', 'Ada']}\n\n\ndef who_is_here(room):\n    raise NotImplementedError\n",
    ),
    (
        "app.py",
        "from messages import send_message\n"
        "from presence import who_is_here\n\n\n"
        "def show(room, user, text):\n"
        "    people = who_is_here(room)\n"
        "    message = send_message(room, user, text)\n"
        "    return {'here': people, 'message': message}\n",
    ),
)

_CHAT_SOLUTIONS = (
    (
        "messages.py",
        "MESSAGES = []\n\n\n"
        "def send_message(room, user, text):\n"
        "    if not str(text).strip():\n"
        "        return None\n"
        "    message = {'room': room, 'user': user, 'text': text}\n"
        "    MESSAGES.append(message)\n"
        "    return message\n",
    ),
    (
        "presence.py",
        "ROOMS = {'general': ['Sam', 'Ada']}\n\n\n"
        "def who_is_here(room):\n"
        "    return sorted(ROOMS.get(room, []))\n",
    ),
)

_SNACK_FILES = (
    (
        "menu.py",
        "PRICES = {'coffee': 3, 'muffin': 4}\n\n\ndef price_of(name):\n    return PRICES[name]\n",
    ),
    (
        "cart.py",
        "def add_item(cart, name):\n    raise NotImplementedError\n",
    ),
    (
        "receipt.py",
        "def total(cart, menu):\n    raise NotImplementedError\n",
    ),
    (
        "counter.py",
        "from cart import add_item\n"
        "from menu import PRICES\n"
        "from receipt import total\n\n\n"
        "def sale(cart, name):\n"
        "    add_item(cart, name)\n"
        "    return total(cart, PRICES)\n",
    ),
)

_SNACK_SOLUTIONS = (
    (
        "cart.py",
        "def add_item(cart, name):\n"
        "    if not str(name).strip():\n"
        "        return cart\n"
        "    cart.append(name)\n"
        "    return cart\n",
    ),
    (
        "receipt.py",
        "def total(cart, menu):\n    return sum(menu[name] for name in cart if name in menu)\n",
    ),
)

_CHECKIN_FILES = (
    (
        "guests.py",
        "GUESTS = {'Sam': False}\n\n\ndef guest_names():\n    return list(GUESTS)\n",
    ),
    (
        "checkin.py",
        "from guests import GUESTS\n\n\ndef check_in(name):\n    raise NotImplementedError\n",
    ),
    (
        "badge.py",
        "def make_badge(name):\n    raise NotImplementedError\n",
    ),
    (
        "desk.py",
        "from badge import make_badge\n"
        "from checkin import check_in\n\n\n"
        "def welcome(name):\n"
        "    check_in(name)\n"
        "    return make_badge(name)\n",
    ),
)

_CHECKIN_SOLUTIONS = (
    (
        "checkin.py",
        "from guests import GUESTS\n\n\n"
        "def check_in(name):\n"
        "    if name not in GUESTS:\n"
        "        return None\n"
        "    GUESTS[name] = True\n"
        "    return name\n",
    ),
    (
        "badge.py",
        "def make_badge(name):\n"
        "    if not str(name).strip():\n"
        "        return None\n"
        "    return f'HELLO my name is {name}'\n",
    ),
)

_SONG_FILES = (
    (
        "library.py",
        "TITLES = ['Tide', 'Reef']\n",
    ),
    (
        "playlist.py",
        "QUEUE = []\n\n\ndef enqueue(title):\n    raise NotImplementedError\n",
    ),
    (
        "player.py",
        "from playlist import QUEUE\n\n\ndef skip():\n    raise NotImplementedError\n",
    ),
    (
        "booth.py",
        "from player import skip\n"
        "from playlist import enqueue\n\n\n"
        "def play(first, second):\n"
        "    enqueue(first)\n"
        "    enqueue(second)\n"
        "    return skip()\n",
    ),
)

_SONG_SOLUTIONS = (
    (
        "playlist.py",
        "QUEUE = []\n\n\n"
        "def enqueue(title):\n"
        "    if not str(title).strip():\n"
        "        return list(QUEUE)\n"
        "    QUEUE.append(title)\n"
        "    return list(QUEUE)\n",
    ),
    (
        "player.py",
        "from playlist import QUEUE\n\n\n"
        "def skip():\n"
        "    if not QUEUE:\n"
        "        return None\n"
        "    QUEUE.pop(0)\n"
        "    return QUEUE[0] if QUEUE else None\n",
    ),
)

_BOARD_FILES = (
    (
        "names.py",
        "TEAM = ['Ada', 'Sam']\n",
    ),
    (
        "tasks.py",
        "TASKS = []\n\n\ndef add_task(title):\n    raise NotImplementedError\n",
    ),
    (
        "done.py",
        "from tasks import TASKS\n\n\ndef mark_done(title):\n    raise NotImplementedError\n",
    ),
    (
        "board.py",
        "from done import mark_done\n"
        "from tasks import TASKS, add_task\n\n\n"
        "def finish(title):\n"
        "    add_task(title)\n"
        "    mark_done(title)\n"
        "    return TASKS\n",
    ),
)

_BOARD_SOLUTIONS = (
    (
        "tasks.py",
        "TASKS = []\n\n\n"
        "def add_task(title):\n"
        "    if not str(title).strip():\n"
        "        return None\n"
        "    task = {'title': title, 'done': False}\n"
        "    TASKS.append(task)\n"
        "    return task\n",
    ),
    (
        "done.py",
        "from tasks import TASKS\n\n\n"
        "def mark_done(title):\n"
        "    for task in TASKS:\n"
        "        if task['title'] == title:\n"
        "            task['done'] = True\n"
        "            task['stamp'] = 'booth'\n"
        "            return task\n"
        "    return None\n",
    ),
)

_ASK = (
    "You each add one function. Name the file, the function, and the rule. "
    "Pasting the error is not enough. Grok edits only the file you name. "
    "Your partner is editing a different one, on their own phone."
)

BUILD_CHALLENGES: tuple[Challenge, ...] = (
    _round(
        id="team-chat",
        title="Team chat",
        brief="A room that shows who is here and can send a message. You add one of those two functions.",
        hint="Name the file and the function. 'Build the chat' makes Grok guess.",
        ask=_ASK,
        index="messages.py send_message\npresence.py who_is_here\nrooms.py, users.py, and app.py are already written.",
        files=_CHAT_FILES,
        solutions=_CHAT_SOLUTIONS,
        check=(
            "import app\n"
            "from messages import send_message\n"
            "assert send_message('general', 'Ada', '   ') is None\n"
            "result = app.show('general', 'Ada', 'hello')\n"
            "assert result['message']['text'] == 'hello'\n"
            "assert result['here'] == ['Ada', 'Sam']\n"
        ),
        file_a="messages.py",
        fn_a="send_message",
        job_a=(
            "You own messages.py. Write send_message(room, user, text) so a real message is saved "
            "with its room, user, and text, then returned. If the text is blank or only spaces, "
            "save nothing and return None."
        ),
        gate_a="blank",
        file_b="presence.py",
        fn_b="who_is_here",
        job_b=(
            "You own presence.py. Write who_is_here(room) so it returns the people in that room "
            "as a new list, sorted from A to Z. An unknown room returns an empty list."
        ),
        gate_b="sorted",
        rule="The rule: blank messages are dropped, or the room list is sorted",
        adequate="In messages.py, add send_message(room, user, text). Save a real message and return it. A blank message is not saved.",
        bare="messages.py send_message(room, user, text) with a blank message stays unsaved.",
        partial="Please add send_message in messages.py.",
        vague="Build the chat feature.",
        reply="Updated messages.py.",
    ),
    _round(
        id="snack-counter",
        title="Snack counter",
        brief="A booth counter that adds a snack and prints the total. You add one of those two functions.",
        hint="Name the file and the function. 'Build the counter' makes Grok guess.",
        ask=_ASK,
        index="cart.py add_item\nreceipt.py total\nmenu.py and counter.py are already written.",
        files=_SNACK_FILES,
        solutions=_SNACK_SOLUTIONS,
        check=(
            "import counter\n"
            "from cart import add_item\n"
            "from menu import PRICES\n"
            "from receipt import total\n"
            "cart = []\n"
            "assert counter.sale(cart, 'coffee') == 3\n"
            "assert counter.sale(cart, 'muffin') == 7\n"
            "assert add_item(['coffee'], '  ') == ['coffee']\n"
            "assert total(['coffee', 'water'], PRICES) == 3\n"
        ),
        file_a="cart.py",
        fn_a="add_item",
        job_a=(
            "You own cart.py. Write add_item(cart, name) so a real snack name is appended and the cart "
            "is returned. A blank name, or a name that is only spaces, is not added."
        ),
        gate_a="blank",
        file_b="receipt.py",
        fn_b="total",
        job_b=(
            "You own receipt.py. Write total(cart, menu) so it adds the prices of names that are in the "
            "menu and returns that amount. A missing name is skipped instead of crashing."
        ),
        gate_b="missing",
        rule="The rule: blank names are left out, or a missing menu name is skipped",
        adequate="In cart.py, add add_item(cart, name). Append a real snack and return the cart. A blank name is not added.",
        bare="cart.py add_item(cart, name) with a blank name stays out of the cart.",
        partial="Please add add_item in cart.py.",
        vague="Build the snack counter.",
        reply="Updated receipt.py.",
    ),
    _round(
        id="hackathon-checkin",
        title="Hackathon check-in",
        brief="The desk checks a person in and prints their badge. You add one of those two functions.",
        hint="Name the file and the function. 'Build check-in' makes Grok guess.",
        ask=_ASK,
        index="checkin.py check_in\nbadge.py make_badge\nguests.py and desk.py are already written.",
        files=_CHECKIN_FILES,
        solutions=_CHECKIN_SOLUTIONS,
        check=(
            "import desk\n"
            "from badge import make_badge\n"
            "from checkin import check_in\n"
            "from guests import GUESTS\n"
            "assert desk.welcome('Sam') == 'HELLO my name is Sam'\n"
            "assert GUESTS['Sam'] is True\n"
            "assert check_in('Nobody') is None\n"
            "assert 'Nobody' not in GUESTS\n"
            "assert make_badge('   ') is None\n"
        ),
        file_a="checkin.py",
        fn_a="check_in",
        job_a=(
            "You own checkin.py. Write check_in(name) so a guest who is already on the list is marked "
            "arrived and the name is returned. A name that is not on the list returns None and is not added."
        ),
        gate_a="list",
        file_b="badge.py",
        fn_b="make_badge",
        job_b=(
            "You own badge.py. Write make_badge(name) so it returns HELLO my name is, then the name. "
            "A blank name, or a name that is only spaces, returns None."
        ),
        gate_b="blank",
        rule="The rule: only people on the list are checked in, or a blank badge returns None",
        adequate="In checkin.py, add check_in(name). Mark a guest arrived only when that name is on the list. Otherwise return None.",
        bare="checkin.py check_in(name) for a guest on the list, and nowhere else.",
        partial="Please add check_in in checkin.py.",
        vague="Build the check-in desk.",
        reply="Updated badge.py.",
    ),
    _round(
        id="song-booth",
        title="Song booth",
        brief="A playlist where one person queues songs and the other skips. You add one of those two functions.",
        hint="Name the file and the function. 'Build the playlist' makes Grok guess.",
        ask=_ASK,
        index="playlist.py enqueue\nplayer.py skip\nlibrary.py and booth.py are already written.",
        files=_SONG_FILES,
        solutions=_SONG_SOLUTIONS,
        check=(
            "import booth\n"
            "from player import skip\n"
            "from playlist import QUEUE, enqueue\n"
            "assert booth.play('Tide', 'Reef') == 'Reef'\n"
            "before = list(QUEUE)\n"
            "assert enqueue('   ') == before\n"
            "QUEUE.clear()\n"
            "assert skip() is None\n"
        ),
        file_a="playlist.py",
        fn_a="enqueue",
        job_a=(
            "You own playlist.py. Write enqueue(title) so a real title is put at the end and the queue "
            "is returned. A blank title, or a title that is only spaces, is not added."
        ),
        gate_a="blank",
        file_b="player.py",
        fn_b="skip",
        job_b=(
            "You own player.py. Write skip() so it drops the first song and returns the new first song. "
            "When the queue is empty, return None instead of crashing."
        ),
        gate_b="empty",
        rule="The rule: a blank title is not queued, or an empty queue returns None",
        adequate="In playlist.py, add enqueue(title). Put a real title at the end and return the queue. A blank title is not added.",
        bare="playlist.py enqueue(title) with a blank title stays out of the queue.",
        partial="Please add enqueue in playlist.py.",
        vague="Build the playlist.",
        reply="Updated playlist.py.",
    ),
    _round(
        id="task-board",
        title="Task board",
        brief="A shared board where one person adds a task and the other marks it done. You add one of those two functions.",
        hint="Name the file and the function. 'Build the board' makes Grok guess.",
        ask=_ASK,
        index="tasks.py add_task\ndone.py mark_done\nnames.py and board.py are already written.",
        files=_BOARD_FILES,
        solutions=_BOARD_SOLUTIONS,
        check=(
            "import board\n"
            "from done import mark_done\n"
            "from tasks import TASKS, add_task\n"
            "tasks = board.finish('print the QR')\n"
            "assert any(task['title'] == 'print the QR' and task['done'] and task.get('stamp') == 'booth' for task in tasks)\n"
            "assert add_task('   ') is None\n"
            "assert all(str(task['title']).strip() for task in TASKS)\n"
            "assert mark_done('missing task') is None\n"
        ),
        file_a="tasks.py",
        fn_a="add_task",
        job_a=(
            "You own tasks.py. Write add_task(title) so a real title is stored as an open task and returned. "
            "A blank title, or a title that is only spaces, is not stored and returns None."
        ),
        gate_a="blank",
        file_b="done.py",
        fn_b="mark_done",
        job_b=(
            "You own done.py. Write mark_done(title) so the matching task is marked done and its stamp "
            "is set to booth, then that task is returned. A missing title returns None."
        ),
        gate_b="stamp",
        rule="The rule: a blank title is not stored, or a finished task gets stamp booth",
        adequate="In tasks.py, add add_task(title). Store a real title as an open task and return it. A blank title is not stored.",
        bare="tasks.py add_task(title) with a blank title stays off the board.",
        partial="Please add add_task in tasks.py.",
        vague="Build the task board.",
        reply="Updated tasks.py.",
    ),
)
