from aiogram.fsm.state import State, StatesGroup


class AdminMovie(StatesGroup):
    movie_file = State()
    movie_desc = State()

class ReklamaState(StatesGroup):
    reklama_text = State()
    reklama_confirm = State()