import datetime
import json
import random

from flask import Flask, render_template, request

app = Flask(__name__)

with open("cmudict-0.7b.txt", "r", encoding="latin-1") as file:
    data = file.read()

rhymes = {}
all_words = []
words_to_phonemes = {}
words_to_full_phonemes = {}

for rhyme in data.split("\n"):
    if not rhyme.startswith(";;;"):
        if "  " not in rhyme:
            continue
        word, phonemes = rhyme.split("  ")
        word = word.lower()
        phonemes = phonemes.strip()  # .replace()
        words_to_full_phonemes[word] = phonemes
        # get last 3 like EY2 Z from S AO1 R D P L EY2 Z
        phonemes = " ".join(phonemes.split(" ")[-3:])

        if phonemes in rhymes:
            rhymes[phonemes].append(word)
        else:
            rhymes[phonemes] = [word]

        all_words.append(word)
        words_to_phonemes[word] = phonemes

# open count_1w.txt
word_counts = {}

with open("count_1w.txt", "r") as file:
    for line in file:
        word, count = line.split("\t")
        word_counts[word] = int(count)

# get count of last word in top quartile
quartile = len(word_counts) // 4
top_quartile = sorted(word_counts.values(), reverse=True)[:quartile]
threshold = top_quartile[-1]

VOWEL_PHONEMES = set("AEIOUWY")

def get_syllable_count(word):
    return len([p for p in words_to_full_phonemes[word].split() if p[0] in VOWEL_PHONEMES])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        words = request.form["word"]

        phoneme = words_to_phonemes.get(words.lower())

        rhyming_words = rhymes.get(phoneme, [])
        rhyming_words = [w.split("(")[0] for w in rhyming_words if "-" not in w and w != words.lower()]
        rhyming_words = sorted(rhyming_words, key=lambda w: word_counts.get(w, 0), reverse=True)
        # add "tq" to end of every word in top quartile
        # print phoneme for polaris
        print(words_to_phonemes["polaris"])
        syllables = {w: get_syllable_count(w) for w in rhyming_words}
        
        # zip results
        results = [
            {"word": w, "syllables": s, "in_top_quartile": word_counts.get(w, 0) >= threshold}
            for w, s in syllables.items()
        ]
        
        # break into {syllable_count: [words]}
        results_as_syllables = {}

        for result in results:
            if result["syllables"] in results_as_syllables:
                results_as_syllables[result["syllables"]].append(result)
            else:
                results_as_syllables[result["syllables"]] = [result]

        # sort results by syllable by usage
        for syllable, words in results_as_syllables.items():
            results_as_syllables[syllable] = sorted(words, key=lambda w: word_counts.get(w["word"], 0), reverse=True)

        results_as_syllables = dict(sorted(results_as_syllables.items()))

        return render_template(
            "index.html",
            words=words,
            rhyming_words=results,
            q=request.form["word"],
            results_as_syllables=results_as_syllables,
            rhyming_words_count=len(rhyming_words),
            is_playing=True
        )

    return render_template(
        "index.html"
    )


if __name__ == "__main__":
    app.run(debug=True)
