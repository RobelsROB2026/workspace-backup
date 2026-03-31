#!/usr/bin/env python3
"""
Clean pass: separate actual scripts from textbook/theory chapters
and re-run key metrics on scripts-only subset.
"""

import os, re
from collections import Counter, defaultdict
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

SCRIPT_DIR = Path(__file__).parent
CORPUS_FILES = sorted(SCRIPT_DIR.glob("*.txt"))

# Files that are clearly textbook/theory (not hypnotic scripts)
THEORY_FILES = {
    'сущность_гипноза_das_wesen_der_hypnose_schilder_1926_hypnose.txt',  # German theory
    'de_laurence_hypnotism_and_magnetism_de_laurence_-_hypnotism_.txt',    # De Laurence textbook
    'der_sogenannte_animalische_magnetismus_oder_hypnotismus_unte.txt',    # German theory
    'eine_experimentelle_studie_auf_dem_gebiete_des_hypnotismus_b.txt',    # German experiment
    'when_the_subconscious_mind_speaks_when_the_subconscious_mind.txt',    # Case study prose
    'creative_visualization_use_the_power_of_your_imagination_to_.txt',    # Self-help book
    'hypnosis_-_chapter_1.txt', 'hypnosis_-_chapter_2.txt',
    'hypnosis_-_chapter_3.txt', 'hypnosis_-_chapter_4.txt',
    'hypnosis_-_chapter_5.txt', 'hypnosis_-_chapter_6.txt',
    'hypnosis_-_chapter_7.txt',
    'a_practical_guide_to_self-hypnosis_ch1.txt',
    'a_practical_guide_to_self-hypnosis_ch2.txt',
    'a_practical_guide_to_self-hypnosis_ch3.txt',
    'a_practical_guide_to_self-hypnosis_ch4.txt',
    'a_practical_guide_to_self-hypnosis_ch5.txt',
    'a_practical_guide_to_self-hypnosis_ch6.txt',
    'a_practical_guide_to_self-hypnosis_ch7.txt',
    'a_practical_guide_to_self-hypnosis_ch8.txt',
    'a_practical_guide_to_self-hypnosis_ch9.txt',
    'a_practical_guide_to_self-hypnosis_ch10.txt',
    'a_practical_guide_to_self-hypnosis_ch11.txt',
    'a_practical_guide_to_self-hypnosis_ch12.txt',
    'a_practical_guide_to_self-hypnosis_ch13.txt',
    'a_practical_guide_to_self-hypnosis_ch14.txt',
    'a_practical_guide_to_self-hypnosis_ch15.txt',
    'a_practical_guide_to_self-hypnosis_ch16.txt',
    'a_practical_guide_to_self-hypnosis_ch17.txt',
    'a_practical_guide_to_self-hypnosis_ch18.txt',
}

INDUCTION_KEYWORDS = ['induction', 'method', 'deepening', 'deepener', 'relaxation_technique',
                       'body_conditioning', 'progressive_relaxation', 'arm_levitation',
                       'eye_fixation', 'countdown', 'self-hypnosis_ch', 'trance',
                       'awareness_induction', 'favorite_place', 'forest_and_stream',
                       'enchanted_forest', 'higher_consciousness']

THERAPY_KEYWORDS = ['anxiety', 'phobia', 'smoking', 'weight', 'pain', 'anger', 'stress',
                    'confidence', 'sleep', 'insomnia', 'depression', 'fear', 'habit',
                    'addiction', 'bereavement', 'grief', 'trauma', 'healing', 'therapy',
                    'blushing', 'baldness', 'nail_biting', 'stuttering', 'jealousy',
                    'motivation', 'self_esteem', 'panic', 'ocd', 'ptsd', 'exam',
                    'public_speaking', 'impotence', 'fertility', 'ibs', 'migraine',
                    'breast', 'abandoned', 'reward', 'business', 'sales', 'sport',
                    'golf', 'learning', 'memory', 'focus', 'creativity',
                    'coping', 'dating', 'divorce', 'driving', 'eating', 'food',
                    'fasting', 'gastric', 'chocolate', 'communication', 'compassion',
                    'optimism', 'love', 'resilience', 'worrier', 'vegetable', 'fruit',
                    'language_study', 'cheek', 'autogenic', 'cyber', 'end_of_life',
                    'noisy', 'healthy']

def categorize(fname):
    fn = fname.lower()
    if fname in THEORY_FILES:
        return 'theory'
    for kw in INDUCTION_KEYWORDS:
        if kw in fn:
            return 'induction'
    for kw in THERAPY_KEYWORDS:
        if kw in fn:
            return 'therapeutic'
    # Remaining _script files are therapeutic
    if '_script' in fn or '_scripts' in fn:
        return 'therapeutic'
    return 'theory'  # conservative: if unclear, it's theory

stop_words = set(stopwords.words('english'))

# Load
scripts_text = []
theory_text = []
induction_text = []
therapeutic_text = []
file_cats = {}

for f in CORPUS_FILES:
    if f.name.endswith('.py'):
        continue
    text = f.read_text(encoding='utf-8', errors='ignore')
    cat = categorize(f.name)
    file_cats[f.name] = cat
    if cat == 'theory':
        theory_text.append(text)
    else:
        scripts_text.append(text)
        if cat == 'induction':
            induction_text.append(text)
        else:
            therapeutic_text.append(text)

print(f"=== CORPUS SPLIT ===")
print(f"Script files: {len(scripts_text)}")
print(f"Theory files: {len(theory_text)}")
scripts_words = sum(len(t.split()) for t in scripts_text)
theory_words = sum(len(t.split()) for t in theory_text)
ind_words = sum(len(t.split()) for t in induction_text)
ther_words = sum(len(t.split()) for t in therapeutic_text)
print(f"Script words: {scripts_words}")
print(f"Theory words: {theory_words}")
print(f"Induction: {len(induction_text)} files, {ind_words} words")
print(f"Therapeutic: {len(therapeutic_text)} files, {ther_words} words")

# Analysis on SCRIPTS ONLY
full = '\n'.join(scripts_text)
sentences = sent_tokenize(full)
words = word_tokenize(full.lower())
words_alpha = [w for w in words if w.isalpha()]
word_freq = Counter(words_alpha)
total_words = len(words_alpha)
unique_words = len(word_freq)
content_words = [w for w in words_alpha if w not in stop_words]
content_freq = Counter(content_words)

print(f"\n=== SCRIPTS-ONLY METRICS ===")
print(f"Sentences: {len(sentences)}")
print(f"Words: {total_words}, Unique: {unique_words}")

# Lexical density
ld = len(content_words) / total_words
print(f"Lexical density: {ld:.4f} ({ld*100:.2f}%)")

# TTR and MATTR
ttr = unique_words / total_words
window = 1000
mattr_vals = []
for i in range(0, len(words_alpha) - window, window // 2):
    chunk = words_alpha[i:i+window]
    mattr_vals.append(len(set(chunk)) / window)
mattr = sum(mattr_vals) / len(mattr_vals) if mattr_vals else 0
print(f"TTR: {ttr:.4f}")
print(f"MATTR (w=1000): {mattr:.4f}")

# Per-category lexical density
for label, txts in [('induction', induction_text), ('therapeutic', therapeutic_text)]:
    cat_ws = [w.lower() for t in txts for w in word_tokenize(t) if w.isalpha()]
    cat_cw = [w for w in cat_ws if w not in stop_words]
    cat_ld = len(cat_cw) / max(len(cat_ws), 1)
    print(f"  [{label}] lexical density: {cat_ld:.4f} ({cat_ld*100:.2f}%)")

full_lower = full.lower()

# === SYNTACTIC STRUCTURE ===
print(f"\n=== SYNTACTIC STRUCTURE (scripts only) ===")

IMPERATIVE_VERBS = [
    'let', 'relax', 'close', 'feel', 'notice', 'allow', 'imagine', 'breathe',
    'focus', 'listen', 'open', 'think', 'look', 'take', 'go', 'drift', 'sleep',
    'rest', 'sink', 'drop', 'float', 'begin', 'continue', 'repeat', 'picture',
    'visualize', 'remember', 'enjoy', 'experience', 'try', 'keep', 'just',
    'simply', 'now', 'stop', 'see', 'hear', 'sense', 'become', 'move', 'place',
    'hold', 'release', 'count', 'say', 'tell', 'make', 'give', 'find', 'bring',
    'accept', 'embrace', 'surrender', 'pay', 'concentrate', 'sit', 'lie',
    'press', 'lift', 'lower', 'turn', 'shift', 'send', 'draw', 'pull', 'push',
    'step', 'walk', 'enter', 'leave', 'come', 'return', 'watch', 'observe'
]

PERMISSIVE_MARKERS = ['can', 'may', 'might', 'could', 'perhaps', 'maybe',
                       'wonder', 'wondering', 'possibly', 'probably']

def analyze_syntax(sents):
    imperatives = 0
    permissive = 0
    you_initial = 0
    questions = 0
    imperative_verbs = Counter()

    for s in sents:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        s_lower = s_stripped.lower()
        first_words = s_lower.split()[:4]
        if not first_words:
            continue

        if s_stripped.endswith('?'):
            questions += 1

        if first_words[0] in ('you', "you're", "you'll", "your"):
            you_initial += 1
            continue

        found_perm = False
        for i, fw in enumerate(first_words[:3]):
            if fw in PERMISSIVE_MARKERS:
                permissive += 1
                found_perm = True
                break
        if not found_perm and ('you can' in s_lower[:40] or 'you may' in s_lower[:40] or
                                'you might' in s_lower[:40] or 'you could' in s_lower[:40]):
            permissive += 1
            found_perm = True
        if found_perm:
            continue

        check_word = first_words[0]
        if check_word in ('and', 'but', 'so', 'then', 'now', 'just', 'simply'):
            for fw in first_words[1:]:
                if fw not in ('and', 'but', 'so', 'then', 'now', 'just', 'simply'):
                    check_word = fw
                    break

        if check_word in IMPERATIVE_VERBS:
            imperatives += 1
            imperative_verbs[check_word] += 1

    return {
        'total': len(sents), 'imperatives': imperatives,
        'permissive': permissive, 'you_initial': you_initial,
        'questions': questions, 'imperative_verbs': imperative_verbs
    }

r = analyze_syntax(sentences)
print(f"Sentences: {r['total']}")
print(f"Imperatives: {r['imperatives']} ({100*r['imperatives']/r['total']:.1f}%)")
print(f"Permissive: {r['permissive']} ({100*r['permissive']/r['total']:.1f}%)")
print(f"You-initial: {r['you_initial']} ({100*r['you_initial']/r['total']:.1f}%)")
print(f"Questions: {r['questions']} ({100*r['questions']/r['total']:.1f}%)")
ratio = r['imperatives'] / max(r['permissive'], 1)
print(f"Imperative:Permissive = {ratio:.2f}:1")
covert = r['imperatives'] + r['you_initial']
print(f"True directive rate (imp + you-init): {covert} ({100*covert/r['total']:.1f}%)")
print(f"\nTop imperative verbs: {r['imperative_verbs'].most_common(25)}")

# Per-category
for label, txts in [('induction', induction_text), ('therapeutic', therapeutic_text)]:
    cat_sents = []
    for t in txts:
        cat_sents.extend(sent_tokenize(t))
    cr = analyze_syntax(cat_sents)
    cratio = cr['imperatives'] / max(cr['permissive'], 1)
    covert_r = cr['imperatives'] + cr['you_initial']
    print(f"\n  [{label}] sents={cr['total']}, imp={cr['imperatives']} ({100*cr['imperatives']/max(cr['total'],1):.1f}%), "
          f"perm={cr['permissive']} ({100*cr['permissive']/max(cr['total'],1):.1f}%), "
          f"you_init={cr['you_initial']} ({100*cr['you_initial']/max(cr['total'],1):.1f}%), "
          f"ratio={cratio:.2f}:1, "
          f"true_directive={100*covert_r/max(cr['total'],1):.1f}%")
    print(f"    Top verbs: {cr['imperative_verbs'].most_common(10)}")

# === KEY VERB ANALYSIS ===
print(f"\n=== MASTER VERBS (scripts only) ===")
VERBS = ['feel', 'let', 'relax', 'allow', 'imagine', 'notice', 'close', 'open',
         'breathe', 'sleep', 'drift', 'float', 'sink', 'go', 'come', 'become',
         'find', 'take', 'think', 'know', 'see', 'hear', 'sense', 'focus',
         'keep', 'begin', 'continue', 'move', 'release', 'accept', 'enjoy',
         'experience', 'remember', 'visualize', 'want', 'try', 'make', 'give',
         'look', 'watch', 'listen', 'rest', 'drop', 'flow', 'spread', 'grow',
         'change', 'count', 'say', 'tell', 'need', 'wish', 'hope', 'believe',
         'trust', 'wonder', 'realize', 'understand', 'discover', 'learn']

verb_counts = Counter()
for v in VERBS:
    c = word_freq.get(v, 0)
    if c > 0:
        verb_counts[v] = c

for v, c in verb_counts.most_common(30):
    print(f"  {v}: {c} ({1000*c/total_words:.2f}/1k)")

# let collocations
print(f"\n'let' collocations:")
let_patterns = re.findall(r'\blet (\w+ \w+ ?\w*)', full_lower)
let_freq = Counter(let_patterns)
for p, c in let_freq.most_common(20):
    print(f"  'let {p}': {c}")

# Verb clusters around 'let'
print(f"\nVerb neighbors of 'let' (within 10 words):")
let_nbrs = Counter()
for i, w in enumerate(words_alpha):
    if w == 'let':
        window = words_alpha[max(0,i-10):i] + words_alpha[i+1:i+11]
        for ww in window:
            if ww in set(VERBS) and ww != 'let':
                let_nbrs[ww] += 1
for v, c in let_nbrs.most_common(15):
    print(f"  {v}: {c}")

# === NOMINALIZATIONS ===
print(f"\n=== NOMINALIZATIONS (scripts only) ===")
NOMS = ['relaxation', 'sensation', 'awareness', 'comfort', 'calmness', 'drowsiness',
        'peacefulness', 'contentment', 'heaviness', 'lightness', 'warmth', 'coolness',
        'numbness', 'tingling', 'deepening', 'healing', 'understanding', 'confidence',
        'strength', 'tranquility', 'serenity', 'stillness', 'quietness',
        'imagination', 'visualization', 'concentration', 'attention', 'consciousness',
        'transformation', 'movement', 'pleasure', 'happiness', 'acceptance',
        'permission', 'freedom', 'release', 'relief', 'resolution', 'realization',
        'discovery', 'connection', 'harmony', 'balance', 'security', 'safety',
        'protection', 'ability', 'possibility', 'potential', 'experience', 'feeling']

nom_counts = Counter()
for n in NOMS:
    c = word_freq.get(n, 0)
    if c > 0:
        nom_counts[n] = c

total_noms = sum(nom_counts.values())
print(f"Total: {total_noms} tokens, {len(nom_counts)} types")
print(f"Per 1000 words: {1000*total_noms/total_words:.2f}")
for n, c in nom_counts.most_common(20):
    print(f"  {n}: {c}")

# === EMBEDDED COMMANDS ===
print(f"\n=== EMBEDDED COMMANDS (scripts only) ===")
patterns = [
    (r'you can (?:just |simply )?(\w+)', 'you can [V]'),
    (r'i want you to (\w+)', 'I want you to [V]'),
    (r'you might (?:just |simply )?(\w+)', 'you might [V]'),
    (r'allow yourself to (\w+)', 'allow yourself to [V]'),
    (r'perhaps you (?:can |could |will |might )?(\w+)', 'perhaps you [V]'),
    (r"don't (?:try|need|have) to (\w+)", "don't try to [V]"),
    (r'you don\'?t (?:need|have) to (\w+)', "you don't need to [V]"),
    (r'you find yourself (\w+ing)', 'you find yourself [V]ing'),
    (r'i wonder if you', 'I wonder if you...'),
    (r'there\'?s? no need to (\w+)', "no need to [V]"),
]
total_emb = 0
for pat, label in patterns:
    c = len(re.findall(pat, full_lower))
    total_emb += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total: {total_emb}")
print(f"Per 1000 words: {1000*total_emb/total_words:.2f}")

# === PACING/LEADING ===
print(f"\n=== PACING/LEADING (scripts only) ===")
pacing = [
    ('as you', r'\bas you\b'), ('when you', r'\bwhen you\b'),
    ('while you', r'\bwhile you\b'), ('the more you', r'\bthe more you\b'),
    ('with each', r'\bwith each\b'), ('with every', r'\bwith every\b'),
    ('each time', r'\beach time\b'), ('every time', r'\bevery time\b'),
    ('and now', r'\band now\b'), ('deeper and deeper', r'\bdeeper and deeper\b'),
    ('more and more', r'\bmore and more\b'),
]
for label, pat in pacing:
    c = len(re.findall(pat, full_lower))
    print(f"  '{label}': {c}")

# Full pacing-leading (as you X... you Y)
pl = re.findall(r'\b(as you|while you|when you|the more you)\b[^.]{5,60}\b(you (?:will|can|begin|feel|notice|find|become|are|may|might))\b', full_lower)
print(f"\nFull pacing→leading transitions: {len(pl)}")

# === REPETITION PATTERNS ===
print(f"\n=== REPETITION (scripts only) ===")
x_and_x = re.findall(r'\b(\w+) and \1\b', full_lower)
xax = Counter(x_and_x)
print("'X and X' intensifiers:")
for w, c in xax.most_common(15):
    print(f"  '{w} and {w}': {c}")

# === PRONOUNS ===
print(f"\n=== PRONOUNS (scripts only) ===")
you_forms = word_freq.get('you', 0) + word_freq.get('your', 0) + full_lower.count("you're") + full_lower.count("you'll")
i_forms = word_freq.get('i', 0) + word_freq.get('my', 0)
print(f"You-forms: {you_forms}")
print(f"I-forms: {i_forms}")
print(f"You:I ratio: {you_forms/max(i_forms,1):.2f}:1")
print(f"'you': {word_freq.get('you', 0)}")
print(f"'your': {word_freq.get('your', 0)}")

# === SENSORY CHANNELS ===
print(f"\n=== SENSORY CHANNELS (scripts only) ===")
VIS = ['see', 'look', 'watch', 'picture', 'visualize', 'imagine', 'image', 'color', 'light', 'bright', 'dark', 'glow', 'scene', 'view']
AUD = ['hear', 'listen', 'sound', 'voice', 'tone', 'quiet', 'silence', 'whisper', 'echo', 'noise', 'music']
KIN = ['feel', 'touch', 'warm', 'cool', 'heavy', 'light', 'soft', 'smooth', 'pressure', 'sensation', 'tingling', 'numbness', 'comfortable', 'relaxed', 'tension', 'tight', 'loose']

v = sum(word_freq.get(w, 0) for w in VIS)
a = sum(word_freq.get(w, 0) for w in AUD)
k = sum(word_freq.get(w, 0) for w in KIN)
t = v + a + k
print(f"Visual: {v} ({100*v/t:.1f}%)")
print(f"Auditory: {a} ({100*a/t:.1f}%)")
print(f"Kinesthetic: {k} ({100*k/t:.1f}%)")

# === PRESUPPOSITIONS ===
print(f"\n=== PRESUPPOSITIONS (scripts only) ===")
presup = [
    ('already', r'\balready\b'), ('beginning to', r'\bbeginning to\b'),
    ('continue to', r'\bcontinue to\b'), ('even more', r'\beven more\b'),
    ('deeper', r'\bdeeper\b'), ('further', r'\bfurther\b'),
    ('notice that', r'\bnotice that\b'), ('realize that', r'\brealize that\b'),
]
total_p = 0
for label, pat in presup:
    c = len(re.findall(pat, full_lower))
    total_p += c
    print(f"  {label}: {c}")
print(f"Total: {total_p}, per 1000 words: {1000*total_p/total_words:.2f}")

# === NEGATION ===
print(f"\n=== NEGATION (scripts only) ===")
negs = [("don't", r"\bdon't\b"), ('not', r'\bnot\b'), ('no', r'\bno\b'),
        ('never', r'\bnever\b'), ('nothing', r'\bnothing\b'), ('without', r'\bwithout\b'),
        ("can't", r"\bcan't\b"), ("won't", r"\bwon't\b")]
total_n = 0
for label, pat in negs:
    c = len(re.findall(pat, full_lower))
    total_n += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total: {total_n}, per 1000 words: {1000*total_n/total_words:.2f}")

# === SENTENCE LENGTH ===
print(f"\n=== SENTENCE LENGTH (scripts only) ===")
slens = [len(word_tokenize(s)) for s in sentences]
avg = sum(slens)/len(slens)
med = sorted(slens)[len(slens)//2]
print(f"Mean: {avg:.1f}, Median: {med}")

# Top 30 content words
print(f"\n=== TOP 30 CONTENT WORDS ===")
for w, c in content_freq.most_common(30):
    print(f"  {w}: {c}")

print("\n=== DONE ===")
