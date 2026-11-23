"""Extract only the three source DOCX files, preserving manual page breaks."""
from pathlib import Path
import hashlib
import json
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT.parent / 'documents'
DOCS = [('SAF001','Plant_Safety_Procedures.docx'),('MNT001','Plant_Maintenance_Manual.docx'),('QUA001','Plant_Quality_Control_Standards.docx')]

def extract():
    chunks=[]
    manifest=[]
    for doc_id, name in DOCS:
        file=SOURCES/name
        doc=Document(file)
        page=1; index=0; section='Document introduction'
        for el in doc.element.body.iterchildren():
            texts=[]
            kind='paragraph'
            if el.tag == qn('w:p'):
                p=Paragraph(el,doc)
                page += sum(br.get(qn('w:type')) == 'page' for br in el.iter(qn('w:br')))
                if p.style.name.startswith('Heading'): section=p.text
                if p.text.strip(): texts=[p.text.strip()]
            elif el.tag == qn('w:tbl'):
                kind='table_row'
                t=Table(el,doc)
                headers=[c.text.strip() for c in t.rows[0].cells]
                texts=[' | '.join(f'{h}: {c.text.strip()}' for h,c in zip(headers,row.cells)) for row in t.rows[1:] if any(c.text.strip() for c in row.cells)]
            for text in texts:
                index+=1
                chunks.append({'chunk_id':f'{doc_id}-{index:03d}','document_id':doc_id,'document_file':name,'page':page,'section':section,'kind':kind,'text':text})
        manifest.append({'document_id':doc_id,'document_file':name,'relative_path':f'../documents/{name}','revision':'0','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'pages':page,'chunk_count':index})
    return chunks, manifest

if __name__=='__main__':
    chunks, manifest=extract()
    (ROOT/'corpus.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in chunks),encoding='utf-8')
    (ROOT/'source_manifest.json').write_text(json.dumps({'corpus_version':'1.0','documents':manifest},indent=2),encoding='utf-8')
    for c in chunks: print(c['chunk_id'],f"p{c['page']}",c['text'])
