import random

def generate_move_code():
    sonlar = []

    while len(sonlar) < 3:
        son = random.randint(0, 9)
        
        if son not in sonlar:
            sonlar.append(son)

    kod = str(sonlar[0]) + str(sonlar[1]) + str(sonlar[2])

    return kod
