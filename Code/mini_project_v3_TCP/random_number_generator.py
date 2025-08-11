# random_number_generator.py
import random
import json
import os

USED_NUMBERS_FILE = "used_numbers.json"
MIN = 1
MAX = 10000  # Define your range here


def load_used_numbers():
    if not os.path.exists(USED_NUMBERS_FILE):
        return set()
    with open(USED_NUMBERS_FILE, "r") as f:
        return set(json.load(f))


def save_used_numbers(used_numbers):
    with open(USED_NUMBERS_FILE, "w") as f:
        json.dump(list(used_numbers), f)


def generate_unique_random_number():
    used_numbers = load_used_numbers()
    attempts = 0
    while attempts < 1000:
        rand_num = random.randint(MIN, MAX)
        if rand_num not in used_numbers:
            used_numbers.add(rand_num)
            save_used_numbers(used_numbers)
            return rand_num
        attempts += 1
    raise RuntimeError("Unable to find a unique random number.")

def generate_random_number():
    rand_num = random.randint(MIN, MAX)
    return rand_num

if __name__ == "__main__":
    print(generate_unique_random_number())
