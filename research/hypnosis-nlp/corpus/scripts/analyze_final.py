#!/usr/bin/env python3
"""
Final analysis: properly filtered corpus.
Pure scripts (you-density >= 50/1k) + mixed content (theory + embedded scripts).
Focus the signature analysis on pure scripts, use mixed for comparison.
"""

import os, re, json
from collections import Counter, defaultdict
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

SCRIPT_DIR = Path(__file__).parent
stop_words = set(stopwords.words('english'))

# Classify by you-density
def classify_file(fpath):
    text = fpath.read_text(encoding='utf-8', errors='ignore')
    words = text.split()
    total = len(words)
    if total < 30:
        return None, None, None
    you_count = sum(1 for w in words if w.lower() in ('you', 'your', "you're", "you'll", "you'd"))
    density = you_count * 1000 / total
    if density >= 50:
        return 'pure_script', text, density
    elif density >= 20:
        return 'mixed', text, density
    else:
        return 'theory', text, density

# Load and classify
pure_scripts = []
mixed = []
theory = []
all_files = {}

for f in sorted(SCRIPT_DIR.glob("*.txt")):
    cat, text, density = classify_file(f)
    if cat is None:
        continue
    all_files[f.name] = {'cat': cat, 'density': density, 'words': len(text.split())}
    if cat == 'pure_script':
        pure_scripts.append((f.name, text))
    elif cat == 'mixed':
        mixed.append((f.name, text))
    else:
        theory.append((f.name, text))

print(f"=== CORPUS CLASSIFICATION ===")
print(f"Pure scripts (you-density >= 50/1k): {len(pure_scripts)} files, {sum(len(t.split()) for _, t in pure_scripts)} words")
print(f"Mixed content (20-50/1k): {len(mixed)} files, {sum(len(t.split()) for _, t in mixed)} words")
print(f"Theory/navigation (<20/1k): {len(theory)} files, {sum(len(t.split()) for _, t in theory)} words")

print(f"\nPure script files:")
for name, text in pure_scripts:
    print(f"  {name} ({len(text.split())} words)")

# Subdivide pure scripts into induction vs therapeutic
INDUCTION_NAMES = {'arm_levitation_method.txt', 'awareness_induction.txt', 'body_conditioning.txt',
                   'clasp_induction.txt', 'confusion_method.txt', 'deep_relaxation_method.txt',
                   'direct_gaze_method.txt', 'drop_object_method.txt', 'elman_classic_induction.txt',
                   'elman_rapid_induction.txt', 'favorite_place.txt', 'fixation_object_method.txt',
                   'forest_and_stream.txt', 'hand_to_face_method.txt', 'handshake_method.txt',
                   'instantaneous_rapid_induction.txt', 'misdirection_method.txt', 'mountain_trip.txt',
                   'nlp_secrets_induction.txt', 'nlp_self_hypnosis_relaxation.txt',
                   'progressive_relaxation.txt', 'rapid_method.txt', 'seven_plus_or_minus_two.txt',
                   'stiff_arm_induction.txt'}

induction_texts = []
therapeutic_texts = []
for name, text in pure_scripts:
    if name in INDUCTION_NAMES:
        induction_texts.append((name, text))
    else:
        therapeutic_texts.append((name, text))

print(f"\n  Induction scripts: {len(induction_texts)}")
print(f"  Therapeutic scripts: {len(therapeutic_texts)}")
for name, text in therapeutic_texts:
    print(f"    {name} ({len(text.split())} words)")

# === ANALYSIS ON PURE SCRIPTS ===
full_text = '\n'.join(t for _, t in pure_scripts)
sentences = sent_tokenize(full_text)
words_raw = word_tokenize(full_text.lower())
words_alpha = [w for w in words_raw if w.isalpha()]
word_freq = Counter(words_alpha)
total_words = len(words_alpha)
unique_words = len(word_freq)
content_words = [w for w in words_alpha if w not in stop_words]
content_freq = Counter(content_words)
full_lower = full_text.lower()

print(f"\n=== PURE SCRIPTS ANALYSIS ===")
print(f"Sentences: {len(sentences)}")
print(f"Words (alpha): {total_words}")
print(f"Unique words: {unique_words}")

# --- 1. SYNTACTIC STRUCTURE ---
print(f"\n{'='*60}")
print(f"1. SYNTACTIC STRUCTURE")
print(f"{'='*60}")

IMPERATIVE_VERBS = set([
    'let', 'relax', 'close', 'feel', 'notice', 'allow', 'imagine', 'breathe',
    'focus', 'listen', 'open', 'think', 'look', 'take', 'go', 'drift', 'sleep',
    'rest', 'sink', 'drop', 'float', 'begin', 'continue', 'repeat', 'picture',
    'visualize', 'remember', 'enjoy', 'experience', 'try', 'keep',
    'stop', 'see', 'hear', 'sense', 'become', 'move', 'place',
    'hold', 'release', 'count', 'say', 'tell', 'make', 'give', 'find', 'bring',
    'accept', 'embrace', 'surrender', 'pay', 'concentrate', 'sit', 'lie',
    'press', 'lift', 'lower', 'turn', 'shift', 'send', 'draw', 'pull', 'push',
    'step', 'walk', 'enter', 'leave', 'come', 'return', 'watch', 'observe'
])

PERMISSIVE_WORDS = set(['can', 'may', 'might', 'could', 'perhaps', 'maybe',
                         'wonder', 'wondering', 'possibly', 'probably'])

def analyze_sentences(sents):
    res = {'total': len(sents), 'imperatives': 0, 'permissive': 0,
           'you_initial': 0, 'questions': 0, 'declarative': 0,
           'imp_verbs': Counter(), 'perm_verbs': Counter()}
    for s in sents:
        s = s.strip()
        if not s or len(s) < 3:
            continue
        sl = s.lower()
        ws = sl.split()
        if len(ws) < 2:
            continue

        if s.endswith('?'):
            res['questions'] += 1
            continue

        # You-initial (covert directive)
        if ws[0] in ('you', "you're", "you'll", "your"):
            res['you_initial'] += 1
            continue

        # Check for permissive markers in first ~30 chars
        first_chunk = sl[:40]
        is_perm = False
        for pm in PERMISSIVE_WORDS:
            if pm in first_chunk.split()[:5]:
                res['permissive'] += 1
                is_perm = True
                break
        if not is_perm and re.match(r'.*?\byou (can|may|might|could)\b', first_chunk):
            res['permissive'] += 1
            is_perm = True
        if is_perm:
            continue

        # Check for imperative (verb-initial after stripping connectors)
        check = ws[0]
        skip = {'and', 'but', 'so', 'then', 'now', 'just', 'simply', 'ok', 'okay', 'alright', 'well'}
        idx = 0
        while check in skip and idx < min(3, len(ws)-1):
            idx += 1
            check = ws[idx]

        if check in IMPERATIVE_VERBS:
            res['imperatives'] += 1
            res['imp_verbs'][check] += 1
            continue

        res['declarative'] += 1

    return res

r = analyze_sentences(sentences)
n = r['total']
print(f"\nSentence-Type Distribution (n={n})")
print(f"{'Type':<45} {'Count':>6} {'%':>7}")
print(f"{'-'*60}")
for label, key in [('Verb-initial imperatives', 'imperatives'),
                    ('Permissive framing', 'permissive'),
                    ('You-initial declaratives (covert directives)', 'you_initial'),
                    ('Questions', 'questions'),
                    ('Other declarative', 'declarative')]:
    print(f"{label:<45} {r[key]:>6} {100*r[key]/n:>6.1f}%")

ratio = r['imperatives'] / max(r['permissive'], 1)
print(f"\nImperative-to-Permissive ratio: {ratio:.2f}:1")
true_dir = r['imperatives'] + r['you_initial']
print(f"True directive rate (imp + you-init): {true_dir} ({100*true_dir/n:.1f}%)")

print(f"\nTop 20 imperative verbs:")
for v, c in r['imp_verbs'].most_common(20):
    print(f"  {v}: {c}")

# Per subcategory
for label, txts in [('INDUCTION', induction_texts), ('THERAPEUTIC', therapeutic_texts)]:
    cat_sents = []
    for _, t in txts:
        cat_sents.extend(sent_tokenize(t))
    cr = analyze_sentences(cat_sents)
    cn = cr['total']
    cratio = cr['imperatives'] / max(cr['permissive'], 1)
    cdir = cr['imperatives'] + cr['you_initial']
    print(f"\n  [{label}] n={cn}")
    print(f"    Imperatives: {cr['imperatives']} ({100*cr['imperatives']/max(cn,1):.1f}%)")
    print(f"    Permissive: {cr['permissive']} ({100*cr['permissive']/max(cn,1):.1f}%)")
    print(f"    You-initial: {cr['you_initial']} ({100*cr['you_initial']/max(cn,1):.1f}%)")
    print(f"    Questions: {cr['questions']} ({100*cr['questions']/max(cn,1):.1f}%)")
    print(f"    Imp:Perm = {cratio:.2f}:1")
    print(f"    True directive: {cdir} ({100*cdir/max(cn,1):.1f}%)")
    print(f"    Top verbs: {cr['imp_verbs'].most_common(10)}")

# --- 2. TRANCE GRAMMAR ---
print(f"\n{'='*60}")
print(f"2. TRANCE GRAMMAR (Milton Model)")
print(f"{'='*60}")

# Nominalizations
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
for nm in NOMS:
    c = word_freq.get(nm, 0)
    if c > 0:
        nom_counts[nm] = c

total_noms = sum(nom_counts.values())
print(f"\nNominalizations: {total_noms} tokens, {len(nom_counts)} types")
print(f"Per 1000 words: {1000*total_noms/total_words:.2f}")
for nm, c in nom_counts.most_common(20):
    print(f"  {nm}: {c}")

# Unspecified verbs
UNSPEC = ['feel', 'sense', 'notice', 'experience', 'know', 'realize',
          'understand', 'become', 'change', 'grow', 'develop', 'move',
          'happen', 'drift', 'float', 'flow', 'spread', 'go', 'come',
          'let', 'allow', 'find', 'discover', 'learn']
unspec_counts = Counter()
for v in UNSPEC:
    c = word_freq.get(v, 0)
    if c > 0:
        unspec_counts[v] = c
print(f"\nUnspecified verbs: {sum(unspec_counts.values())} tokens")
for v, c in unspec_counts.most_common(15):
    print(f"  {v}: {c}")

# Embedded commands
print(f"\nEmbedded command patterns:")
emb_pats = [
    (r'you can (?:just |simply )?(\w+)', 'you can [V]'),
    (r'i want you to (\w+)', 'I want you to [V]'),
    (r'you might (?:just |simply )?(\w+)', 'you might [V]'),
    (r'allow yourself to (\w+)', 'allow yourself to [V]'),
    (r'perhaps you (?:can |could |will |might )?(\w+)', 'perhaps you [V]'),
    (r"don't (?:try|need|have) to (\w+)", "don't [try/need] to [V]"),
    (r'you don\'?t (?:need|have) to (\w+)', "you don't need to [V]"),
    (r'you find yourself (\w+)', 'you find yourself [V]'),
    (r'i wonder if you', 'I wonder if you...'),
    (r"there'?s? no need to (\w+)", "no need to [V]"),
    (r"it'?s? (?:ok|okay|alright|fine|easy|possible|natural|normal) to (\w+)", "it's [ok] to [V]"),
    (r'you (?:will|are going to) (\w+)', 'you will [V]'),
]
total_emb = 0
emb_details = {}
for pat, label in emb_pats:
    matches = re.findall(pat, full_lower)
    c = len(matches)
    total_emb += c
    if c > 0:
        emb_details[label] = (c, Counter(matches).most_common(5))
        print(f"  {label}: {c}")
        if isinstance(matches[0], str):
            top = Counter(matches).most_common(3)
            for verb, vc in top:
                print(f"    → {verb}: {vc}")

print(f"Total embedded: {total_emb}")
print(f"Per 1000 words: {1000*total_emb/total_words:.2f}")

# Pacing/Leading
print(f"\nPacing/Leading phrases:")
pacing_pats = [
    ('as you', r'\bas you\b'), ('when you', r'\bwhen you\b'),
    ('while you', r'\bwhile you\b'), ('the more you', r'\bthe more you\b'),
    ('with each', r'\bwith each\b'), ('with every', r'\bwith every\b'),
    ('each time', r'\beach time\b'), ('and now', r'\band now\b'),
    ('deeper and deeper', r'\bdeeper and deeper\b'),
    ('more and more', r'\bmore and more\b'),
]
total_pacing = 0
for label, pat in pacing_pats:
    c = len(re.findall(pat, full_lower))
    total_pacing += c
    print(f"  '{label}': {c}")
print(f"Total pacing phrases: {total_pacing}")
print(f"Per 1000 words: {1000*total_pacing/total_words:.2f}")

# Full pacing→leading (as you X, you Y)
pl_full = re.findall(
    r'\b(as you|while you|when you|the more you)[^.]{3,80}(you (?:will|can|begin|feel|notice|find|become|are|may|might|go|\'ll|\'re))\b',
    full_lower
)
print(f"Complete pacing→leading transitions: {len(pl_full)}")

# Presuppositions
print(f"\nPresupposition markers:")
presup_pats = [
    ('already', r'\balready\b'), ('beginning to', r'\bbeginning to\b'),
    ('continue to', r'\bcontinue to\b'), ('even more', r'\beven more\b'),
    ('deeper', r'\bdeeper\b'), ('further', r'\bfurther\b'),
    ('still', r'\bstill\b'), ('notice that', r'\bnotice that\b'),
    ('realize that', r'\brealize that\b'),
]
total_presup = 0
for label, pat in presup_pats:
    c = len(re.findall(pat, full_lower))
    total_presup += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total: {total_presup}, per 1000 words: {1000*total_presup/total_words:.2f}")

# --- 3. CADENCE AND REPETITION ---
print(f"\n{'='*60}")
print(f"3. CADENCE AND REPETITION")
print(f"{'='*60}")

# Lexical density
ld = len(content_words) / total_words
print(f"\nLexical density (all pure scripts): {ld:.4f} ({ld*100:.2f}%)")

# Per category
for label, txts in [('induction', induction_texts), ('therapeutic', therapeutic_texts)]:
    cat_ws = [w.lower() for _, t in txts for w in word_tokenize(t) if w.isalpha()]
    cat_cw = [w for w in cat_ws if w not in stop_words]
    cat_ld = len(cat_cw) / max(len(cat_ws), 1)
    print(f"  [{label}]: {cat_ld:.4f} ({cat_ld*100:.2f}%)")

# TTR
ttr = unique_words / total_words
print(f"\nType-Token Ratio: {ttr:.4f}")

# MATTR
window = 500
mattr_vals = []
for i in range(0, len(words_alpha) - window, window // 4):
    chunk = words_alpha[i:i+window]
    mattr_vals.append(len(set(chunk)) / window)
mattr = sum(mattr_vals) / len(mattr_vals)
print(f"MATTR (window=500): {mattr:.4f}")

# Repetitive structures
print(f"\n'X and X' intensifiers:")
x_and_x = Counter(re.findall(r'\b(\w+) and \1\b', full_lower))
for w, c in x_and_x.most_common(15):
    print(f"  '{w} and {w}': {c}")

print(f"\n'more and more X':")
mam = Counter(re.findall(r'more and more (\w+)', full_lower))
for w, c in mam.most_common(10):
    print(f"  'more and more {w}': {c}")

# Top bigrams (content)
bigrams = list(zip(words_alpha[:-1], words_alpha[1:]))
bg_freq = Counter(bigrams)
bg_content = {bg: c for bg, c in bg_freq.items()
              if bg[0] not in stop_words or bg[1] not in stop_words}
print(f"\nTop 25 content bigrams:")
for bg, c in Counter(bg_content).most_common(25):
    print(f"  '{bg[0]} {bg[1]}': {c}")

# Top trigrams (content)
trigrams = list(zip(words_alpha[:-2], words_alpha[1:-1], words_alpha[2:]))
tg_freq = Counter(trigrams)
tg_content = {tg: c for tg, c in tg_freq.items()
              if sum(1 for w in tg if w not in stop_words) >= 2}
print(f"\nTop 20 content trigrams:")
for tg, c in Counter(tg_content).most_common(20):
    print(f"  '{tg[0]} {tg[1]} {tg[2]}': {c}")

# Sentence length
sent_lens = [len(word_tokenize(s)) for s in sentences]
avg_sl = sum(sent_lens)/len(sent_lens)
med_sl = sorted(sent_lens)[len(sent_lens)//2]
print(f"\nSentence length — Mean: {avg_sl:.1f}, Median: {med_sl}")
buckets = [(1,5), (6,10), (11,15), (16,20), (21,30), (31,50), (51,999)]
for lo, hi in buckets:
    count = sum(1 for l in sent_lens if lo <= l <= hi)
    print(f"  {lo}-{hi}: {count} ({100*count/len(sent_lens):.1f}%)")

# --- 4. MASTER VERBS ---
print(f"\n{'='*60}")
print(f"4. MASTER VERBS")
print(f"{'='*60}")

VERBS = ['feel', 'let', 'relax', 'allow', 'imagine', 'notice', 'close', 'open',
         'breathe', 'sleep', 'drift', 'float', 'sink', 'go', 'come', 'become',
         'find', 'take', 'think', 'know', 'see', 'hear', 'sense', 'focus',
         'keep', 'begin', 'continue', 'move', 'release', 'accept', 'enjoy',
         'experience', 'remember', 'visualize', 'want', 'try', 'make', 'give',
         'look', 'watch', 'listen', 'rest', 'drop', 'flow', 'spread', 'grow',
         'change', 'count', 'say', 'tell', 'need', 'wish', 'hope', 'believe',
         'trust', 'wonder', 'realize', 'understand', 'discover', 'learn', 'deepen']

verb_counts = Counter()
for v in VERBS:
    c = word_freq.get(v, 0)
    if c > 0:
        verb_counts[v] = c

print(f"\nVerb frequency (top 30):")
for v, c in verb_counts.most_common(30):
    print(f"  {v}: {c} ({1000*c/total_words:.2f}/1k words)")

# Let analysis
print(f"\n--- 'LET' deep analysis ---")
let_count = word_freq.get('let', 0)
print(f"Total 'let' tokens: {let_count}")
print(f"Per 1000 words: {1000*let_count/total_words:.2f}")

# let + what
print(f"\n'let' + object patterns:")
let_obj = Counter(re.findall(r'\blet (go|yourself|your \w+|it|them|me|us|that|the \w+|this|every \w+|all)', full_lower))
for p, c in let_obj.most_common(20):
    print(f"  'let {p}': {c}")

# let collocations (2 words after)
print(f"\n'let' + next 2 words:")
let_next = Counter(re.findall(r'\blet (\w+ \w+)', full_lower))
for p, c in let_next.most_common(20):
    print(f"  'let {p}': {c}")

# Verb neighborhood of 'let'
print(f"\nVerb neighbors of 'let' (within 8 words):")
let_nbrs = Counter()
for i, w in enumerate(words_alpha):
    if w == 'let':
        window = words_alpha[max(0,i-8):i] + words_alpha[i+1:i+9]
        for ww in window:
            if ww in set(VERBS) and ww != 'let':
                let_nbrs[ww] += 1
for v, c in let_nbrs.most_common(15):
    print(f"  {v}: {c}")

# 'allow' analysis
allow_count = word_freq.get('allow', 0)
print(f"\n'allow' tokens: {allow_count}")
allow_next = Counter(re.findall(r'\ballow (\w+ \w+)', full_lower))
for p, c in allow_next.most_common(10):
    print(f"  'allow {p}': {c}")

# --- 5. ADDITIONAL ---
print(f"\n{'='*60}")
print(f"5. ADDITIONAL METRICS")
print(f"{'='*60}")

# Pronouns
you_forms = word_freq.get('you', 0) + word_freq.get('your', 0)
i_forms = word_freq.get('i', 0) + word_freq.get('my', 0)
print(f"\nYou-forms: {you_forms} ({1000*you_forms/total_words:.1f}/1k)")
print(f"  'you': {word_freq.get('you', 0)}")
print(f"  'your': {word_freq.get('your', 0)}")
print(f"I-forms: {i_forms} ({1000*i_forms/total_words:.1f}/1k)")
print(f"You:I ratio: {you_forms/max(i_forms,1):.2f}:1")

# Sensory channels
VIS = ['see', 'look', 'watch', 'picture', 'visualize', 'imagine', 'image', 'color', 'light', 'bright', 'dark', 'glow', 'scene', 'view']
AUD = ['hear', 'listen', 'sound', 'voice', 'tone', 'quiet', 'silence', 'whisper', 'echo']
KIN = ['feel', 'touch', 'warm', 'cool', 'heavy', 'light', 'soft', 'smooth', 'pressure', 'sensation', 'tingling', 'numbness', 'comfortable', 'relaxed', 'tension', 'tight', 'loose']
v = sum(word_freq.get(w, 0) for w in VIS)
a = sum(word_freq.get(w, 0) for w in AUD)
k = sum(word_freq.get(w, 0) for w in KIN)
t = v + a + k
print(f"\nSensory channels:")
print(f"  Visual: {v} ({100*v/t:.1f}%)")
print(f"  Auditory: {a} ({100*a/t:.1f}%)")
print(f"  Kinesthetic: {k} ({100*k/t:.1f}%)")

# Negation
negs = [("don't", r"\bdon't\b"), ('not', r'\bnot\b'), ('no', r'\bno\b'),
        ('never', r'\bnever\b'), ('nothing', r'\bnothing\b')]
total_neg = 0
print(f"\nNegation:")
for label, pat in negs:
    c = len(re.findall(pat, full_lower))
    total_neg += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total: {total_neg}, per 1000 words: {1000*total_neg/total_words:.2f}")

# Temporal/progressive
print(f"\nTemporal markers:")
temps = ['now', 'already', 'beginning', 'soon', 'continue', 'continuing',
         'still', 'slowly', 'gently', 'deeply', 'gradually', 'further']
for t in temps:
    c = word_freq.get(t, 0)
    if c > 0:
        print(f"  {t}: {c}")

print(f"\n{'='*60}")
print(f"TOP 50 CONTENT WORDS")
print(f"{'='*60}")
for w, c in content_freq.most_common(50):
    print(f"  {w}: {c}")

print("\n=== ANALYSIS COMPLETE ===")
