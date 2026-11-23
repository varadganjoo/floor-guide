# Stopped full-suite run

The user changed the instruction to test failed cases only after the first 20
golden questions had been submitted through the UI. The full 50-question sweep
was stopped at that point.

The five remaining failed cases were then submitted under the same v3 code,
exposing a stale topic-scope validation bug in case 023. Those results remain
in this directory's raw JSONL files. They are not a completed full-suite score.

After fixing that bug, only the eight remaining regression cases were rerun
together under v3.1. See the [targeted verification report](../failed-cases-v3-1/report.md)
for the final, separately recorded results. No result in this stopped run was
overwritten to turn a failure into a pass.
