import os

# Tests open many games from one test client. The per-address cap has its own test.
os.environ.setdefault("SESSIONS_PER_IP", "0")
