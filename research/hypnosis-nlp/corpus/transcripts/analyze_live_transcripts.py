#!/usr/bin/env python3
"""
Phase 2: Cybernetic Feedback Loop Analysis
Analyzes live hypnosis transcripts for contingency/utilization patterns
and compares against Phase 1 static baseline signatures.
"""

import os
import re
from collections import Counter, defaultdict
import sys

TRANSCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Phase 1 baseline values (from static_syntax_analysis_v2.md)
BASELINE = {
    "imp_perm_ratio": 4.36,
    "true_directive_rate": 0.244,
    "let_rate": 6.00,  # per 1k words
    "nominalization_rate": 12.40,
    "embedded_cmd_rate": 10.05,
    "ttr": 0.1019,
    "lexical_density": 0.4716,
    "you_i_ratio": 6.43,
    "you_rate": 89.8,  # per 1k words
    "now_rate": 10.21,
    "kinesthetic_pct": 0.603,
    "pacing_rate": 10.10,
    "presup_rate": 6.90,
    "deeper_rate": 2.86,  # 51 tokens / 17819 words * 1000
}

# Cybernetic-specific patterns
FEEDBACK_MARKERS = [
    r"\[(?:subject|client|patient)\s+(?:nods?|breathes?|blinks?|eyes?\s+(?:close|twitch|flutter)|head\s+(?:drops?|nods?)|arm\s+(?:drops?|lifts?|stays?|remains?))",
    r"\[(?:wait\s+for|look\s+for|watching?\s+for)",
    r"\[(?:if\s+(?:head|eyes?|hand|arm|subject|client))",
]

CONTINGENCY_MARKERS = [
    r"that's right",
    r"that's it",
    r"that's good",
    r"that's wonderful",
    r"that's fine",
    r"good\.?\s",
    r"very good",
    r"wonderful",
    r"perfect",
    r"exactly",
]

UTILIZATION_PATTERNS = [
    r"and\s+as\s+(?:you|that|your)",
    r"notice\s+(?:how|that|what)",
    r"you\s+(?:can|might|may)\s+(?:notice|feel|sense|become\s+aware)",
    r"that's\s+right.*?(?:and|as|while|when)",
    r"(?:each|every|with\s+each)\s+(?:breath|step|number|count)",
]

WAIT_PATTERNS = [
    r"\[wait\s+for",
    r"\[pause\]",
    r"\[.*?seconds?\]",
    r"\.{3,}",  # ellipsis as prosodic pause
    r"…",       # unicode ellipsis
]

CONDITIONAL_PATTERNS = [
    r"\[if\s+",
    r"(?:if|when|whenever)\s+(?:you|they|the\s+(?:subject|client))",
    r"(?:or\s+it\s+might|or\s+(?:you|they)\s+might)",
    r"(?:whether|however)\s+you",
]

# Standard NLP patterns from Phase 1
LET_PATTERN = re.compile(r'\blet\b', re.I)
RELAX_PATTERN = re.compile(r'\brelax\w*\b', re.I)
NOW_PATTERN = re.compile(r'\bnow\b', re.I)
DEEPER_PATTERN = re.compile(r'\bdeeper\b', re.I)
YOU_PATTERN = re.compile(r'\byou(?:r|rs|rself|rselves)?\b', re.I)
I_PATTERN = re.compile(r'\b(?:I|me|my|mine|myself)\b')

NOMINALIZATION_WORDS = [
    'relaxation', 'awareness', 'sensation', 'feeling', 'comfort',
    'confidence', 'calmness', 'peace', 'tranquility', 'consciousness',
    'experience', 'understanding', 'curiosity', 'creativity', 'learning',
    'heaviness', 'lightness', 'warmth', 'coolness', 'numbness',
    'drowsiness', 'sleepiness', 'peacefulness', 'serenity', 'releasing',
    'imagination', 'concentration', 'absorption', 'discovery', 'achievement'
]

EMBEDDED_CMD_PATTERNS = [
    r'\byou\s+can\s+\w+',
    r'\byou\s+will\s+\w+',
    r'\byou\s+might\s+\w+',
    r'\byou\s+may\s+\w+',
    r'\bI\s+want\s+you\s+to\b',
    r'\ballow\s+yourself\s+to\b',
    r'\bfind\s+yourself\b',
]

PACING_PATTERNS = [
    r'\bas\s+you\b',
    r'\bwhen\s+you\b',
    r'\bwhile\s+you\b',
    r'\bthe\s+more\s+you\b',
    r'\bwith\s+each\b',
    r'\beach\s+time\b',
    r'\bevery\s+time\b',
]

KINESTHETIC_WORDS = set([
    'warm', 'heavy', 'light', 'soft', 'relaxed', 'comfortable', 'tension',
    'weight', 'pressure', 'numb', 'tingling', 'floating', 'sinking',
    'drifting', 'dropping', 'loosening', 'releasing', 'spreading',
    'flowing', 'settling', 'limp', 'loose', 'deep', 'deeper',
])

VISUAL_WORDS = set([
    'see', 'look', 'watch', 'bright', 'dark', 'color', 'colour',
    'imagine', 'picture', 'image', 'focus', 'clear', 'vivid',
    'scene', 'view', 'notice', 'observe', 'visualize',
])

AUDITORY_WORDS = set([
    'hear', 'listen', 'sound', 'voice', 'quiet', 'silence', 'tone',
    'whisper', 'loud', 'soft', 'music', 'rhythm', 'echo',
])


def extract_transcript_text(filepath):
    """Extract only the transcript dialogue, removing metadata headers."""
    with open(filepath, 'r') as f:
        text = f.read()
    # Remove header metadata (everything before the --- separator line)
    parts = text.split('---\n', 2)
    if len(parts) >= 3:
        text = parts[2]
    elif len(parts) == 2:
        text = parts[1]
    return text


def extract_speaker_turns(text):
    """Parse transcript into speaker turns."""
    turns = []
    # Match patterns like "HYPNOTIST:", "SUBJECT:", "ERICKSON:", "CLIENT:", etc.
    pattern = re.compile(r'^((?:HYPNOTIST|THERAPIST|ERICKSON|SUBJECT|CLIENT|ANSWER|QUESTION)\s*:)\s*(.*?)(?=^(?:HYPNOTIST|THERAPIST|ERICKSON|SUBJECT|CLIENT|ANSWER|QUESTION)\s*:|$)',
                         re.M | re.S)
    matches = pattern.findall(text)
    for speaker_label, content in matches:
        speaker = speaker_label.strip(':').strip()
        role = 'hypnotist' if speaker in ('HYPNOTIST', 'THERAPIST', 'ERICKSON') else 'subject'
        turns.append({
            'speaker': speaker,
            'role': role,
            'text': content.strip(),
        })
    return turns


def extract_stage_directions(text):
    """Extract all stage directions [in brackets]."""
    return re.findall(r'\[([^\]]+)\]', text)


def get_words(text):
    """Get word tokens from text, excluding stage directions."""
    clean = re.sub(r'\[.*?\]', '', text)
    clean = re.sub(r'[^\w\s\']', ' ', clean)
    return [w.lower() for w in clean.split() if w.strip()]


def analyze_transcript(filepath):
    """Full analysis of a single live transcript."""
    text = extract_transcript_text(filepath)
    turns = extract_speaker_turns(text)
    stage_dirs = extract_stage_directions(text)
    words = get_words(text)
    total_words = len(words)

    if total_words == 0:
        return None

    # Count turns by role
    hypnotist_turns = [t for t in turns if t['role'] == 'hypnotist']
    subject_turns = [t for t in turns if t['role'] == 'subject']

    # Get hypnotist-only text for linguistic analysis
    hypnotist_text = ' '.join(t['text'] for t in hypnotist_turns) if hypnotist_turns else text
    h_words = get_words(hypnotist_text)
    h_total = len(h_words) if h_words else total_words

    # === CYBERNETIC METRICS (unique to Phase 2) ===

    # 1. Feedback markers in stage directions
    feedback_count = 0
    feedback_types = Counter()
    for sd in stage_dirs:
        sd_lower = sd.lower()
        for pat in FEEDBACK_MARKERS:
            if re.search(pat, sd_lower):
                feedback_count += 1
                # Classify feedback type
                if any(w in sd_lower for w in ['breathe', 'breathing', 'breath']):
                    feedback_types['breathing'] += 1
                elif any(w in sd_lower for w in ['blink', 'eye', 'eyelid', 'twitch']):
                    feedback_types['eye_movement'] += 1
                elif any(w in sd_lower for w in ['nod', 'head']):
                    feedback_types['head_movement'] += 1
                elif any(w in sd_lower for w in ['arm', 'hand', 'finger', 'wrist']):
                    feedback_types['limb_response'] += 1
                else:
                    feedback_types['other'] += 1
                break

    # 2. Wait/pause markers (prosodic sensitivity)
    wait_count = sum(len(re.findall(pat, text, re.I)) for pat in WAIT_PATTERNS)

    # 3. Contingency ratifiers
    contingency_count = sum(len(re.findall(pat, text, re.I)) for pat in CONTINGENCY_MARKERS)

    # 4. Utilization patterns
    utilization_count = sum(len(re.findall(pat, text, re.I)) for pat in UTILIZATION_PATTERNS)

    # 5. Conditional branching
    conditional_count = sum(len(re.findall(pat, text, re.I)) for pat in CONDITIONAL_PATTERNS)

    # 6. Stage direction density
    stage_dir_density = len(stage_dirs) / (total_words / 1000) if total_words > 0 else 0

    # === PHASE 1 COMPARISON METRICS ===

    # Let rate
    let_count = len(LET_PATTERN.findall(hypnotist_text))
    let_rate = (let_count / h_total) * 1000

    # Now rate
    now_count = len(NOW_PATTERN.findall(hypnotist_text))
    now_rate = (now_count / h_total) * 1000

    # Deeper rate
    deeper_count = len(DEEPER_PATTERN.findall(hypnotist_text))
    deeper_rate = (deeper_count / h_total) * 1000

    # You:I ratio
    you_count = len(YOU_PATTERN.findall(hypnotist_text))
    i_count = len(I_PATTERN.findall(hypnotist_text))
    you_rate = (you_count / h_total) * 1000
    you_i_ratio = you_count / i_count if i_count > 0 else float('inf')

    # TTR
    unique_words = set(h_words)
    ttr = len(unique_words) / h_total if h_total > 0 else 0

    # Nominalization rate
    nom_count = sum(1 for w in h_words if w in NOMINALIZATION_WORDS)
    nom_rate = (nom_count / h_total) * 1000

    # Embedded command rate
    emb_count = sum(len(re.findall(pat, hypnotist_text, re.I)) for pat in EMBEDDED_CMD_PATTERNS)
    emb_rate = (emb_count / h_total) * 1000

    # Pacing rate
    pace_count = sum(len(re.findall(pat, hypnotist_text, re.I)) for pat in PACING_PATTERNS)
    pace_rate = (pace_count / h_total) * 1000

    # Sensory channels
    k_count = sum(1 for w in h_words if w in KINESTHETIC_WORDS)
    v_count = sum(1 for w in h_words if w in VISUAL_WORDS)
    a_count = sum(1 for w in h_words if w in AUDITORY_WORDS)
    sensory_total = k_count + v_count + a_count
    k_pct = k_count / sensory_total if sensory_total > 0 else 0
    v_pct = v_count / sensory_total if sensory_total > 0 else 0
    a_pct = a_count / sensory_total if sensory_total > 0 else 0

    # Ellipsis/pause density (prosodic markers)
    ellipsis_count = text.count('…') + text.count('...')
    ellipsis_rate = (ellipsis_count / h_total) * 1000

    # Relax rate
    relax_count = len(RELAX_PATTERN.findall(hypnotist_text))
    relax_rate = (relax_count / h_total) * 1000

    # "that's right" rate (contingency ratification)
    thats_right = len(re.findall(r"that's right", hypnotist_text, re.I))
    thats_right_rate = (thats_right / h_total) * 1000

    return {
        'filename': os.path.basename(filepath),
        'total_words': total_words,
        'hypnotist_words': h_total,
        'turns_total': len(turns),
        'turns_hypnotist': len(hypnotist_turns),
        'turns_subject': len(subject_turns),
        'turn_ratio': len(subject_turns) / len(hypnotist_turns) if hypnotist_turns else 0,
        # Cybernetic metrics
        'feedback_markers': feedback_count,
        'feedback_types': dict(feedback_types),
        'wait_markers': wait_count,
        'contingency_ratifiers': contingency_count,
        'utilization_patterns': utilization_count,
        'conditional_branches': conditional_count,
        'stage_directions': len(stage_dirs),
        'stage_dir_density': stage_dir_density,
        'ellipsis_rate': ellipsis_rate,
        'thats_right_rate': thats_right_rate,
        # Phase 1 comparison
        'let_rate': let_rate,
        'now_rate': now_rate,
        'deeper_rate': deeper_rate,
        'you_rate': you_rate,
        'you_i_ratio': you_i_ratio,
        'ttr': ttr,
        'nom_rate': nom_rate,
        'emb_rate': emb_rate,
        'pace_rate': pace_rate,
        'relax_rate': relax_rate,
        'k_pct': k_pct,
        'v_pct': v_pct,
        'a_pct': a_pct,
    }


def classify_interactivity(result):
    """Classify transcript by interactivity level."""
    if result['turns_subject'] >= 5:
        return 'HIGH'
    elif result['turns_subject'] >= 2:
        return 'MODERATE'
    elif result['stage_directions'] >= 5:
        return 'NONVERBAL'
    else:
        return 'MONOLOGUE'


def main():
    files = sorted([
        os.path.join(TRANSCRIPT_DIR, f)
        for f in os.listdir(TRANSCRIPT_DIR)
        if f.endswith('.txt') and not f.startswith('.')
    ])

    if not files:
        print("No transcript files found!")
        return

    results = []
    for f in files:
        r = analyze_transcript(f)
        if r:
            r['interactivity'] = classify_interactivity(r)
            results.append(r)

    print("=" * 80)
    print("PHASE 2: CYBERNETIC FEEDBACK LOOP — LIVE TRANSCRIPT ANALYSIS")
    print("=" * 80)
    print(f"\nCorpus: {len(results)} live transcripts")
    total_words = sum(r['total_words'] for r in results)
    print(f"Total words: {total_words:,}")
    print()

    # === SECTION 1: INTERACTIVITY CLASSIFICATION ===
    print("-" * 60)
    print("1. INTERACTIVITY CLASSIFICATION")
    print("-" * 60)
    for r in results:
        short_name = r['filename'][:50]
        print(f"  {short_name:<52} {r['interactivity']:<10} "
              f"H:{r['turns_hypnotist']:>2} S:{r['turns_subject']:>2} "
              f"SD:{r['stage_directions']:>2}")

    inter_counts = Counter(r['interactivity'] for r in results)
    print(f"\n  HIGH: {inter_counts.get('HIGH', 0)}  "
          f"MODERATE: {inter_counts.get('MODERATE', 0)}  "
          f"NONVERBAL: {inter_counts.get('NONVERBAL', 0)}  "
          f"MONOLOGUE: {inter_counts.get('MONOLOGUE', 0)}")

    # === SECTION 2: CYBERNETIC METRICS ===
    print()
    print("-" * 60)
    print("2. CYBERNETIC FEEDBACK METRICS")
    print("-" * 60)

    print("\n  a) Feedback Markers (non-verbal observation cues in stage directions)")
    all_feedback = Counter()
    for r in results:
        for k, v in r['feedback_types'].items():
            all_feedback[k] += v
    total_fb = sum(r['feedback_markers'] for r in results)
    print(f"     Total feedback markers: {total_fb}")
    for k, v in all_feedback.most_common():
        print(f"       {k}: {v}")

    print(f"\n  b) Wait/Pause Markers (prosodic sensitivity)")
    total_wait = sum(r['wait_markers'] for r in results)
    print(f"     Total wait markers: {total_wait}")
    for r in sorted(results, key=lambda x: x['wait_markers'], reverse=True)[:5]:
        print(f"       {r['filename'][:45]}: {r['wait_markers']}")

    print(f"\n  c) Contingency Ratifiers ('that's right', 'good', 'wonderful', etc.)")
    total_cont = sum(r['contingency_ratifiers'] for r in results)
    print(f"     Total contingency ratifiers: {total_cont}")
    avg_cont = total_cont / len(results)
    print(f"     Average per transcript: {avg_cont:.1f}")
    for r in sorted(results, key=lambda x: x['contingency_ratifiers'], reverse=True)[:5]:
        print(f"       {r['filename'][:45]}: {r['contingency_ratifiers']}")

    print(f"\n  d) Utilization Patterns (feeding back subject state into suggestions)")
    total_util = sum(r['utilization_patterns'] for r in results)
    print(f"     Total utilization patterns: {total_util}")
    avg_util = total_util / len(results)
    print(f"     Average per transcript: {avg_util:.1f}")

    print(f"\n  e) Conditional Branching (if/when contingent on subject response)")
    total_cond = sum(r['conditional_branches'] for r in results)
    print(f"     Total conditional branches: {total_cond}")

    print(f"\n  f) Ellipsis/Pause Rate (prosodic markers per 1k words)")
    avg_ell = sum(r['ellipsis_rate'] for r in results) / len(results)
    print(f"     Average: {avg_ell:.1f}/1k words")
    print(f"     Phase 1 baseline: ~0/1k (static scripts have no pause notation)")

    print(f"\n  g) 'That's right' Rate (ratification density)")
    avg_tr = sum(r['thats_right_rate'] for r in results) / len(results)
    print(f"     Average: {avg_tr:.1f}/1k words")
    print(f"     Phase 1 baseline: not measured (absent in static scripts)")

    # === SECTION 3: PHASE 1 COMPARISON ===
    print()
    print("-" * 60)
    print("3. PHASE 1 BASELINE COMPARISON")
    print("-" * 60)

    metrics = [
        ('let_rate', 'Let rate (/1k)', BASELINE['let_rate']),
        ('now_rate', 'Now rate (/1k)', BASELINE['now_rate']),
        ('deeper_rate', 'Deeper rate (/1k)', BASELINE['deeper_rate']),
        ('you_rate', 'You rate (/1k)', BASELINE['you_rate']),
        ('you_i_ratio', 'You:I ratio', BASELINE['you_i_ratio']),
        ('ttr', 'Type-Token Ratio', BASELINE['ttr']),
        ('nom_rate', 'Nominalization (/1k)', BASELINE['nominalization_rate']),
        ('emb_rate', 'Embedded cmds (/1k)', BASELINE['embedded_cmd_rate']),
        ('pace_rate', 'Pacing phrases (/1k)', BASELINE['pacing_rate']),
        ('relax_rate', 'Relax rate (/1k)', None),
        ('k_pct', 'Kinesthetic %', BASELINE['kinesthetic_pct']),
    ]

    print(f"\n  {'Metric':<25} {'Live Mean':>10} {'Live SD':>10} {'Baseline':>10} {'Delta':>10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    for key, label, baseline in metrics:
        vals = [r[key] for r in results if r[key] != float('inf')]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        variance = sum((v - mean)**2 for v in vals) / len(vals)
        sd = variance ** 0.5
        if baseline is not None:
            delta = ((mean - baseline) / baseline) * 100
            print(f"  {label:<25} {mean:>10.2f} {sd:>10.2f} {baseline:>10.2f} {delta:>+9.1f}%")
        else:
            print(f"  {label:<25} {mean:>10.2f} {sd:>10.2f} {'N/A':>10}")

    # === SECTION 4: SEQUENCING ANALYSIS ===
    print()
    print("-" * 60)
    print("4. SEQUENCING & TEMPORAL ANALYSIS")
    print("-" * 60)

    # Analyze turn-taking patterns in high-interactivity transcripts
    interactive = [r for r in results if r['interactivity'] in ('HIGH', 'MODERATE')]
    if interactive:
        print(f"\n  Interactive transcripts: {len(interactive)}")
        avg_turns = sum(r['turns_total'] for r in interactive) / len(interactive)
        avg_ratio = sum(r['turn_ratio'] for r in interactive) / len(interactive)
        print(f"  Average turns per session: {avg_turns:.1f}")
        print(f"  Average subject:hypnotist turn ratio: {avg_ratio:.2f}")
        print(f"  (Static scripts have 0.0 turn ratio — pure monologue)")

    # Stage direction density comparison
    print(f"\n  Stage Direction Density (per 1k words):")
    for r in sorted(results, key=lambda x: x['stage_dir_density'], reverse=True):
        print(f"    {r['filename'][:45]}: {r['stage_dir_density']:.1f}")

    # === SECTION 5: SENSORY CHANNEL COMPARISON ===
    print()
    print("-" * 60)
    print("5. SENSORY CHANNEL DISTRIBUTION (vs Phase 1 K:60/V:25/A:15)")
    print("-" * 60)

    avg_k = sum(r['k_pct'] for r in results) / len(results) * 100
    avg_v = sum(r['v_pct'] for r in results) / len(results) * 100
    avg_a = sum(r['a_pct'] for r in results) / len(results) * 100
    print(f"  Live transcripts: K:{avg_k:.1f}% / V:{avg_v:.1f}% / A:{avg_a:.1f}%")
    print(f"  Static baseline:  K:60.3%  / V:25.0% / A:14.7%")

    # === SECTION 6: KEY FINDINGS ===
    print()
    print("=" * 80)
    print("KEY CYBERNETIC FINDINGS")
    print("=" * 80)

    # Calculate cybernetic density
    cybernetic_density = (total_fb + total_wait + total_cont + total_util + total_cond) / (total_words / 1000)
    print(f"\n  Total Cybernetic Density: {cybernetic_density:.1f} markers per 1k words")
    print(f"  (feedback + wait + contingency + utilization + conditional)")
    print(f"  Phase 1 baseline: 0.0 (static scripts have no feedback loop)")

    print(f"\n  Breakdown:")
    print(f"    Feedback markers:     {total_fb:>4} ({total_fb/(total_words/1000):.1f}/1k)")
    print(f"    Wait/pause markers:   {total_wait:>4} ({total_wait/(total_words/1000):.1f}/1k)")
    print(f"    Contingency ratifiers:{total_cont:>4} ({total_cont/(total_words/1000):.1f}/1k)")
    print(f"    Utilization patterns: {total_util:>4} ({total_util/(total_words/1000):.1f}/1k)")
    print(f"    Conditional branches: {total_cond:>4} ({total_cond/(total_words/1000):.1f}/1k)")

    print()


if __name__ == '__main__':
    main()
