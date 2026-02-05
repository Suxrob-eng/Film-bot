from aiogram.fsm.state import State, StatesGroup


class AdminMovie(StatesGroup):
    movie_file = State()
    movie_desc = State()