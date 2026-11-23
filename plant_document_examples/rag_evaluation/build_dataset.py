"""Build a source-grounded starter gold set; no model calls or RAG run."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import random
import zipfile
from build_corpus import extract

ROOT=Path(__file__).resolve().parent
chunks, documents=extract()
by_id={c['chunk_id']:c for c in chunks}
cases=[]

def add(domain, kind, difficulty, question, answer, facts, forbidden, evidence, reasoning=None):
    number=len(cases)+1
    abstain=kind=='unanswerable'
    cases.append({
        'id':f'PLANT-RAG-{number:03d}', 'dataset_version':'1.0',
        'domain':domain, 'question_type':kind, 'difficulty':difficulty,
        'question':question, 'answerability':'unanswerable' if abstain else 'answerable',
        'expected_behavior':'abstain_and_identify_missing_information' if abstain else 'answer_with_source_citations',
        'reference_answer':answer, 'required_facts':facts, 'prohibited_claims':forbidden,
        'gold_document_ids':sorted({by_id[x]['document_id'] for x in evidence}) if not abstain else [],
        'gold_chunk_ids':evidence if not abstain else [],
        'evidence_role':'missing_information_context' if abstain else 'supporting_evidence',
        'evidence':[{**by_id[x]} for x in evidence],
        'reasoning_note':reasoning,
        'scoring':{'required_facts':'all_required_semantically','prohibited_claims':'none_allowed',
                   'citations':'supported_material_claims' if not abstain else 'optional_for_absence_statement_required_for_positive_source_claims'}
    })

# Safety: 12 cases
add('safety','lookup','easy',
    'Who approves task risk assessments, PPE selection, emergency arrangements, and safety training?',
    'The Safety Manager approves task risk assessments, PPE selection, emergency arrangements, and training.',
    ['Identify the Safety Manager as the approving role.'],
    ['Assign this approval authority solely to operators.'],['SAF001-009'])
add('safety','procedure','medium',
    'Before a shift starts, what should I check in the handover and along the access routes?',
    'Read the handover for unusual conditions, active maintenance, and restricted areas. Confirm clear access to exits, emergency equipment, and marked pedestrian routes.',
    ['Review unusual conditions, active maintenance, and restricted areas.','Confirm clear exits, emergency-equipment access, and marked pedestrian routes.'],
    ['Begin without reviewing handover conditions.'],['SAF001-014','SAF001-015'])
add('safety','scenario','medium',
    'A machine has a safety defect that has not been resolved. Can I start it and report the defect later?',
    'No. Do not start equipment with an unresolved safety defect. Notify the supervisor and mark the equipment status through the site process.',
    ['Do not start the equipment.','Notify the supervisor and mark its status under the site process.'],
    ['Allow operation until the next maintenance window.'],['SAF001-018'])
add('safety','lookup','easy',
    'Are gloves always required around rotating equipment?',
    'The document does not impose a blanket glove rule. Use the PPE specified by the task assessment, and select gloves only where they do not create an entanglement hazard. Keep hair and clothing secured.',
    ['PPE selection follows the task assessment.','Gloves must not introduce an entanglement hazard.'],
    ['Gloves are always required regardless of entanglement risk.'],['SAF001-017'])
add('safety','procedure','easy',
    'What information should workers consult before handling a chemical?',
    'Consult the safety data sheet and task assessment before handling a chemical. Use labeled containers, report damaged containers, and do not mix unknown materials.',
    ['Consult the safety data sheet.','Consult the task assessment before handling.'],
    ['Unknown materials may be mixed to identify them.'],['SAF001-024'])
add('safety','lookup','easy',
    'Does pressing an emergency stop provide energy isolation for servicing?',
    'No. Emergency stops and control switches do not provide energy isolation. Only trained, authorized personnel may apply the machine-specific energy control procedure.',
    ['An emergency stop is not energy isolation.','Use the machine-specific procedure through trained, authorized personnel.'],
    ['An emergency stop alone makes servicing safe.'],['SAF001-027'])
add('safety','procedure','medium',
    'After stored energy is released or restrained, what must happen before servicing begins?',
    'Prevent stored energy from reaccumulating, then verify effective isolation using approved methods before work begins. Return test controls to a safe state. This is part of the authorized machine-specific procedure.',
    ['Prevent stored-energy reaccumulation.','Verify isolation by approved methods before work.','Return test controls to a safe state.'],
    ['Proceed based only on the machine appearing stopped.'],['SAF001-031','SAF001-032','SAF001-027'])
add('safety','procedure','medium',
    'What checks and notifications are required before restarting equipment after isolation?',
    'Inspect the equipment, clear tools and personnel, and restore safeguards. Each person removes their own lock unless an employer-approved exception applies. Notify affected workers before energizing.',
    ['Inspect equipment, clear tools and personnel, and restore safeguards.','Each person removes their own lock, subject to the employer-approved exception process.','Notify affected workers before energizing.'],
    ['Any available coworker may remove another person\'s lock without the approved exception process.'],['SAF001-033'])
add('safety','scenario','easy',
    'There is a chemical spill in my work area. What does the safety procedure tell an ordinary worker to do?',
    'Move away, alert others, and report from a safe location. Only trained responders may assess or clean the spill.',
    ['Move away, alert others, and report from safety.','Assessment and cleanup are limited to trained responders.'],
    ['An untrained worker should clean the spill immediately.'],['SAF001-039'])
add('safety','procedure','easy',
    'When the evacuation alarm sounds, where do I go and how are missing people handled?',
    'Leave by the assigned safe exit, go to the assembly point, and report for headcount. Tell the warden about missing people and do not re-enter until authorized.',
    ['Use the assigned safe exit and report at the assembly point for headcount.','Report missing people to the warden.','Do not re-enter until authorized.'],
    ['Re-enter independently to search for missing people.'],['SAF001-040'])
add('safety','lookup','medium',
    'What information should be recorded when reporting a hazard, injury, or near miss?',
    'Promptly report to the supervisor and record the location, time, condition, and immediate controls. Protect people first and preserve evidence only when it is safe.',
    ['Report promptly to the supervisor.','Record location, time, condition, and immediate controls.','People take priority and evidence is preserved only when safe.'],
    ['Evidence preservation takes priority over protecting people.'],['SAF001-048'])
add('safety','procedure','hard',
    'What must be completed before the example safety document becomes a site procedure?',
    'The Safety Manager must complete the hazard assessment, verify legal applicability, attach machine-specific procedures and the emergency plan, and approve PPE and training. Supervisors must record instruction and demonstrated worker competence.',
    ['Complete the hazard assessment and verify legal applicability.','Attach machine-specific procedures and the emergency plan.','Approve PPE and training.','Record instruction and demonstrated competence.'],
    ['The example is already approved for operational use.'],['SAF001-059','SAF001-004'])

# Maintenance: 12 cases
add('maintenance','lookup','easy',
    'What equipment do the example asset IDs CV 01, MC 01, PF 01, and TG 01 represent?',
    'CV 01 is the belt conveyor, MC 01 is the enclosed machining center, PF 01 is the pneumatic assembly fixture, and TG 01 is the inspection gauge set.',
    ['CV 01 means belt conveyor.','MC 01 means enclosed machining center.','PF 01 means pneumatic assembly fixture.','TG 01 means inspection gauge set.'],
    ['Swap the fixture and gauge asset identifiers.'],['MNT001-014'])
add('maintenance','lookup','medium',
    'Which information belongs in an equipment asset register?',
    'Record asset ID, location, manufacturer, model, serial number, safety criticality, energy-isolation procedure, manufacturer manual revision, spares list, and maintenance history.',
    ['Include asset ID, location, manufacturer, model, and serial number.','Include safety criticality and the energy-isolation procedure.','Include manufacturer manual revision, spares list, and maintenance history.'],
    ['An asset name alone is a complete register.'],['MNT001-013'])
add('maintenance','lookup','easy',
    'Who approves asset plans, maintenance priorities, competent personnel, and completed repairs?',
    'The Maintenance Manager approves asset plans, priorities, competent personnel, and completed repairs.',
    ['Identify the Maintenance Manager.'],
    ['Assign completed-repair approval solely to a warehouse clerk.'],['MNT001-008'])
add('maintenance','lookup','medium',
    'What factors should determine actual maintenance intervals, and are the example intervals manufacturer limits?',
    'Use manufacturer requirements, duty cycle, environment, failure history, and risk to set intervals. The example frequencies are planning prompts, not manufacturer limits.',
    ['Use manufacturer requirements, duty cycle, environment, failure history, and risk.','Example frequencies are planning prompts rather than OEM limits.'],
    ['The example weekly and monthly frequencies are certified manufacturer limits.'],['MNT001-016'])
add('maintenance','lookup','easy',
    'In the example plan, how often is CV 01 inspected, and what does the inspection cover?',
    'The example plan lists a weekly inspection during planned isolation of the belt, rollers, fasteners, and debris accumulation. Record the condition and compare wear and alignment with approved OEM limits.',
    ['Weekly is the example frequency.','Perform during planned isolation; inspect belt, rollers, fasteners, and debris accumulation.','Record condition and compare wear and alignment with approved OEM limits.'],
    ['Inspect by reaching into a running conveyor.'],['MNT001-020'])
add('maintenance','lookup','easy',
    'What is the example monthly task for PF 01, and what evidence is required?',
    'Under isolation, inspect hoses, fittings, supports, and fixture wear. Confirm there is no damage outside approved limits and complete a functional check after safe restoration.',
    ['Monthly PF 01 inspection covers hoses, fittings, supports, and fixture wear under isolation.','Check damage against approved limits and complete a functional check after safe restoration.'],
    ['Pressurized hose disconnection is an approved inspection method.'],['MNT001-022'])
add('maintenance','procedure','medium',
    'What should happen when safety-critical maintenance becomes overdue?',
    'Maintenance and Safety must make a documented risk decision. Keep the asset unavailable if safe operation cannot be demonstrated. If the work is rescheduled, retain the original due date and approval trail.',
    ['A documented risk decision by Maintenance and Safety is required.','Asset stays unavailable if safe operation cannot be demonstrated.','Retain original due date and approval trail when rescheduling.'],
    ['Automatically extend the due date without recording approval.'],['MNT001-026'])
add('maintenance','lookup','medium',
    'Can a technician substitute any available spare part or lubricant?',
    'No. Use approved part numbers and materials; part substitutions require engineering approval. Keep lubricants labeled and closed, prevent mixing, and record their type and quantity. Do not replace an approved asset setting with a generic torque, grease, or pressure value.',
    ['Use approved parts and materials; engineering approval is needed for substitutions.','Control lubricant identity and mixing and record type and quantity.','Do not substitute generic settings for approved asset values.'],
    ['An apparently similar spare or grease may be substituted without approval.'],['MNT001-028'])
add('maintenance','scenario','medium',
    'The conveyor keeps stopping and its belt is tracking poorly. Should I repeatedly reset it?',
    'No. Stop affected use and report the fault; do not reach in or repeatedly reset it. Authorized follow-up is to isolate, inspect under the approved diagnostic plan, correct the cause, and verify tracking.',
    ['Stop affected use and report.','Do not reach in or repeatedly reset.','Isolate and use the approved diagnostic plan; correct the cause and verify tracking.'],
    ['Repeated resets are an acceptable way to continue production.'],['MNT001-030'])
add('maintenance','scenario','medium',
    'An interlock or stop function has failed. May production continue with that function bypassed?',
    'No. Remove the asset from service. A competent person must diagnose and validate the safety function. Never bypass it for production.',
    ['Remove the asset from service.','A competent person diagnoses and validates the function.','Do not bypass for production.'],
    ['A temporary production bypass is allowed to meet a target.'],['MNT001-033'])
add('maintenance','procedure','medium',
    'Who witnesses the operating check after a repair, and when does Quality approve first-piece checks?',
    'Production witnesses the operating check. Quality approves first-piece checks when product may be affected. Record functional and safety results against defined limits, and keep the asset unavailable if any required check fails.',
    ['Production witnesses the operating check.','Quality approves first-piece checks when product may be affected.','Record results against limits and keep the asset unavailable on a required-check failure.'],
    ['A repaired asset can be released despite a failed required test.'],['MNT001-040'])
add('maintenance','lookup','medium',
    'How often does the example maintenance program review recurring faults, and what changes need engineering review?',
    'Review recurring faults, overdue work, and unplanned downtime monthly. Changes to equipment, software, safety functions, or maintenance tasks require engineering review and updated training before use.',
    ['The example review is monthly and covers recurring faults, overdue work, and unplanned downtime.','Equipment, software, safety-function, and task changes require engineering review and updated training before use.'],
    ['Software changes are exempt from engineering review.'],['MNT001-052'])

# Quality: 12 cases
add('quality','lookup','easy',
    'What is the example product part number and drawing revision?',
    'The example product is BRK 100, drawing revision A.',
    ['BRK 100.','Drawing revision A.'],
    ['Drawing revision B.'],['QUA001-011'])
add('quality','lookup','easy',
    'What is the illustrative overall-length tolerance for BRK 100, and which measurement method is listed?',
    'The illustrative overall length is 100.00 mm +/- 0.20 mm, measured with an approved calibrated caliper.',
    ['100.00 mm +/- 0.20 mm.','Approved calibrated caliper.'],
    ['Overall-length tolerance is +/- 0.10 mm.'],['QUA001-013'])
add('quality','lookup','easy',
    'What example limits and measurement method apply to the bracket hole diameter?',
    'The illustrative hole diameter is 10.00 mm +/- 0.10 mm. Use the approved bore or plug gauge method.',
    ['10.00 mm +/- 0.10 mm.','Approved bore or plug gauge method.'],
    ['Use the center-spacing tolerance as the diameter tolerance.'],['QUA001-014'])
add('quality','lookup','easy',
    'What example specification and method apply to hole center spacing?',
    'The illustrative center spacing is 60.00 mm +/- 0.15 mm. Use an approved fixture or coordinate measurement method.',
    ['60.00 mm +/- 0.15 mm.','Approved fixture or coordinate measurement method.'],
    ['Spacing is 60.00 mm +/- 0.20 mm.'],['QUA001-015'])
add('quality','scenario','medium',
    'Using the example standards, what should happen to a bracket whose measured length is 100.28 mm?',
    'It fails the illustrative 100.20 mm upper limit. Stop the process and place suspect product on hold. Quality defines the affected range from traceable evidence, approves investigation and disposition, and requires a passing first piece before process restart.',
    ['100.28 mm exceeds the illustrative 100.20 mm upper limit.','Stop the process and hold suspect product.','Quality defines the range and disposition; require a passing first piece before restart.'],
    ['Round the result down and accept the part.'],['QUA001-042'])
add('quality','procedure','medium',
    'When is first-piece inspection required, what does it cover, and who approves continuation?',
    'Inspect all drawing features before production release and after setup, tooling, program, material, or relevant maintenance changes. Record a first-piece report and obtain supervisor and Quality approval before continuing.',
    ['Before release and after setup, tooling, program, material, or relevant maintenance changes.','Inspect all drawing features and record a first-piece report.','Supervisor and Quality approve continuation.'],
    ['First-piece inspection is needed only on the first day a machine is installed.'],['QUA001-022'])
add('quality','lookup','medium',
    'Does the example in-process plan inspect a sample or every part, and which characteristics are checked?',
    'It checks every part for length, hole diameter, center spacing, and edge or surface condition using approved methods. Record an inspection log and stop and contain on any failure.',
    ['Every part is checked.','Check length, hole diameter, center spacing, and edge or surface condition.','Record results and stop and contain on any failure.'],
    ['Only one part per lot needs inspection under this example plan.'],['QUA001-023'])
add('quality','procedure','medium',
    'What happens to incoming material if required supplier evidence is missing or mismatched?',
    'Place the material on hold and record the receipt. Each receipt is checked for identity, quantity, condition, material-lot labels, and required supplier documents.',
    ['Hold material with missing or mismatched evidence.','Check every receipt for identity, quantity, condition, lot labels, and required supplier documents.'],
    ['Use the material while waiting for the required evidence.'],['QUA001-021'])
add('quality','lookup','medium',
    'Does calibration traceability alone prove a measurement tool is suitable for the inspection?',
    'No. Traceability alone does not prove suitability. The instrument must have a unique ID, suitable range and capability, current calibration, and appropriate condition. Calibration evidence must support the reference chain and account for measurement uncertainty.',
    ['Traceability alone does not prove suitability.','Check unique ID, range and capability, calibration currency, and condition.','Support the calibration chain and account for uncertainty.'],
    ['Any traceable tool is automatically suitable for any tolerance.'],['QUA001-026'])
add('quality','scenario','medium',
    'A result is just outside tolerance. May an inspector round it into tolerance?',
    'No. Quality defines the decision rule and uncertainty treatment before inspection. Do not round a failed result into tolerance or accept a borderline reading without the approved rule.',
    ['Do not round a failed result into tolerance.','Use the Quality-defined decision rule and uncertainty treatment established before inspection.'],
    ['Rounding is allowed whenever the result is close to the limit.'],['QUA001-027'])
add('quality','scenario','medium',
    'We found a defect but cannot tell which units are affected. How much product goes on hold?',
    'Include the full lot until evidence narrows the suspect range. Label and physically segregate affected units with a hold ID and block their use and shipment in the inventory system.',
    ['Hold the full lot until evidence narrows the range.','Use a hold ID, physically segregate, and block use and shipment.'],
    ['Hold only the visibly failed unit when the suspect range is unknown.'],['QUA001-031'])
add('quality','lookup','medium',
    'Can an operator grant a concession for a nonconforming bracket, and what dispositions are listed?',
    'Operators may not grant a concession. Quality and Engineering document disposition: approved rework with reinspection, controlled scrap, supplier return, or an authorized concession. Obtain customer approval where required.',
    ['Operators may not grant concessions.','Quality and Engineering document approved rework plus reinspection, controlled scrap, supplier return, or authorized concession.','Get customer approval where required.'],
    ['An operator can grant a concession solely to meet production targets.'],['QUA001-033'])

# Eight cross-document cases require facts from multiple source documents.
add('cross_document','multi_document','hard',
    'A machining-center repair may have affected bracket dimensions. What maintenance checks and quality approvals are needed before production continues and product ships?',
    'Maintenance records passing functional and safety results against defined limits, with Production witnessing the operating check. Relevant maintenance changes require inspection of all first-piece drawing features and supervisor and Quality approval before continuation. Shipment remains blocked until required checks and approvals are complete.',
    ['Record functional and safety results against limits and have Production witness the operating check.','Inspect all first-piece drawing features after relevant maintenance and obtain supervisor and Quality approval.','Block shipment until required checks and approvals are complete.'],
    ['Repair completion alone authorizes shipment.'],['MNT001-040','QUA001-022','QUA001-024'])
add('cross_document','multi_document','hard',
    'An inspection gauge is found overdue after it was used on parts. What equipment action and product review do the manuals require?',
    'Identify and quarantine the gauge. Quality evaluates prior results, arranges calibration or replacement, and defines containment. Assess product measured since the last known valid check; do not keep using the overdue gauge.',
    ['Identify and quarantine the gauge.','Quality evaluates prior results, arranges calibration or replacement, and defines containment.','Assess product measured since the last known valid check.'],
    ['Continue using the overdue gauge because prior parts appeared acceptable.'],['MNT001-034','QUA001-027'])
add('cross_document','multi_document','hard',
    'Unusual vibration starts during machining. What immediate production, maintenance, and product actions are described?',
    'Stop the machine safely and report the event. Stop using the asset and identify affected product. Maintenance inspects under the approved asset procedure, repairs, and verifies against approved limits. If a product defect is found, stop the affected process and notify the supervisor and Quality, recording the required defect details.',
    ['Stop safely and report the vibration.','Identify affected product and inspect, repair, and verify the asset under the approved procedure.','If product is defective, notify the supervisor and Quality and record the defect details.'],
    ['Continue machining until the vibration causes a confirmed failure.'],['SAF001-025','MNT001-031','QUA001-030'])
add('cross_document','multi_document','hard',
    'Can an operator clean inside equipment during a daily maintenance check if the emergency stop is pressed?',
    'No. Daily checks are external observations from a safe operating position. Intrusive cleaning requires the approved isolation and task procedure. An emergency stop does not provide energy isolation; only trained, authorized personnel may apply the machine-specific energy control procedure.',
    ['Daily checks are external observations.','Intrusive cleaning requires approved isolation and task procedures.','An emergency stop is not isolation; trained, authorized personnel apply the machine-specific procedure.'],
    ['Pressing emergency stop authorizes reaching inside for cleaning.'],['MNT001-018','SAF001-027'])
add('cross_document','multi_document','hard',
    'A guard interlock fault is found during production. Can the machine be used temporarily while repairs are arranged?',
    'No. The safety procedure prohibits starting equipment with an unresolved safety defect and prohibits bypassing safety devices. The maintenance manual requires an asset with an interlock or stop-function fault to be removed from service and diagnosed and validated by a competent person, without a production bypass.',
    ['Do not start equipment with an unresolved safety defect or bypass a safety device.','Remove an asset with interlock or stop-function failure from service.','A competent person must diagnose and validate the failed safety function.'],
    ['A temporary production bypass is allowed.'],['SAF001-018','SAF001-021','MNT001-033'])
add('cross_document','multi_document','hard',
    'Across the maintenance and quality documents, what does each example program review monthly?',
    'Maintenance reviews recurring faults, overdue work, and unplanned downtime. Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions. These monthly frequencies are features of the example programs.',
    ['Maintenance reviews recurring faults, overdue work, and unplanned downtime monthly.','Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions monthly.','Describe these as example-program frequencies.'],
    ['These frequencies are stated as universal legal requirements.'],['MNT001-052','QUA001-050'])
add('cross_document','multi_document','hard',
    'Do these three documents authorize immediate plant operation or prove certification to a quality standard?',
    'No. All three are examples marked not released for operation. Their scenario is for training and demonstration and does not establish compliance or equipment authorization. The quality document explicitly states that no ISO or other quality-standard certification is implied.',
    ['All three are examples and not released for operation.','They do not establish compliance or equipment authorization.','No ISO or other quality-standard certification is implied.'],
    ['The plant is ISO certified because these documents exist.'],['SAF001-004','MNT001-004','QUA001-004','SAF001-006','MNT001-006','QUA001-006','QUA001-009'])
add('cross_document','multi_document','hard',
    'What prevents a maintenance repair sign-off from automatically releasing a held product lot?',
    'Maintenance handover includes first-piece inspection and held-product records, with Quality approval when required. Separately, quality release requires passing inspections and traceability, closure of holds or a valid concession, compliant labels and packaging, and a signed and dated release by the designated Quality authority. A repair sign-off does not replace those product-release requirements.',
    ['Maintenance handover records first-piece inspection and held product and includes Quality approval if required.','Quality requires passing inspections and traceability plus closed holds or a valid concession.','Labels and packaging must comply and the designated Quality authority signs and dates release.'],
    ['A maintenance sign-off automatically removes all product holds.'],['MNT001-048','MNT001-050','QUA001-037','QUA001-038','QUA001-039','QUA001-040'])

# Six deliberately unanswerable requests: context identifies gaps, not missing values.
add('missing_information','unanswerable','medium',
    'What exact emergency telephone number should I call at Riverton Components Plant?',
    'The supplied documents do not give an emergency telephone number; the field is blank. Obtain the approved site emergency contact information before relying on the procedure.',
    ['State that the exact emergency number is not supplied.','Identify the blank site field and need for approved site contact information.'],
    ['Invent a telephone number or present a general emergency number as the plant-specific value.'],['SAF001-043'])
add('missing_information','unanswerable','medium',
    'Where exactly are the primary and alternate assembly areas for this plant?',
    'Their locations are not supplied. The primary and alternate assembly-area fields are blank and must be completed with approved site information.',
    ['Both assembly-area locations are missing.','The fields need approved site information.'],
    ['Invent a parking lot, gate, building, or compass direction.'],['SAF001-044'])
add('missing_information','unanswerable','hard',
    'What exact lubricant grade and quantity should I use for the MC 01 lubrication points?',
    'The source documents do not specify the exact MC 01 lubricant grade or quantity. Approved lubricants and quantities must be entered in the asset task sheet using the applicable manufacturer instructions; do not substitute a generic grease or setting.',
    ['Exact MC 01 lubricant grade and quantity are not provided.','Consult approved asset-specific instructions and task-sheet values.','Do not invent or substitute a generic lubricant.'],
    ['Supply an unsupported lubricant grade, brand, or quantity.'],['MNT001-016','MNT001-021','MNT001-028'])
add('missing_information','unanswerable','medium',
    'How many years must the plant retain quality inspection and calibration records?',
    'No number of years is specified. The document requires retention under an approved site schedule, and retention periods must be approved before site issue.',
    ['A numerical retention period is not supplied.','Use the approved site retention schedule; periods require approval before issue.'],
    ['Invent a fixed retention period such as five or seven years.'],['QUA001-049','QUA001-052'])
add('missing_information','unanswerable','hard',
    'Which exact steel grade must BRK 100 be made from?',
    'The exact grade is not stated. Material grade and condition must match the approved purchase specification, supported by supplier evidence and lot identification. Retrieve the approved specification rather than infer a grade.',
    ['The exact material grade is missing.','The approved purchase specification governs grade and condition.'],
    ['Invent a steel grade or alloy designation.'],['QUA001-012'])
add('missing_information','unanswerable','medium',
    'Who is the named emergency coordinator, and who is their deputy?',
    'No names are provided. The emergency coordinator and deputy field is blank and needs approved site information.',
    ['The coordinator and deputy names are not provided.','The relevant site field is blank.'],
    ['Invent names or treat an unrelated job title as the named coordinator.'],['SAF001-046'])

def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

def validate():
    assert len(cases)==50
    assert len({r['id'] for r in cases})==50
    assert len({r['question'].casefold() for r in cases})==50
    assert Counter(r['domain'] for r in cases)=={'safety':12,'maintenance':12,'quality':12,'cross_document':8,'missing_information':6}
    assert sum(r['answerability']=='answerable' for r in cases)==44
    for row in cases:
        assert row['reference_answer'] and row['required_facts'] and row['prohibited_claims'] and row['evidence']
        assert len({e['chunk_id'] for e in row['evidence']})==len(row['evidence'])
        for e in row['evidence']:
            assert e == by_id[e['chunk_id']]
            assert 1<=e['page']<=4
        if row['question_type']=='multi_document':
            assert len(row['gold_document_ids'])>=2
        if row['answerability']=='unanswerable':
            assert not row['gold_chunk_ids'] and not row['gold_document_ids']
    # Independent arithmetic sanity check for the numerical containment scenario.
    from decimal import Decimal
    assert Decimal('100.00')+Decimal('0.20')==Decimal('100.20')
    assert Decimal('100.28')>Decimal('100.20')

validate()
write_jsonl(ROOT/'golden_dataset.jsonl',cases)
write_jsonl(ROOT/'corpus.jsonl',chunks)
(ROOT/'source_manifest.json').write_text(json.dumps({'corpus_version':'1.0','documents':documents},indent=2),encoding='utf-8')

with (ROOT/'golden_dataset.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['id','domain','question_type','difficulty','answerability','question','reference_answer','required_facts','prohibited_claims','source_locations','gold_chunk_ids','source_evidence','evidence_role']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for r in cases:
        flat={k:r[k] for k in fields if k in r}
        for key in ['required_facts','prohibited_claims','gold_chunk_ids']: flat[key]=json.dumps(flat[key],ensure_ascii=False)
        flat['source_locations']='; '.join(f"{e['document_file']} p{e['page']} / {e['section']} / {e['chunk_id']}" for e in r['evidence'])
        flat['source_evidence']=json.dumps([e['text'] for e in r['evidence']],ensure_ascii=False)
        w.writerow(flat)

questions=[{'id':r['id'],'question':r['question']} for r in cases]
random.Random(42).shuffle(questions)
write_jsonl(ROOT/'test_questions.jsonl',questions)
with (ROOT/'test_questions.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['id','question']); w.writeheader(); w.writerows(questions)
write_jsonl(ROOT/'results_template.jsonl',[{**q,'answer':None,'retrieved_chunk_ids':[],'citations':[],'latency_ms':None,'run_id':None} for q in questions])

report={
    'status':'passed', 'dataset_version':'1.0', 'case_count':len(cases),'corpus_chunks':len(chunks),
    'domain_counts':dict(Counter(r['domain'] for r in cases)),
    'answerability_counts':dict(Counter(r['answerability'] for r in cases)),
    'difficulty_counts':dict(Counter(r['difficulty'] for r in cases)),
    'question_type_counts':dict(Counter(r['question_type'] for r in cases)),
    'checks':['50 unique IDs and question texts','44 answerable and 6 unanswerable','12 cases per source domain and 8 cross-document cases','every evidence reference resolves exactly to the extracted corpus','page references within the four-page sources','cross-document cases cite multiple documents','abstention cases have no positive gold retrieval targets','length containment arithmetic verified with decimals'],
    'review_status':'Agent-authored and source-checked starter set; not independently reviewed by a plant subject-matter expert.',
    'limitations':['No RAG system has been run or scored.','Structural checks do not independently prove semantic correctness.','The set covers these fictional example documents only.']
}
(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
review=['# Plant RAG golden questions and answers','', 'Version 1.0. Agent-authored starter set grounded only in the three example plant documents.','']
for r in cases:
    review += [f"## {r['id']} {r['domain']}",'',f"**Question:** {r['question']}",'',f"**Reference answer:** {r['reference_answer']}",'',f"**Type:** {r['question_type']} | **Difficulty:** {r['difficulty']} | **Answerability:** {r['answerability']}",'','**Required facts:**']
    review += ['- '+fact for fact in r['required_facts']]
    review += ['','**Do not claim:**']+['- '+claim for claim in r['prohibited_claims']]
    review += ['','**Source evidence**'+(' identifying the gap' if r['answerability']=='unanswerable' else '')+':']
    for e in r['evidence']:
        review += [f"- {e['document_file']}, page {e['page']}, {e['section']} ({e['chunk_id']}): {e['text'].replace(chr(10),' ')}"]
    review += ['']
(ROOT/'golden_questions_and_answers.md').write_text('\n'.join(review),encoding='utf-8')
print(json.dumps(report,indent=2))
