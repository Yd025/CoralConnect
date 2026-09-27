"""Pair rounds where two people each add a function to a small app."""

from __future__ import annotations

import re

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
    file_b: str,
    fn_b: str,
    job_b: str,
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
        beats=(
            Beat(
                ask=ask,
                fixture_title="Project files",
                fixture=index.strip(),
                facts=(
                    Fact(
                        "file",
                        f"Which file: {file_a} or {file_b}",
                        ((re.escape(file_a), re.escape(file_b)),),
                    ),
                    Fact(
                        "function",
                        f"Which function: {fn_a} or {fn_b}",
                        ((rf"\b{fn_a}\b", rf"\b{fn_b}\b"),),
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
        "ROOMS = {'general': ['Ada', 'Sam']}\n\n\ndef who_is_here(room):\n    raise NotImplementedError\n",
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
        "    message = {'room': room, 'user': user, 'text': text}\n"
        "    MESSAGES.append(message)\n"
        "    return message\n",
    ),
    (
        "presence.py",
        "ROOMS = {'general': ['Ada', 'Sam']}\n\n\n"
        "def who_is_here(room):\n"
        "    return list(ROOMS.get(room, []))\n",
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
        "def add_item(cart, name):\n    cart.append(name)\n    return cart\n",
    ),
    (
        "receipt.py",
        "def total(cart, menu):\n    return sum(menu[name] for name in cart)\n",
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
        "    GUESTS[name] = True\n"
        "    return name\n",
    ),
    (
        "badge.py",
        "def make_badge(name):\n    return f'HELLO my name is {name}'\n",
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
        "            return task\n"
        "    return None\n",
    ),
)

_ASK = (
    "You each add one function. Name the file and the function in your prompt. "
    "Grok edits that file. Your partner is editing a different one."
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
            "result = app.show('general', 'Ada', 'hello')\n"
            "assert result['message']['text'] == 'hello'\n"
            "assert 'Ada' in result['here']\n"
        ),
        file_a="messages.py",
        fn_a="send_message",
        job_a="Add send_message(room, user, text) in messages.py. It saves the message and returns it.",
        file_b="presence.py",
        fn_b="who_is_here",
        job_b="Add who_is_here(room) in presence.py. It returns the people in that room.",
        adequate="In messages.py, add send_message(room, user, text). Save the message and return it.",
        bare="messages.py send_message(room, user, text) saves the message.",
        partial="Please add send_message to the chat.",
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
            "cart = []\n"
            "assert counter.sale(cart, 'coffee') == 3\n"
            "assert counter.sale(cart, 'muffin') == 7\n"
        ),
        file_a="cart.py",
        fn_a="add_item",
        job_a="Add add_item(cart, name) in cart.py. It appends the snack and returns the cart.",
        file_b="receipt.py",
        fn_b="total",
        job_b="Add total(cart, menu) in receipt.py. It adds up the prices and returns the amount.",
        adequate="In receipt.py, add total(cart, menu). Look up each price and return the sum.",
        bare="receipt.py total(cart, menu) sums the prices.",
        partial="Please add total to the counter.",
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
            "from guests import GUESTS\n"
            "assert desk.welcome('Sam') == 'HELLO my name is Sam'\n"
            "assert GUESTS['Sam'] is True\n"
        ),
        file_a="checkin.py",
        fn_a="check_in",
        job_a="Add check_in(name) in checkin.py. It marks that guest as arrived.",
        file_b="badge.py",
        fn_b="make_badge",
        job_b="Add make_badge(name) in badge.py. It returns HELLO my name is, then the name.",
        adequate="In badge.py, add make_badge(name). Return HELLO my name is, then the name.",
        bare="badge.py make_badge(name) is the guest badge text.",
        partial="Please add make_badge for the guest.",
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
            "assert booth.play('Tide', 'Reef') == 'Reef'\n"
        ),
        file_a="playlist.py",
        fn_a="enqueue",
        job_a="Add enqueue(title) in playlist.py. It puts the song at the end and returns the queue.",
        file_b="player.py",
        fn_b="skip",
        job_b="Add skip() in player.py. It drops the first song and returns the new one.",
        adequate="In playlist.py, add enqueue(title). Put the title at the end and return the queue.",
        bare="playlist.py enqueue(title) puts a song at the end.",
        partial="Please add enqueue for the booth.",
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
            "tasks = board.finish('print the QR')\n"
            "assert any(task['title'] == 'print the QR' and task['done'] for task in tasks)\n"
        ),
        file_a="tasks.py",
        fn_a="add_task",
        job_a="Add add_task(title) in tasks.py. It stores the title as an open task and returns it.",
        file_b="done.py",
        fn_b="mark_done",
        job_b="Add mark_done(title) in done.py. It finds that task and marks it done.",
        adequate="In tasks.py, add add_task(title). Store the title as open and return it.",
        bare="tasks.py add_task(title) keeps an open task.",
        partial="Please add add_task for the team.",
        vague="Build the task board.",
        reply="Updated tasks.py.",
    ),
)
