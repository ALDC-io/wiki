New chat window - save context from previous window using this prompt


Create a file called `CHAT-HANDOFF.md` for use in a fresh chat.

Make it a compact restart brief, not a full transcript summary.

Include only:
1. current objective
2. current phase and current slice
3. last completed task
4. next task
5. locked architecture decisions
6. current repo state that matters
7. files likely to change next
8. tests/invariants to protect
9. open blockers/questions
10. what not to do yet

Requirements:
- keep it high signal
- avoid duplication
- do not include long history
- assume the file will be pasted into a new chat to restore context quickly
- make it specific to the repo’s current state