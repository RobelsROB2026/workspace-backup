#!/usr/bin/env python3
"""
Computational Signature Analysis of Hypnotic Induction Language
Full corpus: 166 scripts, ~373k words
"""

import os, re, sys, json, math
from collections import Counter, defaultdict
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag
from nltk.corpus import stopwords

SCRIPT_DIR = Path(__file__).parent
CORPUS_FILES = sorted(SCRIPT_DIR.glob("*.txt"))

# --- Categorization ---
# Heuristic: files with "induction" or "method" in name are induction scripts
# Files with therapeutic/condition names are therapeutic scripts
INDUCTION_KEYWORDS = ['induction', 'method', 'deepening', 'deepener', 'relaxation_technique',
                       'body_conditioning', 'progressive_relaxation', 'arm_levitation',
                       'eye_fixation', 'countdown', 'self-hypnosis', 'self_hypnosis',
                       'trance', 'hypnotize', 'awareness_induction']
THERAPY_KEYWORDS = ['anxiety', 'phobia', 'smoking', 'weight', 'pain', 'anger', 'stress',
                    'confidence', 'sleep', 'insomnia', 'depression', 'fear', 'habit',
                    'addiction', 'bereavement', 'grief', 'trauma', 'healing', 'therapy',
                    'blushing', 'baldness', 'nail_biting', 'stuttering', 'jealousy',
                    'motivation', 'self_esteem', 'panic', 'ocd', 'ptsd', 'exam',
                    'public_speaking', 'impotence', 'fertility', 'ibs', 'migraine',
                    'breast', 'abandoned', 'reward', 'business', 'sales', 'sport',
                    'golf', 'learning', 'memory', 'focus', 'creativity']

def categorize(fname):
    fn = fname.lower()
    for kw in INDUCTION_KEYWORDS:
        if kw in fn:
            return 'induction'
    for kw in THERAPY_KEYWORDS:
        if kw in fn:
            return 'therapeutic'
    return 'uncategorized'

# --- Load corpus ---
print("Loading corpus...")
all_text = []
texts_by_cat = defaultdict(list)
file_stats = []

for f in CORPUS_FILES:
    if f.name == os.path.basename(__file__):
        continue
    text = f.read_text(encoding='utf-8', errors='ignore')
    cat = categorize(f.name)
    all_text.append(text)
    texts_by_cat[cat].append(text)
    file_stats.append({'name': f.name, 'category': cat, 'words': len(text.split())})

full_text = '\n'.join(all_text)
print(f"Loaded {len(all_text)} files, {len(full_text.split())} words")
for cat, txts in texts_by_cat.items():
    wc = sum(len(t.split()) for t in txts)
    print(f"  {cat}: {len(txts)} files, {wc} words")

# --- Tokenization ---
print("Tokenizing...")
sentences = sent_tokenize(full_text)
words = word_tokenize(full_text.lower())
words_alpha = [w for w in words if w.isalpha()]
word_freq = Counter(words_alpha)
total_words = len(words_alpha)
unique_words = len(word_freq)
stop_words = set(stopwords.words('english'))
content_words = [w for w in words_alpha if w not in stop_words]
content_freq = Counter(content_words)

print(f"Sentences: {len(sentences)}")
print(f"Words (alpha): {total_words}, Unique: {unique_words}")

# --- 1. SYNTACTIC STRUCTURE: Imperatives vs. Permissive ---
print("\n=== 1. SYNTACTIC STRUCTURE ===")

# Imperative detection: sentence starts with base verb
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

PACING_LEADING = re.compile(
    r'\b(as you|while you|when you|the more you|each time you|every time you|'
    r'and as you|and the more|with each|with every)\b.*\b(you will|you can|'
    r'you begin|you feel|you notice|you find|you become|you are|you\'ll|'
    r'you may|you might|the more)\b', re.IGNORECASE
)

# Per-category analysis
def analyze_syntax(sents):
    imperatives = 0
    permissive = 0
    you_initial = 0
    questions = 0
    pacing_leading = 0
    imperative_verbs = Counter()

    for s in sents:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        s_lower = s_stripped.lower()
        first_words = s_lower.split()[:3]

        if s_stripped.endswith('?'):
            questions += 1

        # Pacing/leading
        if PACING_LEADING.search(s_lower):
            pacing_leading += 1

        # You-initial
        if first_words and first_words[0] in ('you', "you're", "you'll", "your"):
            you_initial += 1
            continue

        # Permissive check
        found_perm = False
        for pm in PERMISSIVE_MARKERS:
            if pm in first_words[:4] or f'you {pm}' in s_lower[:30]:
                permissive += 1
                found_perm = True
                break
        if found_perm:
            continue

        # Imperative check
        if first_words:
            # Skip numbers, articles, pronouns
            check_word = first_words[0]
            if check_word in ('and', 'but', 'so', 'then', 'now'):
                if len(first_words) > 1:
                    check_word = first_words[1]
            if check_word in ('just', 'simply'):
                if len(first_words) > 1:
                    check_word = first_words[1]

            if check_word in IMPERATIVE_VERBS:
                imperatives += 1
                imperative_verbs[check_word] += 1

    return {
        'total': len(sents),
        'imperatives': imperatives,
        'permissive': permissive,
        'you_initial': you_initial,
        'questions': questions,
        'pacing_leading': pacing_leading,
        'imperative_verbs': imperative_verbs
    }

# Full corpus
full_syntax = analyze_syntax(sentences)
print(f"Total sentences: {full_syntax['total']}")
print(f"Imperatives: {full_syntax['imperatives']} ({100*full_syntax['imperatives']/full_syntax['total']:.1f}%)")
print(f"Permissive: {full_syntax['permissive']} ({100*full_syntax['permissive']/full_syntax['total']:.1f}%)")
print(f"You-initial: {full_syntax['you_initial']} ({100*full_syntax['you_initial']/full_syntax['total']:.1f}%)")
print(f"Questions: {full_syntax['questions']} ({100*full_syntax['questions']/full_syntax['total']:.1f}%)")
print(f"Pacing/Leading: {full_syntax['pacing_leading']} ({100*full_syntax['pacing_leading']/full_syntax['total']:.1f}%)")
imp_to_perm = full_syntax['imperatives'] / max(full_syntax['permissive'], 1)
print(f"Imperative-to-Permissive ratio: {imp_to_perm:.2f}:1")
print(f"\nTop imperative verbs: {full_syntax['imperative_verbs'].most_common(20)}")

# Per-category
cat_syntax = {}
for cat, txts in texts_by_cat.items():
    cat_sents = []
    for t in txts:
        cat_sents.extend(sent_tokenize(t))
    cat_syntax[cat] = analyze_syntax(cat_sents)
    r = cat_syntax[cat]
    ratio = r['imperatives'] / max(r['permissive'], 1)
    print(f"\n  [{cat}] sents={r['total']}, imp={r['imperatives']} ({100*r['imperatives']/max(r['total'],1):.1f}%), "
          f"perm={r['permissive']} ({100*r['permissive']/max(r['total'],1):.1f}%), "
          f"you_init={r['you_initial']} ({100*r['you_initial']/max(r['total'],1):.1f}%), "
          f"ratio={ratio:.2f}:1, pacing_leading={r['pacing_leading']}")

# --- 2. TRANCE GRAMMAR (Milton Model) ---
print("\n\n=== 2. TRANCE GRAMMAR ===")

# 2.1 Nominalizations
NOMINALIZATIONS = [
    'relaxation', 'feeling', 'sensation', 'experience', 'awareness', 'comfort',
    'calmness', 'drowsiness', 'peacefulness', 'contentment', 'heaviness',
    'lightness', 'warmth', 'coolness', 'numbness', 'tingling', 'floating',
    'drifting', 'sinking', 'deepening', 'letting', 'breathing', 'healing',
    'understanding', 'knowledge', 'wisdom', 'confidence', 'strength',
    'tranquility', 'serenity', 'stillness', 'quietness', 'silence',
    'imagination', 'visualization', 'concentration', 'attention', 'focus',
    'consciousness', 'unconsciousness', 'subconscious', 'transformation',
    'change', 'growth', 'movement', 'pleasure', 'happiness', 'joy',
    'peace', 'calm', 'ease', 'rest', 'sleep', 'dream', 'trance',
    'hypnosis', 'suggestion', 'acceptance', 'permission', 'freedom',
    'release', 'relief', 'resolution', 'realization', 'discovery',
    'connection', 'harmony', 'balance', 'security', 'safety', 'protection',
    'ability', 'possibility', 'potential', 'power', 'energy', 'vibration'
]
# Only count actual nominalizations (process -> noun)
TRUE_NOMINALIZATIONS = [
    'relaxation', 'sensation', 'awareness', 'comfort', 'calmness', 'drowsiness',
    'peacefulness', 'contentment', 'heaviness', 'lightness', 'warmth', 'coolness',
    'numbness', 'tingling', 'deepening', 'healing', 'understanding', 'knowledge',
    'confidence', 'strength', 'tranquility', 'serenity', 'stillness', 'quietness',
    'imagination', 'visualization', 'concentration', 'attention', 'consciousness',
    'transformation', 'movement', 'pleasure', 'happiness', 'acceptance',
    'permission', 'freedom', 'release', 'relief', 'resolution', 'realization',
    'discovery', 'connection', 'harmony', 'balance', 'security', 'safety',
    'protection', 'ability', 'possibility', 'potential', 'experience', 'feeling'
]

nom_counts = Counter()
for nom in TRUE_NOMINALIZATIONS:
    c = word_freq.get(nom, 0)
    if c > 0:
        nom_counts[nom] = c

print("Nominalizations (top 25):")
total_noms = sum(nom_counts.values())
for nom, c in nom_counts.most_common(25):
    print(f"  {nom}: {c}")
print(f"Total nominalization tokens: {total_noms}")
print(f"Nominalization types: {len(nom_counts)}")
print(f"Nominalizations per 1000 words: {1000*total_noms/total_words:.2f}")

# 2.2 Unspecified verbs
UNSPECIFIED_VERBS = ['feel', 'sense', 'notice', 'experience', 'know', 'realize',
                     'understand', 'become', 'change', 'grow', 'develop', 'move',
                     'happen', 'occur', 'drift', 'float', 'flow', 'spread',
                     'go', 'come', 'let', 'allow', 'find', 'discover', 'learn']
print("\nUnspecified verbs (top 20):")
unspec_counts = Counter()
for v in UNSPECIFIED_VERBS:
    c = word_freq.get(v, 0)
    if c > 0:
        unspec_counts[v] = c
for v, c in unspec_counts.most_common(20):
    print(f"  {v}: {c}")
print(f"Total unspecified verb tokens: {sum(unspec_counts.values())}")

# 2.3 Embedded commands - patterns like "you can [verb]", "I wonder if you [verb]"
EMBED_PATTERNS = [
    (r'you can (?:just |simply )?(\w+)', 'you can [verb]'),
    (r'i wonder if you (?:can |could |have |will |might )?(\w+)', 'I wonder if...'),
    (r'you might (?:just |simply )?(\w+)', 'you might [verb]'),
    (r'i want you to (\w+)', 'I want you to [verb]'),
    (r'allow yourself to (\w+)', 'allow yourself to [verb]'),
    (r'perhaps you (?:can |could |will |might )?(\w+)', 'perhaps you...'),
    (r'it\'?s? (?:ok|okay|alright|fine|possible|easy) to (\w+)', "it's OK to [verb]"),
    (r"don't (?:try|need|have) to (\w+)", "don't try to [verb]"),
    (r'there\'?s? no need to (\w+)', "no need to [verb]"),
    (r'you don\'?t (?:need|have) to (\w+)', "you don't need to [verb]"),
    (r'you find yourself (\w+ing)', 'you find yourself [verb]ing'),
]

embed_counts = Counter()
embed_examples = defaultdict(list)
full_lower = full_text.lower()
for pat, label in EMBED_PATTERNS:
    matches = re.findall(pat, full_lower)
    embed_counts[label] = len(matches)
    # Get example sentences
    for m in re.finditer(pat, full_lower):
        start = max(0, m.start() - 20)
        end = min(len(full_lower), m.end() + 40)
        if len(embed_examples[label]) < 3:
            embed_examples[label].append(full_lower[start:end].replace('\n', ' ').strip())

print("\nEmbedded command patterns:")
total_embedded = sum(embed_counts.values())
for label, c in embed_counts.most_common():
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total embedded commands: {total_embedded}")
print(f"Embedded commands per 1000 words: {1000*total_embedded/total_words:.2f}")

# 2.4 Pacing/Leading transitions
# Already counted above
print(f"\nPacing/Leading transitions: {full_syntax['pacing_leading']}")
print(f"Per 1000 sentences: {1000*full_syntax['pacing_leading']/len(sentences):.1f}")

# Additional pacing patterns
PACING_PATTERNS = [
    (r'as you\b', 'as you'),
    (r'while you\b', 'while you'),
    (r'when you\b', 'when you'),
    (r'the more you\b', 'the more you'),
    (r'each time\b', 'each time'),
    (r'every time\b', 'every time'),
    (r'with each\b', 'with each'),
    (r'with every\b', 'with every'),
    (r'and as\b', 'and as'),
    (r'and now\b', 'and now'),
    (r'and the\b', 'and the'),
    (r'deeper and deeper\b', 'deeper and deeper'),
    (r'more and more\b', 'more and more'),
]
print("\nPacing/Leading phrase frequencies:")
for pat, label in PACING_PATTERNS:
    c = len(re.findall(pat, full_lower))
    print(f"  '{label}': {c}")

# --- 3. CADENCE AND REPETITION ---
print("\n\n=== 3. CADENCE AND REPETITION ===")

# 3.1 Lexical density = content words / total words
lexical_density = len(content_words) / total_words
print(f"Lexical density (corpus): {lexical_density:.4f} ({lexical_density*100:.2f}%)")

# Per-category lexical density
for cat, txts in texts_by_cat.items():
    cat_words = []
    for t in txts:
        ws = [w.lower() for w in word_tokenize(t) if w.isalpha()]
        cat_words.extend(ws)
    cat_content = [w for w in cat_words if w not in stop_words]
    ld = len(cat_content) / max(len(cat_words), 1)
    print(f"  [{cat}] lexical density: {ld:.4f} ({ld*100:.2f}%)")

# 3.2 Type-Token Ratio
ttr = unique_words / total_words
print(f"\nType-Token Ratio (TTR): {ttr:.4f}")
# Moving average TTR (MATTR) with window of 1000
window = 1000
mattr_values = []
for i in range(0, len(words_alpha) - window, window // 2):
    chunk = words_alpha[i:i+window]
    mattr_values.append(len(set(chunk)) / window)
mattr = sum(mattr_values) / len(mattr_values) if mattr_values else 0
print(f"MATTR (window=1000): {mattr:.4f}")

# 3.3 Repetitive loops - repeated bigrams and trigrams
print("\nTop 30 bigrams (excluding stopword-only):")
bigrams = list(zip(words_alpha[:-1], words_alpha[1:]))
bigram_freq = Counter(bigrams)
# Filter: at least one content word
bigram_content = {bg: c for bg, c in bigram_freq.items()
                  if bg[0] not in stop_words or bg[1] not in stop_words}
for bg, c in Counter(bigram_content).most_common(30):
    print(f"  '{bg[0]} {bg[1]}': {c}")

print("\nTop 20 trigrams (excluding stopword-only):")
trigrams = list(zip(words_alpha[:-2], words_alpha[1:-1], words_alpha[2:]))
trigram_freq = Counter(trigrams)
trigram_content = {tg: c for tg, c in trigram_freq.items()
                   if any(w not in stop_words for w in tg)}
for tg, c in Counter(trigram_content).most_common(20):
    print(f"  '{tg[0]} {tg[1]} {tg[2]}': {c}")

# 3.4 Repetition structures: "X and X" patterns
print("\nRepetitive intensifiers ('X and X' patterns):")
x_and_x = re.findall(r'\b(\w+) and \1\b', full_lower)
x_and_x_freq = Counter(x_and_x)
for w, c in x_and_x_freq.most_common(15):
    print(f"  '{w} and {w}': {c}")

# "more and more X" pattern
more_and_more = re.findall(r'more and more (\w+)', full_lower)
print(f"\n'more and more X' (n={len(more_and_more)}):")
for w, c in Counter(more_and_more).most_common(10):
    print(f"  'more and more {w}': {c}")

# --- 4. MASTER VERBS ---
print("\n\n=== 4. MASTER VERBS ===")

# All verbs by POS tag (sample for speed — tag 20k words)
print("POS tagging sample (20k words)...")
sample_words = words_alpha[:20000]
sample_tagged = pos_tag(sample_words)
verb_tags = {'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}
tagged_verbs = Counter()
for word, tag in sample_tagged:
    if tag in verb_tags:
        tagged_verbs[word] += 1

print("Top 40 verbs by POS tag (sample):")
for v, c in tagged_verbs.most_common(40):
    print(f"  {v}: {c}")

# Full corpus verb frequency (using known verb list)
HYPNOTIC_VERBS = [
    'let', 'relax', 'feel', 'allow', 'imagine', 'notice', 'close', 'open',
    'breathe', 'sleep', 'drift', 'float', 'sink', 'drop', 'go', 'come',
    'become', 'find', 'take', 'give', 'make', 'think', 'know', 'see',
    'hear', 'sense', 'watch', 'look', 'listen', 'focus', 'concentrate',
    'rest', 'begin', 'continue', 'keep', 'move', 'lift', 'rise', 'fall',
    'flow', 'spread', 'grow', 'release', 'accept', 'enjoy', 'experience',
    'remember', 'forget', 'learn', 'change', 'try', 'want', 'need',
    'wish', 'hope', 'believe', 'trust', 'surrender', 'embrace', 'hold',
    'picture', 'visualize', 'recall', 'suggest', 'deepen', 'awaken',
    'wake', 'return', 'emerge', 'count', 'repeat', 'say', 'tell',
    'speak', 'ask', 'wonder', 'realize', 'discover', 'understand'
]

print("\nFull corpus verb frequencies (top 30):")
verb_full = Counter()
for v in HYPNOTIC_VERBS:
    c = word_freq.get(v, 0)
    if c > 0:
        verb_full[v] = c
for v, c in verb_full.most_common(30):
    pct = 100 * c / total_words
    print(f"  {v}: {c} ({pct:.3f}%)")

# 'let' collocations
print("\n'let' collocations (what follows 'let'):")
let_follows = re.findall(r'\blet (\w+ \w+)', full_lower)
let_follows_freq = Counter(let_follows)
for phrase, c in let_follows_freq.most_common(20):
    print(f"  'let {phrase}': {c}")

# 'let' constructions
print("\n'let' full patterns:")
let_patterns = re.findall(r'\blet (your \w+|yourself|go|it|me|us|them|that|the \w+|this)', full_lower)
let_pat_freq = Counter(let_patterns)
for p, c in let_pat_freq.most_common(15):
    print(f"  'let {p}': {c}")

# Verb clustering — which verbs co-occur within 10 words of 'let'
print("\nVerbs within 10 words of 'let':")
let_neighborhood = Counter()
words_list = words_alpha
for i, w in enumerate(words_list):
    if w == 'let':
        window_words = words_list[max(0,i-10):i] + words_list[i+1:i+11]
        for ww in window_words:
            if ww in set(HYPNOTIC_VERBS) and ww != 'let':
                let_neighborhood[ww] += 1
for v, c in let_neighborhood.most_common(15):
    print(f"  {v}: {c}")

# --- 5. ADDITIONAL METRICS ---
print("\n\n=== 5. ADDITIONAL METRICS ===")

# Sentence length distribution
sent_lengths = [len(word_tokenize(s)) for s in sentences]
avg_sent_len = sum(sent_lengths) / len(sent_lengths)
median_sent_len = sorted(sent_lengths)[len(sent_lengths)//2]
print(f"Avg sentence length: {avg_sent_len:.1f} words")
print(f"Median sentence length: {median_sent_len} words")
print(f"Max sentence length: {max(sent_lengths)} words")
print(f"Min sentence length: {min(sent_lengths)} words")

# Distribution buckets
buckets = [(1,5), (6,10), (11,15), (16,20), (21,30), (31,50), (51,100), (101,999)]
print("Sentence length distribution:")
for lo, hi in buckets:
    count = sum(1 for l in sent_lengths if lo <= l <= hi)
    pct = 100 * count / len(sent_lengths)
    print(f"  {lo}-{hi} words: {count} ({pct:.1f}%)")

# Pronoun analysis
pronouns = {
    'you': word_freq.get('you', 0),
    'your': word_freq.get('your', 0),
    "you're": full_lower.count("you're"),
    "you'll": full_lower.count("you'll"),
    'i': word_freq.get('i', 0),
    'my': word_freq.get('my', 0),
    'we': word_freq.get('we', 0),
    'they': word_freq.get('they', 0),
    'it': word_freq.get('it', 0),
}
print("\nPronoun frequencies:")
for p, c in sorted(pronouns.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}")
you_total = pronouns['you'] + pronouns['your'] + pronouns["you're"] + pronouns["you'll"]
i_total = pronouns['i'] + pronouns['my']
print(f"You-forms total: {you_total}")
print(f"I-forms total: {i_total}")
print(f"You:I ratio: {you_total/max(i_total,1):.2f}:1")

# Temporal markers
TEMPORAL = ['now', 'already', 'beginning', 'soon', 'continue', 'continuing',
            'still', 'yet', 'always', 'never', 'forever', 'gradually',
            'slowly', 'gently', 'deeply', 'further', 'each', 'every']
print("\nTemporal/progressive markers:")
for t in TEMPORAL:
    c = word_freq.get(t, 0)
    if c > 0:
        print(f"  {t}: {c}")

# Sensory channel distribution
VISUAL = ['see', 'look', 'watch', 'picture', 'visualize', 'imagine', 'image',
          'color', 'light', 'bright', 'dark', 'glow', 'scene', 'view']
AUDITORY = ['hear', 'listen', 'sound', 'voice', 'tone', 'quiet', 'silence',
            'whisper', 'echo', 'noise', 'music', 'word', 'say', 'tell', 'speak']
KINESTHETIC = ['feel', 'touch', 'warm', 'cool', 'heavy', 'light', 'soft',
               'smooth', 'pressure', 'sensation', 'tingling', 'numbness',
               'comfortable', 'relaxed', 'tension', 'tight', 'loose']

def count_channel(wordlist):
    return sum(word_freq.get(w, 0) for w in wordlist)

vis = count_channel(VISUAL)
aud = count_channel(AUDITORY)
kin = count_channel(KINESTHETIC)
total_sensory = vis + aud + kin
print(f"\nSensory channel distribution:")
print(f"  Visual: {vis} ({100*vis/total_sensory:.1f}%)")
print(f"  Auditory: {aud} ({100*aud/total_sensory:.1f}%)")
print(f"  Kinesthetic: {kin} ({100*kin/total_sensory:.1f}%)")

# Negation patterns
NEG_PATTERNS = [
    (r"\bdon't\b", "don't"),
    (r'\bnot\b', 'not'),
    (r'\bno\b', 'no'),
    (r'\bnever\b', 'never'),
    (r'\bnothing\b', 'nothing'),
    (r'\bnowhere\b', 'nowhere'),
    (r'\bwithout\b', 'without'),
    (r"\bcan't\b", "can't"),
    (r"\bwon't\b", "won't"),
    (r"\bneedn't\b", "needn't"),
]
print("\nNegation frequencies:")
total_neg = 0
for pat, label in NEG_PATTERNS:
    c = len(re.findall(pat, full_lower))
    total_neg += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total negations: {total_neg}")
print(f"Negations per 1000 words: {1000*total_neg/total_words:.2f}")

# Presuppositions
PRESUP_PATTERNS = [
    (r'\balready\b', 'already (temporal presupposition)'),
    (r'\bbeginning to\b', 'beginning to (process presupposition)'),
    (r'\bcontinue to\b', 'continue to (continuity presupposition)'),
    (r'\beven more\b', 'even more (comparative presupposition)'),
    (r'\bstill\b', 'still (continuity presupposition)'),
    (r'\bdeeper\b', 'deeper (comparative presupposition)'),
    (r'\bfurther\b', 'further (comparative presupposition)'),
    (r'\bstart to\b', 'start to (process presupposition)'),
    (r'\bnotice that\b', 'notice that (awareness presupposition)'),
    (r'\brealize that\b', 'realize that (awareness presupposition)'),
    (r'\baware that\b', 'aware that (awareness presupposition)'),
]
print("\nPresupposition markers:")
total_presup = 0
for pat, label in PRESUP_PATTERNS:
    c = len(re.findall(pat, full_lower))
    total_presup += c
    if c > 0:
        print(f"  {label}: {c}")
print(f"Total presuppositions: {total_presup}")
print(f"Presuppositions per 1000 words: {1000*total_presup/total_words:.2f}")

print("\n\n=== ANALYSIS COMPLETE ===")
print(f"Total words analyzed: {total_words}")
print(f"Total sentences: {len(sentences)}")
print(f"Total files: {len(all_text)}")
