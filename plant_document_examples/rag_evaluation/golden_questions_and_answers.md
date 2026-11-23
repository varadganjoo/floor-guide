# Plant RAG golden questions and answers

Version 1.0. Agent-authored starter set grounded only in the three example plant documents.

## PLANT-RAG-001 safety

**Question:** Who approves task risk assessments, PPE selection, emergency arrangements, and safety training?

**Reference answer:** The Safety Manager approves task risk assessments, PPE selection, emergency arrangements, and training.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Identify the Safety Manager as the approving role.

**Do not claim:**
- Assign this approval authority solely to operators.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, 1 Responsibilities and work boundaries (SAF001-009): Role: Safety Manager | Responsibility: Approve task risk assessments, PPE selection, emergency arrangements, and training.

## PLANT-RAG-002 safety

**Question:** Before a shift starts, what should I check in the handover and along the access routes?

**Reference answer:** Read the handover for unusual conditions, active maintenance, and restricted areas. Confirm clear access to exits, emergency equipment, and marked pedestrian routes.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Review unusual conditions, active maintenance, and restricted areas.
- Confirm clear exits, emergency-equipment access, and marked pedestrian routes.

**Do not claim:**
- Begin without reviewing handover conditions.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, 2 Before each shift (SAF001-014): Read the shift handover and identify unusual conditions, active maintenance, and restricted areas.
- Plant_Safety_Procedures.docx, page 1, 2 Before each shift (SAF001-015): Confirm clear access to exits, emergency equipment, and marked pedestrian routes.

## PLANT-RAG-003 safety

**Question:** A machine has a safety defect that has not been resolved. Can I start it and report the defect later?

**Reference answer:** No. Do not start equipment with an unresolved safety defect. Notify the supervisor and mark the equipment status through the site process.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Do not start the equipment.
- Notify the supervisor and mark its status under the site process.

**Do not claim:**
- Allow operation until the next maintenance window.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, 2 Before each shift (SAF001-018): Do not start equipment with an unresolved safety defect. Notify the supervisor and mark its status under the site process.

## PLANT-RAG-004 safety

**Question:** Are gloves always required around rotating equipment?

**Reference answer:** The document does not impose a blanket glove rule. Use the PPE specified by the task assessment, and select gloves only where they do not create an entanglement hazard. Keep hair and clothing secured.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- PPE selection follows the task assessment.
- Gloves must not introduce an entanglement hazard.

**Do not claim:**
- Gloves are always required regardless of entanglement risk.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, 2 Before each shift (SAF001-017): Use PPE specified by the task assessment. Keep clothing and hair secured; select gloves only where they do not create an entanglement hazard.

## PLANT-RAG-005 safety

**Question:** What information should workers consult before handling a chemical?

**Reference answer:** Consult the safety data sheet and task assessment before handling a chemical. Use labeled containers, report damaged containers, and do not mix unknown materials.

**Type:** procedure | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Consult the safety data sheet.
- Consult the task assessment before handling.

**Do not claim:**
- Unknown materials may be mixed to identify them.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 2, Routine production (SAF001-024): Use labeled chemical containers and consult the safety data sheet and task assessment before handling. Report damaged containers; do not mix unknown materials.

## PLANT-RAG-006 safety

**Question:** Does pressing an emergency stop provide energy isolation for servicing?

**Reference answer:** No. Emergency stops and control switches do not provide energy isolation. Only trained, authorized personnel may apply the machine-specific energy control procedure.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- An emergency stop is not energy isolation.
- Use the machine-specific procedure through trained, authorized personnel.

**Do not claim:**
- An emergency stop alone makes servicing safe.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-027): Only trained, authorized personnel may apply the machine-specific energy control procedure. The following is an overview, not an equipment isolation instruction. Emergency stops and control switches do not provide energy isolation. [S2]

## PLANT-RAG-007 safety

**Question:** After stored energy is released or restrained, what must happen before servicing begins?

**Reference answer:** Prevent stored energy from reaccumulating, then verify effective isolation using approved methods before work begins. Return test controls to a safe state. This is part of the authorized machine-specific procedure.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Prevent stored-energy reaccumulation.
- Verify isolation by approved methods before work.
- Return test controls to a safe state.

**Do not claim:**
- Proceed based only on the machine appearing stopped.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-031): 4. Release or restrain stored energy and prevent reaccumulation.
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-032): 5. Verify effective isolation using approved methods before work begins; return test controls to a safe state.
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-027): Only trained, authorized personnel may apply the machine-specific energy control procedure. The following is an overview, not an equipment isolation instruction. Emergency stops and control switches do not provide energy isolation. [S2]

## PLANT-RAG-008 safety

**Question:** What checks and notifications are required before restarting equipment after isolation?

**Reference answer:** Inspect the equipment, clear tools and personnel, and restore safeguards. Each person removes their own lock unless an employer-approved exception applies. Notify affected workers before energizing.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Inspect equipment, clear tools and personnel, and restore safeguards.
- Each person removes their own lock, subject to the employer-approved exception process.
- Notify affected workers before energizing.

**Do not claim:**
- Any available coworker may remove another person's lock without the approved exception process.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-033): 6. Before restart, inspect equipment, clear tools and personnel, and restore safeguards. Each person removes their own lock; exceptions require the employer-approved process. Notify affected workers before energizing.

## PLANT-RAG-009 safety

**Question:** There is a chemical spill in my work area. What does the safety procedure tell an ordinary worker to do?

**Reference answer:** Move away, alert others, and report from a safe location. Only trained responders may assess or clean the spill.

**Type:** scenario | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Move away, alert others, and report from safety.
- Assessment and cleanup are limited to trained responders.

**Do not claim:**
- An untrained worker should clean the spill immediately.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 3, 4 Emergency response and reporting (SAF001-039): Situation: Chemical release | Immediate action: Move away, alert others, and report from a safe location. Only trained responders may assess or clean the spill.

## PLANT-RAG-010 safety

**Question:** When the evacuation alarm sounds, where do I go and how are missing people handled?

**Reference answer:** Leave by the assigned safe exit, go to the assembly point, and report for headcount. Tell the warden about missing people and do not re-enter until authorized.

**Type:** procedure | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Use the assigned safe exit and report at the assembly point for headcount.
- Report missing people to the warden.
- Do not re-enter until authorized.

**Do not claim:**
- Re-enter independently to search for missing people.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 3, 4 Emergency response and reporting (SAF001-040): Situation: Evacuation alarm | Immediate action: Leave by the assigned safe exit, go to the assembly point, and report for headcount. Tell the warden about missing people; do not re-enter until authorized.

## PLANT-RAG-011 safety

**Question:** What information should be recorded when reporting a hazard, injury, or near miss?

**Reference answer:** Promptly report to the supervisor and record the location, time, condition, and immediate controls. Protect people first and preserve evidence only when it is safe.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Report promptly to the supervisor.
- Record location, time, condition, and immediate controls.
- People take priority and evidence is preserved only when safe.

**Do not claim:**
- Evidence preservation takes priority over protecting people.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 3, Hazards incidents and near misses (SAF001-048): Report hazards, injuries, and near misses promptly to the supervisor. Protect people first, preserve evidence only when safe, and record the location, time, condition, and immediate controls. The supervisor assigns an owner and due date, verifies the correction, and authorizes restart when controls are effective.

## PLANT-RAG-012 safety

**Question:** What must be completed before the example safety document becomes a site procedure?

**Reference answer:** The Safety Manager must complete the hazard assessment, verify legal applicability, attach machine-specific procedures and the emergency plan, and approve PPE and training. Supervisors must record instruction and demonstrated worker competence.

**Type:** procedure | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Complete the hazard assessment and verify legal applicability.
- Attach machine-specific procedures and the emergency plan.
- Approve PPE and training.
- Record instruction and demonstrated competence.

**Do not claim:**
- The example is already approved for operational use.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 4, Release and training requirements (SAF001-059): Before this example becomes a site procedure, the Safety Manager must complete the hazard assessment, verify legal applicability, attach machine-specific procedures and the emergency plan, and approve PPE and training. Supervisors must record worker instruction and demonstrated competence. Review after changes, incidents, or identified gaps, and on the approved review schedule.
- Plant_Safety_Procedures.docx, page 1, Document introduction (SAF001-004): EXAMPLE ONLY - NOT RELEASED FOR OPERATION

## PLANT-RAG-013 maintenance

**Question:** What equipment do the example asset IDs CV 01, MC 01, PF 01, and TG 01 represent?

**Reference answer:** CV 01 is the belt conveyor, MC 01 is the enclosed machining center, PF 01 is the pneumatic assembly fixture, and TG 01 is the inspection gauge set.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- CV 01 means belt conveyor.
- MC 01 means enclosed machining center.
- PF 01 means pneumatic assembly fixture.
- TG 01 means inspection gauge set.

**Do not claim:**
- Swap the fixture and gauge asset identifiers.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 1, 2 Equipment records and source instructions (MNT001-014): Example assets: CV 01 belt conveyor; MC 01 enclosed machining center; PF 01 pneumatic assembly fixture; TG 01 inspection gauge set. These identifiers describe the scenario only.

## PLANT-RAG-014 maintenance

**Question:** Which information belongs in an equipment asset register?

**Reference answer:** Record asset ID, location, manufacturer, model, serial number, safety criticality, energy-isolation procedure, manufacturer manual revision, spares list, and maintenance history.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Include asset ID, location, manufacturer, model, and serial number.
- Include safety criticality and the energy-isolation procedure.
- Include manufacturer manual revision, spares list, and maintenance history.

**Do not claim:**
- An asset name alone is a complete register.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 1, 2 Equipment records and source instructions (MNT001-013): Maintain an asset register with asset ID, location, manufacturer, model, serial number, safety criticality, energy-isolation procedure, manufacturer manual revision, spares list, and maintenance history. Each work order must identify the exact asset and approved task instruction.

## PLANT-RAG-015 maintenance

**Question:** Who approves asset plans, maintenance priorities, competent personnel, and completed repairs?

**Reference answer:** The Maintenance Manager approves asset plans, priorities, competent personnel, and completed repairs.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Identify the Maintenance Manager.

**Do not claim:**
- Assign completed-repair approval solely to a warehouse clerk.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 1, 1 Maintenance responsibilities (MNT001-008): Role: Maintenance Manager | Responsibility: Approve asset plans, priorities, competent personnel, and completed repairs.

## PLANT-RAG-016 maintenance

**Question:** What factors should determine actual maintenance intervals, and are the example intervals manufacturer limits?

**Reference answer:** Use manufacturer requirements, duty cycle, environment, failure history, and risk to set intervals. The example frequencies are planning prompts, not manufacturer limits.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Use manufacturer requirements, duty cycle, environment, failure history, and risk.
- Example frequencies are planning prompts rather than OEM limits.

**Do not claim:**
- The example weekly and monthly frequencies are certified manufacturer limits.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 1, Before adopting this manual (MNT001-016): Set maintenance intervals using manufacturer requirements, duty cycle, environment, failure history, and risk. The frequencies in this example are planning prompts. They are not manufacturer limits. Enter approved lubricants, quantities, torque values, wear limits, pressures, and test criteria in each asset task sheet before work is authorized.

## PLANT-RAG-017 maintenance

**Question:** In the example plan, how often is CV 01 inspected, and what does the inspection cover?

**Reference answer:** The example plan lists a weekly inspection during planned isolation of the belt, rollers, fasteners, and debris accumulation. Record the condition and compare wear and alignment with approved OEM limits.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Weekly is the example frequency.
- Perform during planned isolation; inspect belt, rollers, fasteners, and debris accumulation.
- Record condition and compare wear and alignment with approved OEM limits.

**Do not claim:**
- Inspect by reaching into a running conveyor.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 2, 3 Preventive maintenance planning (MNT001-020): Asset and timing: CV 01 Weekly | Example task: During planned isolation, inspect belt, rollers, fasteners, and debris accumulation. | Evidence and acceptance: Record condition; compare wear and alignment with approved OEM limits.

## PLANT-RAG-018 maintenance

**Question:** What is the example monthly task for PF 01, and what evidence is required?

**Reference answer:** Under isolation, inspect hoses, fittings, supports, and fixture wear. Confirm there is no damage outside approved limits and complete a functional check after safe restoration.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- Monthly PF 01 inspection covers hoses, fittings, supports, and fixture wear under isolation.
- Check damage against approved limits and complete a functional check after safe restoration.

**Do not claim:**
- Pressurized hose disconnection is an approved inspection method.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 2, 3 Preventive maintenance planning (MNT001-022): Asset and timing: PF 01 Monthly | Example task: Under isolation, inspect hoses, fittings, supports, and fixture wear. | Evidence and acceptance: No damage outside approved limits; functional check completed after safe restoration.

## PLANT-RAG-019 maintenance

**Question:** What should happen when safety-critical maintenance becomes overdue?

**Reference answer:** Maintenance and Safety must make a documented risk decision. Keep the asset unavailable if safe operation cannot be demonstrated. If the work is rescheduled, retain the original due date and approval trail.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- A documented risk decision by Maintenance and Safety is required.
- Asset stays unavailable if safe operation cannot be demonstrated.
- Retain original due date and approval trail when rescheduling.

**Do not claim:**
- Automatically extend the due date without recording approval.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 2, Scheduling and overdue work (MNT001-026): The planner assigns a due date, task duration, technician, isolation requirement, and parts. Safety-critical overdue work requires a documented risk decision by Maintenance and Safety; the asset remains unavailable when safe operation cannot be demonstrated. Rescheduling must retain the original due date and approval trail.

## PLANT-RAG-020 maintenance

**Question:** Can a technician substitute any available spare part or lubricant?

**Reference answer:** No. Use approved part numbers and materials; part substitutions require engineering approval. Keep lubricants labeled and closed, prevent mixing, and record their type and quantity. Do not replace an approved asset setting with a generic torque, grease, or pressure value.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Use approved parts and materials; engineering approval is needed for substitutions.
- Control lubricant identity and mixing and record type and quantity.
- Do not substitute generic settings for approved asset values.

**Do not claim:**
- An apparently similar spare or grease may be substituted without approval.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 2, Spares and lubrication control (MNT001-028): Use approved part numbers and materials. Record substituted parts only after engineering approval. Store lubricants in labeled closed containers, prevent mixing, and record the type and quantity used. Never substitute a generic torque, grease, or pressure setting for an approved asset value.

## PLANT-RAG-021 maintenance

**Question:** The conveyor keeps stopping and its belt is tracking poorly. Should I repeatedly reset it?

**Reference answer:** No. Stop affected use and report the fault; do not reach in or repeatedly reset it. Authorized follow-up is to isolate, inspect under the approved diagnostic plan, correct the cause, and verify tracking.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Stop affected use and report.
- Do not reach in or repeatedly reset.
- Isolate and use the approved diagnostic plan; correct the cause and verify tracking.

**Do not claim:**
- Repeated resets are an acceptable way to continue production.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 3, 4 Fault response and safe work execution (MNT001-030): Reported condition: Conveyor stops or belt tracks poorly | Safe response: Stop affected use and report. Do not reach in or repeatedly reset. | Authorized follow up: Isolate; inspect to the approved diagnostic plan; correct cause and verify tracking.

## PLANT-RAG-022 maintenance

**Question:** An interlock or stop function has failed. May production continue with that function bypassed?

**Reference answer:** No. Remove the asset from service. A competent person must diagnose and validate the safety function. Never bypass it for production.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Remove the asset from service.
- A competent person diagnoses and validates the function.
- Do not bypass for production.

**Do not claim:**
- A temporary production bypass is allowed to meet a target.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 3, 4 Fault response and safe work execution (MNT001-033): Reported condition: Interlock or stop-function fault | Safe response: Remove the asset from service. | Authorized follow up: Competent person diagnoses and validates the safety function. Never bypass for production.

## PLANT-RAG-023 maintenance

**Question:** Who witnesses the operating check after a repair, and when does Quality approve first-piece checks?

**Reference answer:** Production witnesses the operating check. Quality approves first-piece checks when product may be affected. Record functional and safety results against defined limits, and keep the asset unavailable if any required check fails.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Production witnesses the operating check.
- Quality approves first-piece checks when product may be affected.
- Record results against limits and keep the asset unavailable on a required-check failure.

**Do not claim:**
- A repaired asset can be released despite a failed required test.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 3, Work order sequence (MNT001-040): 5. Record functional and safety results against defined limits. Production witnesses the operating check; Quality approves first-piece checks when product may be affected. Keep the asset unavailable if any required check fails.

## PLANT-RAG-024 maintenance

**Question:** How often does the example maintenance program review recurring faults, and what changes need engineering review?

**Reference answer:** Review recurring faults, overdue work, and unplanned downtime monthly. Changes to equipment, software, safety functions, or maintenance tasks require engineering review and updated training before use.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- The example review is monthly and covers recurring faults, overdue work, and unplanned downtime.
- Equipment, software, safety-function, and task changes require engineering review and updated training before use.

**Do not claim:**
- Software changes are exempt from engineering review.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 4, Review and improvement (MNT001-052): Review recurring faults, overdue work, and unplanned downtime monthly in this example program. Assign corrective actions to repeat failures and verify results after implementation. Changes to equipment, software, safety functions, or maintenance tasks require engineering review and updated training before use. Store work orders in the asset history under the site retention schedule.

## PLANT-RAG-025 quality

**Question:** What is the example product part number and drawing revision?

**Reference answer:** The example product is BRK 100, drawing revision A.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- BRK 100.
- Drawing revision A.

**Do not claim:**
- Drawing revision B.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 1, 2 Example bracket acceptance criteria (QUA001-011): Characteristic: Part identity | Example requirement: BRK 100; drawing revision A | Method: Traveler and drawing check

## PLANT-RAG-026 quality

**Question:** What is the illustrative overall-length tolerance for BRK 100, and which measurement method is listed?

**Reference answer:** The illustrative overall length is 100.00 mm +/- 0.20 mm, measured with an approved calibrated caliper.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- 100.00 mm +/- 0.20 mm.
- Approved calibrated caliper.

**Do not claim:**
- Overall-length tolerance is +/- 0.10 mm.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 1, 2 Example bracket acceptance criteria (QUA001-013): Characteristic: Overall length | Example requirement: 100.00 mm +/- 0.20 mm | Method: Approved calibrated caliper

## PLANT-RAG-027 quality

**Question:** What example limits and measurement method apply to the bracket hole diameter?

**Reference answer:** The illustrative hole diameter is 10.00 mm +/- 0.10 mm. Use the approved bore or plug gauge method.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- 10.00 mm +/- 0.10 mm.
- Approved bore or plug gauge method.

**Do not claim:**
- Use the center-spacing tolerance as the diameter tolerance.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 1, 2 Example bracket acceptance criteria (QUA001-014): Characteristic: Hole diameter | Example requirement: 10.00 mm +/- 0.10 mm | Method: Approved bore or plug gauge method

## PLANT-RAG-028 quality

**Question:** What example specification and method apply to hole center spacing?

**Reference answer:** The illustrative center spacing is 60.00 mm +/- 0.15 mm. Use an approved fixture or coordinate measurement method.

**Type:** lookup | **Difficulty:** easy | **Answerability:** answerable

**Required facts:**
- 60.00 mm +/- 0.15 mm.
- Approved fixture or coordinate measurement method.

**Do not claim:**
- Spacing is 60.00 mm +/- 0.20 mm.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 1, 2 Example bracket acceptance criteria (QUA001-015): Characteristic: Hole center spacing | Example requirement: 60.00 mm +/- 0.15 mm | Method: Approved fixture or coordinate measurement

## PLANT-RAG-029 quality

**Question:** Using the example standards, what should happen to a bracket whose measured length is 100.28 mm?

**Reference answer:** It fails the illustrative 100.20 mm upper limit. Stop the process and place suspect product on hold. Quality defines the affected range from traceable evidence, approves investigation and disposition, and requires a passing first piece before process restart.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- 100.28 mm exceeds the illustrative 100.20 mm upper limit.
- Stop the process and hold suspect product.
- Quality defines the range and disposition; require a passing first piece before restart.

**Do not claim:**
- Round the result down and accept the part.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 3, Example containment decision (QUA001-042): A length result of 100.28 mm fails the illustrative upper limit of 100.20 mm. Stop the process and place the suspect product on hold. Quality defines the affected range from traceable evidence, approves investigation and disposition, and requires a passing first piece before process restart.

## PLANT-RAG-030 quality

**Question:** When is first-piece inspection required, what does it cover, and who approves continuation?

**Reference answer:** Inspect all drawing features before production release and after setup, tooling, program, material, or relevant maintenance changes. Record a first-piece report and obtain supervisor and Quality approval before continuing.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Before release and after setup, tooling, program, material, or relevant maintenance changes.
- Inspect all drawing features and record a first-piece report.
- Supervisor and Quality approve continuation.

**Do not claim:**
- First-piece inspection is needed only on the first day a machine is installed.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 2, 3 Inspection plan and measurement control (QUA001-022): Stage: First piece | Frequency and checks: Before production release and after setup, tooling, program, material, or relevant maintenance changes: all drawing features. | Record and reaction: First-piece report; supervisor and Quality approval before continuing.

## PLANT-RAG-031 quality

**Question:** Does the example in-process plan inspect a sample or every part, and which characteristics are checked?

**Reference answer:** It checks every part for length, hole diameter, center spacing, and edge or surface condition using approved methods. Record an inspection log and stop and contain on any failure.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Every part is checked.
- Check length, hole diameter, center spacing, and edge or surface condition.
- Record results and stop and contain on any failure.

**Do not claim:**
- Only one part per lot needs inspection under this example plan.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 2, 3 Inspection plan and measurement control (QUA001-023): Stage: In process | Frequency and checks: Every part: length, hole diameter, center spacing, and edge or surface condition using approved methods. | Record and reaction: Inspection log; stop and contain on any failure.

## PLANT-RAG-032 quality

**Question:** What happens to incoming material if required supplier evidence is missing or mismatched?

**Reference answer:** Place the material on hold and record the receipt. Each receipt is checked for identity, quantity, condition, material-lot labels, and required supplier documents.

**Type:** procedure | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Hold material with missing or mismatched evidence.
- Check every receipt for identity, quantity, condition, lot labels, and required supplier documents.

**Do not claim:**
- Use the material while waiting for the required evidence.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 2, 3 Inspection plan and measurement control (QUA001-021): Stage: Incoming material | Frequency and checks: Every receipt: identity, quantity, condition, material-lot labels, and required supplier documents. | Record and reaction: Receiving record; hold material with missing or mismatched evidence.

## PLANT-RAG-033 quality

**Question:** Does calibration traceability alone prove a measurement tool is suitable for the inspection?

**Reference answer:** No. Traceability alone does not prove suitability. The instrument must have a unique ID, suitable range and capability, current calibration, and appropriate condition. Calibration evidence must support the reference chain and account for measurement uncertainty.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Traceability alone does not prove suitability.
- Check unique ID, range and capability, calibration currency, and condition.
- Support the calibration chain and account for uncertainty.

**Do not claim:**
- Any traceable tool is automatically suitable for any tolerance.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 2, Measurement equipment (QUA001-026): Use instruments with unique IDs, suitable range and capability, current calibration, and appropriate condition. Record actual numerical results where the method permits. A gauge check uses the approved accept or reject result. Calibration records must support a documented chain to the specified reference and account for measurement uncertainty. Traceability alone does not prove suitability. [Q1]

## PLANT-RAG-034 quality

**Question:** A result is just outside tolerance. May an inspector round it into tolerance?

**Reference answer:** No. Quality defines the decision rule and uncertainty treatment before inspection. Do not round a failed result into tolerance or accept a borderline reading without the approved rule.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Do not round a failed result into tolerance.
- Use the Quality-defined decision rule and uncertainty treatment established before inspection.

**Do not claim:**
- Rounding is allowed whenever the result is close to the limit.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 2, Measurement equipment (QUA001-027): Quality defines the measurement decision rule and uncertainty treatment before inspection. Do not round a failed result into tolerance or accept a borderline reading without the approved rule. Use specified inspection conditions and trained personnel. Remove damaged or overdue gauges from service and assess product measured since the last known valid check.

## PLANT-RAG-035 quality

**Question:** We found a defect but cannot tell which units are affected. How much product goes on hold?

**Reference answer:** Include the full lot until evidence narrows the suspect range. Label and physically segregate affected units with a hold ID and block their use and shipment in the inventory system.

**Type:** scenario | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Hold the full lot until evidence narrows the range.
- Use a hold ID, physically segregate, and block use and shipment.

**Do not claim:**
- Hold only the visibly failed unit when the suspect range is unknown.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 3, Contain and investigate (QUA001-031): 2. Label and physically segregate affected units with a hold ID. Block their use and shipment in the inventory system. If the suspect range is uncertain, include the full lot until evidence narrows it.

## PLANT-RAG-036 quality

**Question:** Can an operator grant a concession for a nonconforming bracket, and what dispositions are listed?

**Reference answer:** Operators may not grant a concession. Quality and Engineering document disposition: approved rework with reinspection, controlled scrap, supplier return, or an authorized concession. Obtain customer approval where required.

**Type:** lookup | **Difficulty:** medium | **Answerability:** answerable

**Required facts:**
- Operators may not grant concessions.
- Quality and Engineering document approved rework plus reinspection, controlled scrap, supplier return, or authorized concession.
- Get customer approval where required.

**Do not claim:**
- An operator can grant a concession solely to meet production targets.

**Source evidence**:
- Plant_Quality_Control_Standards.docx, page 3, Contain and investigate (QUA001-033): 4. Quality and Engineering document disposition: approved rework followed by reinspection, scrap with controlled disposal, supplier return, or authorized concession. Obtain customer approval where required. Operators may not grant a concession.

## PLANT-RAG-037 cross_document

**Question:** A machining-center repair may have affected bracket dimensions. What maintenance checks and quality approvals are needed before production continues and product ships?

**Reference answer:** Maintenance records passing functional and safety results against defined limits, with Production witnessing the operating check. Relevant maintenance changes require inspection of all first-piece drawing features and supervisor and Quality approval before continuation. Shipment remains blocked until required checks and approvals are complete.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Record functional and safety results against limits and have Production witness the operating check.
- Inspect all first-piece drawing features after relevant maintenance and obtain supervisor and Quality approval.
- Block shipment until required checks and approvals are complete.

**Do not claim:**
- Repair completion alone authorizes shipment.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 3, Work order sequence (MNT001-040): 5. Record functional and safety results against defined limits. Production witnesses the operating check; Quality approves first-piece checks when product may be affected. Keep the asset unavailable if any required check fails.
- Plant_Quality_Control_Standards.docx, page 2, 3 Inspection plan and measurement control (QUA001-022): Stage: First piece | Frequency and checks: Before production release and after setup, tooling, program, material, or relevant maintenance changes: all drawing features. | Record and reaction: First-piece report; supervisor and Quality approval before continuing.
- Plant_Quality_Control_Standards.docx, page 2, 3 Inspection plan and measurement control (QUA001-024): Stage: Final release | Frequency and checks: Every unit: required feature results complete, identity correct, and packaging acceptable. Every shipment: label, count, and traceability review. | Record and reaction: Release record; shipment blocked until required checks and approvals are complete.

## PLANT-RAG-038 cross_document

**Question:** An inspection gauge is found overdue after it was used on parts. What equipment action and product review do the manuals require?

**Reference answer:** Identify and quarantine the gauge. Quality evaluates prior results, arranges calibration or replacement, and defines containment. Assess product measured since the last known valid check; do not keep using the overdue gauge.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Identify and quarantine the gauge.
- Quality evaluates prior results, arranges calibration or replacement, and defines containment.
- Assess product measured since the last known valid check.

**Do not claim:**
- Continue using the overdue gauge because prior parts appeared acceptable.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 3, 4 Fault response and safe work execution (MNT001-034): Reported condition: Gauge damaged or overdue | Safe response: Identify and quarantine the gauge. | Authorized follow up: Quality evaluates prior results, arranges calibration or replacement, and defines containment.
- Plant_Quality_Control_Standards.docx, page 2, Measurement equipment (QUA001-027): Quality defines the measurement decision rule and uncertainty treatment before inspection. Do not round a failed result into tolerance or accept a borderline reading without the approved rule. Use specified inspection conditions and trained personnel. Remove damaged or overdue gauges from service and assess product measured since the last known valid check.

## PLANT-RAG-039 cross_document

**Question:** Unusual vibration starts during machining. What immediate production, maintenance, and product actions are described?

**Reference answer:** Stop the machine safely and report the event. Stop using the asset and identify affected product. Maintenance inspects under the approved asset procedure, repairs, and verifies against approved limits. If a product defect is found, stop the affected process and notify the supervisor and Quality, recording the required defect details.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Stop safely and report the vibration.
- Identify affected product and inspect, repair, and verify the asset under the approved procedure.
- If product is defective, notify the supervisor and Quality and record the defect details.

**Do not claim:**
- Continue machining until the vibration causes a confirmed failure.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 2, Routine production (SAF001-025): Stop the machine safely for unusual noise, vibration, damaged guards, a jam, or a product condition that indicates equipment failure. Report the event.
- Plant_Maintenance_Manual.docx, page 3, 4 Fault response and safe work execution (MNT001-031): Reported condition: Machine vibration or unusual noise | Safe response: Stop using the asset and identify affected product. | Authorized follow up: Inspect under the asset procedure; repair and verify against approved limits.
- Plant_Quality_Control_Standards.docx, page 3, Contain and investigate (QUA001-030): 1. Stop the affected process and notify the supervisor and Quality. Identify the defect, actual result, requirement, instrument, time, and work order.

## PLANT-RAG-040 cross_document

**Question:** Can an operator clean inside equipment during a daily maintenance check if the emergency stop is pressed?

**Reference answer:** No. Daily checks are external observations from a safe operating position. Intrusive cleaning requires the approved isolation and task procedure. An emergency stop does not provide energy isolation; only trained, authorized personnel may apply the machine-specific energy control procedure.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Daily checks are external observations.
- Intrusive cleaning requires approved isolation and task procedures.
- An emergency stop is not isolation; trained, authorized personnel apply the machine-specific procedure.

**Do not claim:**
- Pressing emergency stop authorizes reaching inside for cleaning.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 2, 3 Preventive maintenance planning (MNT001-018): Daily checks below are external observations from a safe operating position. Any intrusive inspection, cleaning, adjustment, or servicing must follow the approved isolation and task procedure. Operators report defects; technicians perform authorized maintenance.
- Plant_Safety_Procedures.docx, page 2, Energy isolation for servicing (SAF001-027): Only trained, authorized personnel may apply the machine-specific energy control procedure. The following is an overview, not an equipment isolation instruction. Emergency stops and control switches do not provide energy isolation. [S2]

## PLANT-RAG-041 cross_document

**Question:** A guard interlock fault is found during production. Can the machine be used temporarily while repairs are arranged?

**Reference answer:** No. The safety procedure prohibits starting equipment with an unresolved safety defect and prohibits bypassing safety devices. The maintenance manual requires an asset with an interlock or stop-function fault to be removed from service and diagnosed and validated by a competent person, without a production bypass.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Do not start equipment with an unresolved safety defect or bypass a safety device.
- Remove an asset with interlock or stop-function failure from service.
- A competent person must diagnose and validate the failed safety function.

**Do not claim:**
- A temporary production bypass is allowed.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, 2 Before each shift (SAF001-018): Do not start equipment with an unresolved safety defect. Notify the supervisor and mark its status under the site process.
- Plant_Safety_Procedures.docx, page 2, Routine production (SAF001-021): Use the current operating instruction for the assigned machine. Keep guards and interlocks effective and keep people clear of moving parts. Never reach into a danger zone or bypass a safety device. Guarding must address points of operation, nip points, rotating parts, and ejected material. [S1]
- Plant_Maintenance_Manual.docx, page 3, 4 Fault response and safe work execution (MNT001-033): Reported condition: Interlock or stop-function fault | Safe response: Remove the asset from service. | Authorized follow up: Competent person diagnoses and validates the safety function. Never bypass for production.

## PLANT-RAG-042 cross_document

**Question:** Across the maintenance and quality documents, what does each example program review monthly?

**Reference answer:** Maintenance reviews recurring faults, overdue work, and unplanned downtime. Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions. These monthly frequencies are features of the example programs.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Maintenance reviews recurring faults, overdue work, and unplanned downtime monthly.
- Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions monthly.
- Describe these as example-program frequencies.

**Do not claim:**
- These frequencies are stated as universal legal requirements.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 4, Review and improvement (MNT001-052): Review recurring faults, overdue work, and unplanned downtime monthly in this example program. Assign corrective actions to repeat failures and verify results after implementation. Changes to equipment, software, safety functions, or maintenance tasks require engineering review and updated training before use. Store work orders in the asset history under the site retention schedule.
- Plant_Quality_Control_Standards.docx, page 4, Records and performance review (QUA001-050): In this example program, Quality reviews first-pass yield, defect rates, repeat defects, customer returns, and overdue corrective actions monthly. Define calculation methods and targets at site approval. Trend findings trigger action; a favorable average never authorizes shipment of a failed unit.

## PLANT-RAG-043 cross_document

**Question:** Do these three documents authorize immediate plant operation or prove certification to a quality standard?

**Reference answer:** No. All three are examples marked not released for operation. Their scenario is for training and demonstration and does not establish compliance or equipment authorization. The quality document explicitly states that no ISO or other quality-standard certification is implied.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- All three are examples and not released for operation.
- They do not establish compliance or equipment authorization.
- No ISO or other quality-standard certification is implied.

**Do not claim:**
- The plant is ISO certified because these documents exist.

**Source evidence**:
- Plant_Safety_Procedures.docx, page 1, Document introduction (SAF001-004): EXAMPLE ONLY - NOT RELEASED FOR OPERATION
- Plant_Maintenance_Manual.docx, page 1, Document introduction (MNT001-004): EXAMPLE ONLY - NOT RELEASED FOR OPERATION
- Plant_Quality_Control_Standards.docx, page 1, Document introduction (QUA001-004): EXAMPLE ONLY - NOT RELEASED FOR OPERATION
- Plant_Safety_Procedures.docx, page 1, Document introduction (SAF001-006): Plant scenario: a fictional facility receiving metal blanks, machining and deburring brackets, assembling components, and packing finished goods. This document supports training and demonstration. It does not establish regulatory compliance or equipment authorization.
- Plant_Maintenance_Manual.docx, page 1, Document introduction (MNT001-006): Plant scenario: a fictional facility receiving metal blanks, machining and deburring brackets, assembling components, and packing finished goods. This document supports training and demonstration. It does not establish regulatory compliance or equipment authorization.
- Plant_Quality_Control_Standards.docx, page 1, Document introduction (QUA001-006): Plant scenario: a fictional facility receiving metal blanks, machining and deburring brackets, assembling components, and packing finished goods. This document supports training and demonstration. It does not establish regulatory compliance or equipment authorization.
- Plant_Quality_Control_Standards.docx, page 1, 1 Authority and product requirements (QUA001-009): Use the current approved drawing, purchase specification, and customer requirements. Resolve conflicts before production. The numerical values below are fictional training criteria, not engineering specifications for an actual part. No certification to ISO or another quality standard is implied.

## PLANT-RAG-044 cross_document

**Question:** What prevents a maintenance repair sign-off from automatically releasing a held product lot?

**Reference answer:** Maintenance handover includes first-piece inspection and held-product records, with Quality approval when required. Separately, quality release requires passing inspections and traceability, closure of holds or a valid concession, compliant labels and packaging, and a signed and dated release by the designated Quality authority. A repair sign-off does not replace those product-release requirements.

**Type:** multi_document | **Difficulty:** hard | **Answerability:** answerable

**Required facts:**
- Maintenance handover records first-piece inspection and held product and includes Quality approval if required.
- Quality requires passing inspections and traceability plus closed holds or a valid concession.
- Labels and packaging must comply and the designated Quality authority signs and dates release.

**Do not claim:**
- A maintenance sign-off automatically removes all product holds.

**Source evidence**:
- Plant_Maintenance_Manual.docx, page 4, 5 Maintenance record and handover (MNT001-048): Record: First-piece inspection and held product | Result or reference: 
- Plant_Maintenance_Manual.docx, page 4, 5 Maintenance record and handover (MNT001-050): As-left status: Available / Unavailable  |  Next maintenance due __________________ Technician sign off __________  Maintenance approval __________ Production handover __________  Quality approval if required __________
- Plant_Quality_Control_Standards.docx, page 3, Release criteria (QUA001-037): Required inspections have passed and records link the product to its drawing revision, material lot, and work order.
- Plant_Quality_Control_Standards.docx, page 3, Release criteria (QUA001-038): Holds are closed or a valid concession identifies the exact units and authorized limits.
- Plant_Quality_Control_Standards.docx, page 3, Release criteria (QUA001-039): Labels, quantities, and packaging meet the order requirements.
- Plant_Quality_Control_Standards.docx, page 3, Release criteria (QUA001-040): The designated Quality release authority signs and dates the release. Production targets do not override acceptance criteria.

## PLANT-RAG-045 missing_information

**Question:** What exact emergency telephone number should I call at Riverton Components Plant?

**Reference answer:** The supplied documents do not give an emergency telephone number; the field is blank. Obtain the approved site emergency contact information before relying on the procedure.

**Type:** unanswerable | **Difficulty:** medium | **Answerability:** unanswerable

**Required facts:**
- State that the exact emergency number is not supplied.
- Identify the blank site field and need for approved site contact information.

**Do not claim:**
- Invent a telephone number or present a general emergency number as the plant-specific value.

**Source evidence** identifying the gap:
- Plant_Safety_Procedures.docx, page 3, Site information to complete before issue (SAF001-043): Emergency number: __________________  Internal reporting number: __________________

## PLANT-RAG-046 missing_information

**Question:** Where exactly are the primary and alternate assembly areas for this plant?

**Reference answer:** Their locations are not supplied. The primary and alternate assembly-area fields are blank and must be completed with approved site information.

**Type:** unanswerable | **Difficulty:** medium | **Answerability:** unanswerable

**Required facts:**
- Both assembly-area locations are missing.
- The fields need approved site information.

**Do not claim:**
- Invent a parking lot, gate, building, or compass direction.

**Source evidence** identifying the gap:
- Plant_Safety_Procedures.docx, page 3, Site information to complete before issue (SAF001-044): Primary assembly area: __________________  Alternate assembly area: __________________

## PLANT-RAG-047 missing_information

**Question:** What exact lubricant grade and quantity should I use for the MC 01 lubrication points?

**Reference answer:** The source documents do not specify the exact MC 01 lubricant grade or quantity. Approved lubricants and quantities must be entered in the asset task sheet using the applicable manufacturer instructions; do not substitute a generic grease or setting.

**Type:** unanswerable | **Difficulty:** hard | **Answerability:** unanswerable

**Required facts:**
- Exact MC 01 lubricant grade and quantity are not provided.
- Consult approved asset-specific instructions and task-sheet values.
- Do not invent or substitute a generic lubricant.

**Do not claim:**
- Supply an unsupported lubricant grade, brand, or quantity.

**Source evidence** identifying the gap:
- Plant_Maintenance_Manual.docx, page 1, Before adopting this manual (MNT001-016): Set maintenance intervals using manufacturer requirements, duty cycle, environment, failure history, and risk. The frequencies in this example are planning prompts. They are not manufacturer limits. Enter approved lubricants, quantities, torque values, wear limits, pressures, and test criteria in each asset task sheet before work is authorized.
- Plant_Maintenance_Manual.docx, page 2, 3 Preventive maintenance planning (MNT001-021): Asset and timing: MC 01 Weekly | Example task: Inspect accessible fluid systems, filtration indicators, and scheduled lubrication points under the task sheet. | Evidence and acceptance: Record fluid condition and values against asset limits; use specified materials only.
- Plant_Maintenance_Manual.docx, page 2, Spares and lubrication control (MNT001-028): Use approved part numbers and materials. Record substituted parts only after engineering approval. Store lubricants in labeled closed containers, prevent mixing, and record the type and quantity used. Never substitute a generic torque, grease, or pressure setting for an approved asset value.

## PLANT-RAG-048 missing_information

**Question:** How many years must the plant retain quality inspection and calibration records?

**Reference answer:** No number of years is specified. The document requires retention under an approved site schedule, and retention periods must be approved before site issue.

**Type:** unanswerable | **Difficulty:** medium | **Answerability:** unanswerable

**Required facts:**
- A numerical retention period is not supplied.
- Use the approved site retention schedule; periods require approval before issue.

**Do not claim:**
- Invent a fixed retention period such as five or seven years.

**Source evidence** identifying the gap:
- Plant_Quality_Control_Standards.docx, page 4, Records and performance review (QUA001-049): Retain receiving records, inspection results, calibration evidence, nonconformance reports, concessions, and release records under the approved retention schedule. Keep originals readable, controlled, and retrievable by lot. Corrections must preserve the original entry and identify who changed it, when, and why.
- Plant_Quality_Control_Standards.docx, page 4, Site approval (QUA001-052): Approve actual drawings, characteristic risks, methods, decision rules, inspection frequencies, and retention periods before issue. Engineering __________  Quality __________ Effective date __________  Next review __________  Record location __________

## PLANT-RAG-049 missing_information

**Question:** Which exact steel grade must BRK 100 be made from?

**Reference answer:** The exact grade is not stated. Material grade and condition must match the approved purchase specification, supported by supplier evidence and lot identification. Retrieve the approved specification rather than infer a grade.

**Type:** unanswerable | **Difficulty:** hard | **Answerability:** unanswerable

**Required facts:**
- The exact material grade is missing.
- The approved purchase specification governs grade and condition.

**Do not claim:**
- Invent a steel grade or alloy designation.

**Source evidence** identifying the gap:
- Plant_Quality_Control_Standards.docx, page 1, 2 Example bracket acceptance criteria (QUA001-012): Characteristic: Material | Example requirement: Grade and condition match approved purchase specification | Method: Supplier evidence and lot identification

## PLANT-RAG-050 missing_information

**Question:** Who is the named emergency coordinator, and who is their deputy?

**Reference answer:** No names are provided. The emergency coordinator and deputy field is blank and needs approved site information.

**Type:** unanswerable | **Difficulty:** medium | **Answerability:** unanswerable

**Required facts:**
- The coordinator and deputy names are not provided.
- The relevant site field is blank.

**Do not claim:**
- Invent names or treat an unrelated job title as the named coordinator.

**Source evidence** identifying the gap:
- Plant_Safety_Procedures.docx, page 3, Site information to complete before issue (SAF001-046): Emergency coordinator and deputy: _____________________________________________
