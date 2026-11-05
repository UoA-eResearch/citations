"""The prompt battery (plan section 0): six families from fixed templates and word lists, written before the model
was run on any prompt. Selection (top-1 = target with logit margin >= 2) is done by select_prompts.py.

  prompts.py -> data/prompt_candidates.jsonl (family, prompt, target)
"""
import json
import random
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "prompt_candidates.jsonl"

CAPITALS = [("France", "Paris"), ("Japan", "Tokyo"), ("Italy", "Rome"), ("Germany", "Berlin"), ("Spain", "Madrid"),
            ("Russia", "Moscow"), ("Egypt", "Cairo"), ("Greece", "Athens"), ("China", "Beijing"), ("Canada", "Ottawa"),
            ("Kenya", "Nairobi"), ("Peru", "Lima"), ("Norway", "Oslo"), ("Sweden", "Stockholm"), ("Poland", "Warsaw"),
            ("Austria", "Vienna"), ("Portugal", "Lisbon"), ("Ireland", "Dublin"), ("Thailand", "Bangkok"),
            ("Argentina", "Buenos Aires"), ("Turkey", "Ankara"), ("India", "New Delhi"), ("Cuba", "Havana"),
            ("Chile", "Santiago"), ("Belgium", "Brussels"), ("Hungary", "Budapest"), ("Finland", "Helsinki"),
            ("Denmark", "Copenhagen"), ("Iran", "Tehran"), ("Iraq", "Baghdad"), ("Vietnam", "Hanoi"),
            ("Indonesia", "Jakarta"), ("Australia", "Canberra"), ("Mexico", "Mexico City"), ("Colombia", "Bogotá")]
ELEMENTS = [("gold", "Au"), ("silver", "Ag"), ("iron", "Fe"), ("sodium", "Na"), ("potassium", "K"), ("lead", "Pb"),
            ("copper", "Cu"), ("tin", "Sn"), ("mercury", "Hg"), ("oxygen", "O"), ("hydrogen", "H"), ("carbon", "C")]
LANDMARKS = [("the Eiffel Tower", "Paris"), ("the Colosseum", "Rome"), ("the Brandenburg Gate", "Berlin"),
             ("the Kremlin", "Moscow"), ("the Acropolis", "Athens"), ("the Great Wall", "Beijing"),
             ("Mount Fuji", "Tokyo"), ("the Sagrada Familia", "Madrid"), ("the Pyramids of Giza", "Cairo"),
             ("Machu Picchu", "Lima"), ("the Taj Mahal", "New Delhi"), ("Angkor Wat", "Phnom Penh"),
             ("the Little Mermaid statue", "Copenhagen"), ("the Leaning Tower of Pisa", "Rome"),
             ("Neuschwanstein Castle", "Berlin"), ("the Alhambra", "Madrid"), ("Uluru", "Canberra"),
             ("the CN Tower", "Ottawa"), ("the Blue Mosque", "Ankara"), ("Chichen Itza", "Mexico City")]
ANTONYMS = {"French": [("chaud", "froid"), ("grand", "petit"), ("jour", "nuit"), ("haut", "bas"), ("vrai", "faux"),
                       ("noir", "blanc"), ("riche", "pauvre"), ("jeune", "vieux"), ("lent", "rapide"), ("ouvert", "fermé")],
            "Spanish": [("caliente", "frío"), ("grande", "pequeño"), ("día", "noche"), ("alto", "bajo"), ("bueno", "malo"),
                        ("negro", "blanco"), ("rico", "pobre"), ("joven", "viejo"), ("lento", "rápido"), ("abierto", "cerrado")],
            "German": [("heiß", "kalt"), ("groß", "klein"), ("Tag", "Nacht"), ("hoch", "tief"), ("gut", "schlecht"),
                       ("schwarz", "weiß"), ("reich", "arm"), ("jung", "alt"), ("langsam", "schnell"), ("offen", "geschlossen")]}
NAMES = ["Mary", "John", "Alice", "Bob", "Sarah", "David", "Emma", "James", "Laura", "Michael", "Anna", "Tom"]
PLACES = ["store", "park", "school", "beach", "library", "market"]
OBJECTS = ["a drink", "a book", "a gift", "a letter", "an apple", "a ticket"]
WORDS = ["apple", "river", "table", "cloud", "garden", "pencil", "window", "orange", "mountain", "candle", "bottle",
         "forest", "planet", "silver", "rocket", "violin", "basket", "dragon", "harbor", "lemon"]


def main():
    rng = random.Random(20261105)
    rows = []
    for c, cap in CAPITALS:
        rows.append(("factual", f"The capital of {c} is", " " + cap))
    for el, sym in ELEMENTS:
        rows.append(("factual", f"The chemical symbol for {el} is", " " + sym))
    for lm, cap in LANDMARKS:
        rows.append(("two_hop", f"The capital of the country where {lm} is located is", " " + cap))
    for lang, pairs in ANTONYMS.items():
        for a, b in pairs:
            rows.append(("antonym", f'The opposite of "{a}" in {lang} is "', b))
    for _ in range(45):
        a, b = rng.sample(NAMES, 2); pl = rng.choice(PLACES); ob = rng.choice(OBJECTS)
        rows.append(("ioi", f"When {a} and {b} went to the {pl}, {b} gave {ob} to", " " + a))
    for _ in range(45):
        seq = rng.sample(WORDS, 6)
        rows.append(("induction", " ".join(seq) + " | " + " ".join(seq[:5]), " " + seq[5]))
    for a in range(1, 9):
        for b in range(1, 10 - a):
            rows.append(("arithmetic", f"{a} + {b} =", " " + str(a + b)))
    # D1 (added after the first selection kept 111 of 223, with two-hop 0, antonym 1 and IOI 14; before any graph):
    # one worked example in the prompt for two-hop and antonyms (the example is never a target), and 90 more IOI prompts.
    demo_lm, demo_cap = LANDMARKS[1]
    for lm, cap in LANDMARKS:
        if lm == demo_lm:
            continue
        rows.append(("two_hop", f"Q: What is the capital of the country where {demo_lm} is located? A: {demo_cap}\n"
                                f"Q: What is the capital of the country where {lm} is located? A:", " " + cap))
    for lang, pairs in ANTONYMS.items():
        for i, (a, b) in enumerate(pairs):
            da, db = pairs[(i + 1) % len(pairs)]
            rows.append(("antonym", f'{lang} opposites: "{da}" -> "{db}"; "{a}" -> "', b))
    rng2 = random.Random(20261106)
    for _ in range(90):
        a, b = rng2.sample(NAMES, 2); pl = rng2.choice(PLACES); ob = rng2.choice(OBJECTS)
        rows.append(("ioi", f"After {a} and {b} arrived at the {pl}, {b} handed {ob} to", " " + a))
    # D1 round 2 (two-hop kept 3 and antonym 10 even with a worked example): more prompts in the families the model
    # handles - induction (second seed), subtraction, more capitals.
    rng3 = random.Random(20261107)
    for _ in range(60):
        seq = rng3.sample(WORDS, 6)
        rows.append(("induction", " ".join(seq) + " | " + " ".join(seq[:5]), " " + seq[5]))
    for a in range(2, 10):
        for b in range(1, a):
            rows.append(("arithmetic", f"{a} - {b} =", " " + str(a - b)))
    for c, cap in [("Morocco", "Rabat"), ("Nigeria", "Abuja"), ("Ukraine", "Kyiv"), ("Romania", "Bucharest"),
                   ("Bulgaria", "Sofia"), ("Serbia", "Belgrade"), ("Croatia", "Zagreb"), ("Czechia", "Prague"),
                   ("Switzerland", "Bern"), ("Netherlands", "Amsterdam"), ("Philippines", "Manila"),
                   ("Malaysia", "Kuala Lumpur"), ("Pakistan", "Islamabad"), ("Bangladesh", "Dhaka"),
                   ("Nepal", "Kathmandu"), ("Venezuela", "Caracas"), ("Ecuador", "Quito"), ("Uruguay", "Montevideo"),
                   ("Ethiopia", "Addis Ababa"), ("Ghana", "Accra"), ("Senegal", "Dakar"), ("Algeria", "Algiers"),
                   ("Tunisia", "Tunis"), ("Lebanon", "Beirut"), ("Syria", "Damascus"), ("Jordan", "Amman"),
                   ("Saudi Arabia", "Riyadh"), ("Qatar", "Doha"), ("Mongolia", "Ulaanbaatar"), ("Iceland", "Reykjavik")]:
        rows.append(("factual", f"The capital of {c} is", " " + cap))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for fam, p, t in rows:
            f.write(json.dumps({"family": fam, "prompt": p, "target": t}, ensure_ascii=False) + "\n")
    from collections import Counter
    print(len(rows), "candidates", dict(Counter(r[0] for r in rows)))


if __name__ == "__main__":
    main()
