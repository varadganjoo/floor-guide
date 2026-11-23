from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'documents'
OUT.mkdir(exist_ok=True)

def para(doc, text, style=None):
    p = doc.add_paragraph(text, style)
    return p

def heading(doc, text):
    doc.add_heading(text, level=1)

def bullets(doc, items):
    for item in items: para(doc, item, 'List Bullet')

def steps(doc, items):
    for i, item in enumerate(items, 1): para(doc, f'{i}. {item}')

def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c, w in zip(t.columns, widths): c.width = Inches(w)
    for cell, text in zip(t.rows[0].cells, headers): cell.text = text
    props = t.rows[0]._tr.get_or_add_trPr()
    rep = OxmlElement('w:tblHeader'); props.append(rep)
    for row in rows:
        for cell, text in zip(t.add_row().cells, row): cell.text = text
    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        for ci, cell in enumerate(row.cells):
            cell.width = Inches(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), '253848' if ri == 0 else ('F2F5F7' if ri % 2 else 'FFFFFF'))
            pr.append(shading)
            margins = OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                e = OxmlElement('w:'+edge); e.set(qn('w:w'),'95'); e.set(qn('w:type'),'dxa'); margins.append(e)
            pr.append(margins)
            borders = OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e = OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); borders.append(e)
            pr.append(borders)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.03
                for r in p.runs:
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor.from_string('FFFFFF' if ri == 0 else '000000')
                    r.bold = ri == 0
    para(doc, '') .paragraph_format.space_after = Pt(0)
    return t

def newdoc(title, ident, owner, purpose):
    d = Document()
    s = d.sections[0]
    s.page_width = Inches(8.5); s.page_height = Inches(11)
    s.top_margin = Inches(.7); s.bottom_margin = Inches(.65)
    s.left_margin = s.right_margin = Inches(.75)
    s.header_distance = s.footer_distance = Inches(.3)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','List Bullet']:
        st = d.styles[name]; st.font.name = 'Calibri'; st.font.color.rgb = RGBColor(0,0,0)
    d.styles['Normal'].font.size = Pt(10.5)
    d.styles['Normal'].paragraph_format.space_after = Pt(6)
    d.styles['Normal'].paragraph_format.line_spacing = 1.06
    d.styles['Title'].font.size = Pt(26)
    d.styles['Title'].paragraph_format.space_after = Pt(9)
    d.styles['Heading 1'].font.size = Pt(14)
    d.styles['Heading 1'].paragraph_format.space_before = Pt(12)
    d.styles['Heading 1'].paragraph_format.space_after = Pt(6)
    d.styles['Heading 2'].font.size = Pt(11)
    for border in list(d.styles.element.xpath('.//w:pBdr')):
        border.getparent().remove(border)
    para(d, title, 'Title')
    para(d, 'Example plant document  |  Riverton Components Plant', 'Subtitle')
    para(d, f'{ident}  |  Revision 0  |  Prepared 23 November 2026  |  Owner {owner}')
    para(d, 'EXAMPLE ONLY - NOT RELEASED FOR OPERATION').runs[0].bold = True
    para(d, purpose)
    para(d, 'Plant scenario: a fictional facility receiving metal blanks, machining and deburring brackets, assembling components, and packing finished goods. This document supports training and demonstration. It does not establish regulatory compliance or equipment authorization.')
    p = s.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r=p.add_run(f'{ident}  |  Example only  |  Page '); r.font.size=Pt(8)
    field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); p._p.append(field)
    d.core_properties.author = 'Riverton Components Plant'
    d.core_properties.title = title
    d.core_properties.subject = 'Example plant operating documentation'
    return d

def page(d, title):
    d.add_page_break(); heading(d, title)

def refs(d, entries):
    heading(d, 'Reference material')
    for name,url in entries:
        p=para(d, name + '\n' + url)
        for r in p.runs: r.font.size=Pt(8.5)
    para(d, 'Reference pages checked 23 November 2026. Confirm applicable local requirements and current manufacturer instructions before site release.').runs[0].font.size=Pt(9)

d = newdoc('Plant Safety Procedures','SAF 001','Safety Manager',
    'Employees, contractors, and visitors use these example procedures to recognize hazards, stop unsafe work, and report emergencies. Work may begin only after site hazards, training, and task controls have been approved.')
heading(d,'1 Responsibilities and work boundaries')
table(d,['Role','Responsibility'],[
    ('Plant Manager','Provide resources and authorize the site safety program.'),
    ('Safety Manager','Approve task risk assessments, PPE selection, emergency arrangements, and training.'),
    ('Supervisors','Confirm worker competence, inspect work areas, and correct unsafe conditions.'),
    ('All personnel','Follow approved instructions, report hazards, and stop work when controls fail.')],[1.5,5.5])
para(d,'Specialized work requires separate approved procedures and authorization, including electrical work, confined space entry, hot work, work at height, lifting operations, and chemical spill response.')
heading(d,'2 Before each shift')
bullets(d,[
    'Read the shift handover and identify unusual conditions, active maintenance, and restricted areas.',
    'Confirm clear access to exits, emergency equipment, and marked pedestrian routes.',
    'Check guards visually without entering danger zones. Report damage, leaks, unsecured loads, and abnormal equipment conditions.',
    'Use PPE specified by the task assessment. Keep clothing and hair secured; select gloves only where they do not create an entanglement hazard.',
    'Do not start equipment with an unresolved safety defect. Notify the supervisor and mark its status under the site process.'
])

page(d,'3 Safe production and hazardous energy')
heading(d,'Routine production')
para(d,'Use the current operating instruction for the assigned machine. Keep guards and interlocks effective and keep people clear of moving parts. Never reach into a danger zone or bypass a safety device. Guarding must address points of operation, nip points, rotating parts, and ejected material. [S1]')
bullets(d,[
    'Use designated handling aids for sharp parts and heavy loads. Follow the site lifting assessment and stay outside suspended-load areas.',
    'Keep pedestrians within marked routes. Powered trucks may be used only by site-authorized operators.',
    'Use labeled chemical containers and consult the safety data sheet and task assessment before handling. Report damaged containers; do not mix unknown materials.',
    'Stop the machine safely for unusual noise, vibration, damaged guards, a jam, or a product condition that indicates equipment failure. Report the event.'
])
heading(d,'Energy isolation for servicing')
para(d,'Only trained, authorized personnel may apply the machine-specific energy control procedure. The following is an overview, not an equipment isolation instruction. Emergency stops and control switches do not provide energy isolation. [S2]')
steps(d,[
    'Identify the approved procedure, every energy source, stored-energy hazards, and affected personnel.',
    'Notify affected personnel and shut down in the approved sequence.',
    'Isolate energy sources and apply assigned locks and identification as required by the site program.',
    'Release or restrain stored energy and prevent reaccumulation.',
    'Verify effective isolation using approved methods before work begins; return test controls to a safe state.',
    'Before restart, inspect equipment, clear tools and personnel, and restore safeguards. Each person removes their own lock; exceptions require the employer-approved process. Notify affected workers before energizing.'
])
para(d,'Group work, shift changes, contractors, and temporary energization for testing require dedicated arrangements in the site program. Stop if the procedure does not match the equipment. [S2]')

page(d,'4 Emergency response and reporting')
para(d,'The site emergency action plan must define reporting, alarms, evacuation routes, assembly areas, accountability, and assigned response duties. These arrangements must be explained before personnel enter the plant. [S3]')
table(d,['Situation','Immediate action'],[
    ('Fire or smoke','Raise the alarm and evacuate by a safe route. Report the location from safety. Firefighting is limited to personnel authorized under the site plan.'),
    ('Injury or entrapment','Summon emergency assistance. Stop equipment if safe. Keep others away; do not attempt an untrained rescue or enter a danger zone.'),
    ('Chemical release','Move away, alert others, and report from a safe location. Only trained responders may assess or clean the spill.'),
    ('Evacuation alarm','Leave by the assigned safe exit, go to the assembly point, and report for headcount. Tell the warden about missing people; do not re-enter until authorized.'),
    ('Severe weather or external threat','Follow the specific shelter or evacuation instruction given under the site emergency plan.')],[1.55,5.45])
heading(d,'Site information to complete before issue')
para(d,'Emergency number: __________________  Internal reporting number: __________________')
para(d,'Primary assembly area: __________________  Alternate assembly area: __________________')
para(d,'Alarm meanings and accessible evacuation arrangements: _____________________________')
para(d,'Emergency coordinator and deputy: _____________________________________________')
heading(d,'Hazards incidents and near misses')
para(d,'Report hazards, injuries, and near misses promptly to the supervisor. Protect people first, preserve evidence only when safe, and record the location, time, condition, and immediate controls. The supervisor assigns an owner and due date, verifies the correction, and authorizes restart when controls are effective.')

page(d,'5 Safety inspection and document release')
para(d,'Shift inspection record  |  Date __________  Area __________  Inspector __________')
table(d,['Check','Pass or fail','Action and owner'],[
    ('Exits and pedestrian routes clear','',''),
    ('Guards intact and access controlled','',''),
    ('Work area free of leaks and trip hazards','',''),
    ('Required PPE available and serviceable','',''),
    ('Emergency equipment accessible','',''),
    ('Defects and maintenance status communicated','','')],[3.1,1,2.9])
para(d,'Any failed safety control requires supervisor review before affected work starts. Corrected by __________  Verification __________  Date __________')
heading(d,'Release and training requirements')
para(d,'Before this example becomes a site procedure, the Safety Manager must complete the hazard assessment, verify legal applicability, attach machine-specific procedures and the emergency plan, and approve PPE and training. Supervisors must record worker instruction and demonstrated competence. Review after changes, incidents, or identified gaps, and on the approved review schedule.')
para(d,'Prepared by __________  Safety review __________  Plant approval __________\nEffective date __________  Next review __________  Training record location __________')
refs(d,[
    ('[S1] OSHA 1910.212 General requirements for all machines','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.212'),
    ('[S2] OSHA 1910.147 Control of hazardous energy','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147'),
    ('[S3] OSHA 1910.38 Emergency action plans','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.38')])
d.save(OUT/'Plant_Safety_Procedures.docx')

d = newdoc('Plant Maintenance Manual','MNT 001','Maintenance Manager',
    'Maintenance personnel use this example manual to plan preventive work, record faults, and return equipment to service with documented safety and quality checks. It covers sample conveyors, machining equipment, pneumatic fixtures, and measurement tools.')
heading(d,'1 Maintenance responsibilities')
table(d,['Role','Responsibility'],[
    ('Maintenance Manager','Approve asset plans, priorities, competent personnel, and completed repairs.'),
    ('Technician','Follow asset-specific instructions and isolation procedures; record as-found and as-left conditions.'),
    ('Production Supervisor','Coordinate downtime and confirm operational readiness at handover.'),
    ('Quality Inspector','Approve affected product checks and measurement-system status before product release.')],[1.65,5.35])
heading(d,'2 Equipment records and source instructions')
para(d,'Maintain an asset register with asset ID, location, manufacturer, model, serial number, safety criticality, energy-isolation procedure, manufacturer manual revision, spares list, and maintenance history. Each work order must identify the exact asset and approved task instruction.')
para(d,'Example assets: CV 01 belt conveyor; MC 01 enclosed machining center; PF 01 pneumatic assembly fixture; TG 01 inspection gauge set. These identifiers describe the scenario only.')
heading(d,'Before adopting this manual')
para(d,'Set maintenance intervals using manufacturer requirements, duty cycle, environment, failure history, and risk. The frequencies in this example are planning prompts. They are not manufacturer limits. Enter approved lubricants, quantities, torque values, wear limits, pressures, and test criteria in each asset task sheet before work is authorized.')

page(d,'3 Preventive maintenance planning')
para(d,'Daily checks below are external observations from a safe operating position. Any intrusive inspection, cleaning, adjustment, or servicing must follow the approved isolation and task procedure. Operators report defects; technicians perform authorized maintenance.')
table(d,['Asset and timing','Example task','Evidence and acceptance'],[
    ('All assets\nEach shift','Observe guards, leaks, abnormal sounds, and status indicators.','Checklist complete; no unresolved safety defect.'),
    ('CV 01\nWeekly','During planned isolation, inspect belt, rollers, fasteners, and debris accumulation.','Record condition; compare wear and alignment with approved OEM limits.'),
    ('MC 01\nWeekly','Inspect accessible fluid systems, filtration indicators, and scheduled lubrication points under the task sheet.','Record fluid condition and values against asset limits; use specified materials only.'),
    ('PF 01\nMonthly','Under isolation, inspect hoses, fittings, supports, and fixture wear.','No damage outside approved limits; functional check completed after safe restoration.'),
    ('Safety functions\nApproved interval','Competent person performs documented guard, interlock, and stop-function tests.','Expected safe response demonstrated; record method, results, and tester.'),
    ('TG 01\nBefore use and at due date','Check condition and calibration status; send for scheduled calibration.','No overdue or damaged tool in service; certificate linked to tool ID.')],[1.35,2.85,2.8])
heading(d,'Scheduling and overdue work')
para(d,'The planner assigns a due date, task duration, technician, isolation requirement, and parts. Safety-critical overdue work requires a documented risk decision by Maintenance and Safety; the asset remains unavailable when safe operation cannot be demonstrated. Rescheduling must retain the original due date and approval trail.')
heading(d,'Spares and lubrication control')
para(d,'Use approved part numbers and materials. Record substituted parts only after engineering approval. Store lubricants in labeled closed containers, prevent mixing, and record the type and quantity used. Never substitute a generic torque, grease, or pressure setting for an approved asset value.')

page(d,'4 Fault response and safe work execution')
table(d,['Reported condition','Safe response','Authorized follow up'],[
    ('Conveyor stops or belt tracks poorly','Stop affected use and report. Do not reach in or repeatedly reset.','Isolate; inspect to the approved diagnostic plan; correct cause and verify tracking.'),
    ('Machine vibration or unusual noise','Stop using the asset and identify affected product.','Inspect under the asset procedure; repair and verify against approved limits.'),
    ('Air leak or damaged hose','Keep clear and stop affected use.','Isolate and safely depressurize; replace approved parts and verify integrity.'),
    ('Interlock or stop-function fault','Remove the asset from service.','Competent person diagnoses and validates the safety function. Never bypass for production.'),
    ('Gauge damaged or overdue','Identify and quarantine the gauge.','Quality evaluates prior results, arranges calibration or replacement, and defines containment.')],[1.6,2.55,2.85])
heading(d,'Work order sequence')
steps(d,[
    'Record the fault, asset ID, time, symptoms, and production impact. Maintenance sets priority: unsafe condition means stop use; other work is scheduled by risk and production need.',
    'Review the asset manual, task risk assessment, required permits, parts, tools, and acceptance criteria. Apply SAF 001 and the machine-specific energy control procedure before intrusive work.',
    'Record as-found evidence, perform the approved repair, and document parts and measured settings. Escalate any mismatch between the machine and its instruction.',
    'Inspect the repair, restore guards, and complete the site restoration process. Energized testing requires a separate approved test procedure and controlled access.',
    'Record functional and safety results against defined limits. Production witnesses the operating check; Quality approves first-piece checks when product may be affected. Keep the asset unavailable if any required check fails.'
])

page(d,'5 Maintenance record and handover')
para(d,'Work order __________  Asset __________  Date __________  Technician __________\nFault reported by __________  Priority __________  Downtime start and end __________')
para(d,'Approved task and manual revision __________  Isolation procedure __________\nPermit reference __________  Parts and materials used ______________________________')
table(d,['Record','Result or reference'],[
    ('As-found condition and fault cause',''),
    ('Work performed and approved changes',''),
    ('Measured settings and acceptance limits',''),
    ('Safety and functional test results',''),
    ('First-piece inspection and held product',''),
    ('Open actions owner and due date','')],[2.8,4.2])
para(d,'As-left status: Available / Unavailable  |  Next maintenance due __________________\nTechnician sign off __________  Maintenance approval __________\nProduction handover __________  Quality approval if required __________')
heading(d,'Review and improvement')
para(d,'Review recurring faults, overdue work, and unplanned downtime monthly in this example program. Assign corrective actions to repeat failures and verify results after implementation. Changes to equipment, software, safety functions, or maintenance tasks require engineering review and updated training before use. Store work orders in the asset history under the site retention schedule.')
heading(d,'Site approval')
para(d,'Complete the asset register and approved task sheets before issue. Approver __________\nEffective date __________  Review date __________  Record location __________')
refs(d,[('Safety reference for maintenance energy control','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147')])
d.save(OUT/'Plant_Maintenance_Manual.docx')

d = newdoc('Plant Quality Control Standards','QUA 001','Quality Manager',
    'Production and Quality personnel use these example standards to inspect material, control process output, contain nonconforming product, and authorize shipment. The example product is a simple machined mounting bracket identified as BRK 100.')
heading(d,'1 Authority and product requirements')
para(d,'The Quality Manager approves inspection plans and shipment release. Engineering owns drawings and approved changes. Operators check their work and stop the process for a failed check. Inspectors record results and control product status. Only designated disposition authorities may approve rework, scrap, or a concession.')
para(d,'Use the current approved drawing, purchase specification, and customer requirements. Resolve conflicts before production. The numerical values below are fictional training criteria, not engineering specifications for an actual part. No certification to ISO or another quality standard is implied.')
heading(d,'2 Example bracket acceptance criteria')
table(d,['Characteristic','Example requirement','Method'],[
    ('Part identity','BRK 100; drawing revision A','Traveler and drawing check'),
    ('Material','Grade and condition match approved purchase specification','Supplier evidence and lot identification'),
    ('Overall length','100.00 mm +/- 0.20 mm','Approved calibrated caliper'),
    ('Hole diameter','10.00 mm +/- 0.10 mm','Approved bore or plug gauge method'),
    ('Hole center spacing','60.00 mm +/- 0.15 mm','Approved fixture or coordinate measurement'),
    ('Edges and surface','No visible burrs or cracks at specified inspection conditions; compare to approved visual standard','Visual inspection under defined light and access'),
    ('Pack and label','Correct part revision, quantity, lot ID, and protective packaging','Count and label verification')],[1.35,3.35,2.3])
para(d,'Engineering must define datums, measurement methods, visual conditions, and any critical characteristics before site release. Missing or ambiguous acceptance criteria require a hold and clarification.')

page(d,'3 Inspection plan and measurement control')
para(d,'Example lot definition: one part number and revision produced under one work order with identified material lots and a recorded setup. A material or setup change must remain traceable. This example uses complete inspection for specified features; reduced sampling requires a separately approved risk-based plan.')
table(d,['Stage','Frequency and checks','Record and reaction'],[
    ('Incoming material','Every receipt: identity, quantity, condition, material-lot labels, and required supplier documents.','Receiving record; hold material with missing or mismatched evidence.'),
    ('First piece','Before production release and after setup, tooling, program, material, or relevant maintenance changes: all drawing features.','First-piece report; supervisor and Quality approval before continuing.'),
    ('In process','Every part: length, hole diameter, center spacing, and edge or surface condition using approved methods.','Inspection log; stop and contain on any failure.'),
    ('Final release','Every unit: required feature results complete, identity correct, and packaging acceptable. Every shipment: label, count, and traceability review.','Release record; shipment blocked until required checks and approvals are complete.')],[1.15,3.35,2.5])
heading(d,'Measurement equipment')
para(d,'Use instruments with unique IDs, suitable range and capability, current calibration, and appropriate condition. Record actual numerical results where the method permits. A gauge check uses the approved accept or reject result. Calibration records must support a documented chain to the specified reference and account for measurement uncertainty. Traceability alone does not prove suitability. [Q1]')
para(d,'Quality defines the measurement decision rule and uncertainty treatment before inspection. Do not round a failed result into tolerance or accept a borderline reading without the approved rule. Use specified inspection conditions and trained personnel. Remove damaged or overdue gauges from service and assess product measured since the last known valid check.')

page(d,'4 Nonconforming product and shipment release')
heading(d,'Contain and investigate')
steps(d,[
    'Stop the affected process and notify the supervisor and Quality. Identify the defect, actual result, requirement, instrument, time, and work order.',
    'Label and physically segregate affected units with a hold ID. Block their use and shipment in the inventory system. If the suspect range is uncertain, include the full lot until evidence narrows it.',
    'Trace the issue to material, machine, setup, tool, and prior inspection records. Include work in progress, finished stock, and shipped product when relevant.',
    'Quality and Engineering document disposition: approved rework followed by reinspection, scrap with controlled disposal, supplier return, or authorized concession. Obtain customer approval where required. Operators may not grant a concession.',
    'Correct the process cause and verify the setup with a new first piece. Reinspect affected product to the approved disposition plan before removing the hold.',
    'Assign corrective action, owner, and due date for recurring or significant failures. Check effectiveness against a defined follow-up period or production quantity.'
])
heading(d,'Release criteria')
bullets(d,[
    'Required inspections have passed and records link the product to its drawing revision, material lot, and work order.',
    'Holds are closed or a valid concession identifies the exact units and authorized limits.',
    'Labels, quantities, and packaging meet the order requirements.',
    'The designated Quality release authority signs and dates the release. Production targets do not override acceptance criteria.'
])
heading(d,'Example containment decision')
para(d,'A length result of 100.28 mm fails the illustrative upper limit of 100.20 mm. Stop the process and place the suspect product on hold. Quality defines the affected range from traceable evidence, approves investigation and disposition, and requires a passing first piece before process restart.')

page(d,'5 Inspection records and quality review')
para(d,'Work order __________  Part and revision __________  Material lot __________\nMachine and setup __________  Inspector __________  Date and time __________\nInstrument IDs and calibration due dates _________________________________________')
table(d,['Unit ID','Length mm','Hole mm','Spacing mm','Visual','Result'],[
    ('Example 001','100.06','10.03','60.04','Pass','Pass'),
    ('Example 002','100.28','10.01','60.00','Pass','HOLD'),
    ('','','','','',''),
    ('','','','','',''),
    ('','','','','','')],[1.05,1.15,1.15,1.25,1.2,1.2])
para(d,'Example entries are training data. Use actual results and the approved decision rule in production.\nQuantity inspected __________  Accepted __________  Held __________  Hold ID __________\nDisposition reference __________  Release authority __________  Release date __________')
heading(d,'Records and performance review')
para(d,'Retain receiving records, inspection results, calibration evidence, nonconformance reports, concessions, and release records under the approved retention schedule. Keep originals readable, controlled, and retrievable by lot. Corrections must preserve the original entry and identify who changed it, when, and why.')
para(d,'In this example program, Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions monthly. Define calculation methods and targets at site approval. Trend findings trigger action; a favorable average never authorizes shipment of a failed unit.')
heading(d,'Site approval')
para(d,'Approve actual drawings, characteristic risks, methods, decision rules, inspection frequencies, and retention periods before issue. Engineering __________  Quality __________\nEffective date __________  Next review __________  Record location __________')
refs(d,[('[Q1] NIST Metrological Traceability Frequently Asked Questions and Policy','https://www.nist.gov/metrology/metrological-traceability')])
d.save(OUT/'Plant_Quality_Control_Standards.docx')

for f in OUT.glob('*.docx'):
    doc=Document(f)
    words=sum(len(p.text.split()) for p in doc.paragraphs)+sum(len(c.text.split()) for t in doc.tables for row in t.rows for c in row.cells)
    print(f'{f.name}: {words} words, {len(doc.tables)} tables, {f.stat().st_size} bytes')
