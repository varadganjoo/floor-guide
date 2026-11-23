"""Verify exported dataset consistency and build a portable ZIP package."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent

def read_jsonl(name):
    return [json.loads(line) for line in (ROOT/name).read_text(encoding='utf-8').splitlines() if line.strip()]

gold=read_jsonl('golden_dataset.jsonl')
queries=read_jsonl('test_questions.jsonl')
results=read_jsonl('results_template.jsonl')
corpus=read_jsonl('corpus.jsonl')
with (ROOT/'golden_dataset.csv').open(encoding='utf-8-sig',newline='') as f: csv_gold=list(csv.DictReader(f))
with (ROOT/'test_questions.csv').open(encoding='utf-8-sig',newline='') as f: csv_queries=list(csv.DictReader(f))
assert len(gold)==len(queries)==len(results)==len(csv_gold)==len(csv_queries)==50
assert queries==csv_queries
question_by_id={g['id']:g['question'] for g in gold}
assert {q['id']:q['question'] for q in queries}==question_by_id
assert all(set(q)=={'id','question'} for q in queries)
assert [q['id'] for q in queries]!=[g['id'] for g in gold]
assert [{k:r[k] for k in ['id','question']} for r in results]==queries
assert all(r['answer'] is None and r['retrieved_chunk_ids']==[] for r in results)
for a,b in zip(gold,csv_gold):
    for k in ['id','question','reference_answer','answerability','domain','question_type','difficulty','evidence_role']:
        assert a[k]==b[k],(a['id'],k)
    for k in ['required_facts','prohibited_claims','gold_chunk_ids']:
        assert a[k]==json.loads(b[k]),(a['id'],k)
    assert [e['text'] for e in a['evidence']]==json.loads(b['source_evidence'])
lookup={c['chunk_id']:c for c in corpus}
assert len(lookup)==177
for row in gold:
    assert all(e==lookup[e['chunk_id']] for e in row['evidence'])
    assert row['id'] in (ROOT/'golden_questions_and_answers.md').read_text(encoding='utf-8')
manifest=json.loads((ROOT/'source_manifest.json').read_text(encoding='utf-8'))
for doc in manifest['documents']:
    path=(ROOT/doc['relative_path']).resolve()
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==doc['sha256']

def sample(count,seed):
    p=subprocess.run([sys.executable,str(ROOT/'sample_questions.py'),'--count',str(count),'--seed',str(seed)],capture_output=True,text=True,check=True)
    return [json.loads(x) for x in p.stdout.splitlines()]

subset=sample(10,2026)
assert subset==sample(10,2026)
assert len({r['id'] for r in subset})==10
assert all(question_by_id[r['id']]==r['question'] for r in subset)
assert subset!=sample(10,2027)
assert len(sample(50,42))==50
for count in [0,51]:
    p=subprocess.run([sys.executable,str(ROOT/'sample_questions.py'),'--count',str(count)],capture_output=True,text=True)
    assert p.returncode==2 and '--count must be between 1 and 50' in p.stderr

report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
extra=['CSV and JSONL values match','question-only files contain only ID and question','shuffled questions and empty results preserve gold case IDs','source file SHA256 hashes match','random sampler is repeatable and samples without replacement','sampler rejects invalid sample sizes']
report['checks']+= [x for x in extra if x not in report['checks']]
report['package_validation']='passed'
(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

bundle=ROOT.parent/'Plant_RAG_Golden_Dataset.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.suffix in {'.json','.jsonl','.csv','.md','.py'}:
            z.write(path,'rag_evaluation/'+path.name)
    for doc in manifest['documents']:
        path=(ROOT/doc['relative_path']).resolve()
        z.write(path,'documents/'+path.name)
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    assert len(z.namelist())==17
    assert len(z.read('rag_evaluation/test_questions.jsonl').splitlines())==50
    for doc in manifest['documents']:
        assert hashlib.sha256(z.read('documents/'+doc['document_file'])).hexdigest()==doc['sha256']
print(json.dumps({'case_count':len(gold),'corpus_chunks':len(corpus),'checks':'passed','bundle':str(bundle),'bundle_bytes':bundle.stat().st_size,'archive_members':17,'sample_ids_seed_2026':[r['id'] for r in subset]},indent=2))
