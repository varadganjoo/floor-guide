"""Sample the question-only file with a reproducible seed; standard library only."""
import argparse
import json
from pathlib import Path
import random

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--count',type=int,default=10)
parser.add_argument('--seed',type=int,default=42)
args=parser.parse_args()
rows=[json.loads(line) for line in (Path(__file__).resolve().parent/'test_questions.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
if not 1<=args.count<=len(rows): parser.error(f'--count must be between 1 and {len(rows)}')
for row in random.Random(args.seed).sample(rows,args.count):
    print(json.dumps(row,ensure_ascii=False))
