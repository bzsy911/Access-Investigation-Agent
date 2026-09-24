# Session 3 — Demo Setup and Project Documentation

## Tasks

### 1. Create `demo.py`

Create a `demo.py` script that runs the prepared investigation demos without
requiring the full command to be typed each time. The script should wrap at
least the following investigations:

```
python agent.py "Which former employees still have active accounts?"
python agent.py "Which users on critical apps are not enrolled in MFA?"
python agent.py --debug --steps 15 "Show drive permissions for ended employees"
```

Support running all demos in sequence or selecting individual ones by ID
(e.g. `python demo.py 1`, `python demo.py 2`).

### 2. Update `PROJECT.md`

Update `PROJECT.md` to serve as a self-contained reference document for future
sessions. It should include:

- A status table listing every file in the repository and whether it is
  complete.
- A quick-start command sequence for a new session.
- A log of all bugs and debugging gotchas encountered during implementation,
  with a description of each problem, its root cause, and the fix applied.

The goal is that reading `PROJECT.md` alone is sufficient to get fully up to
speed at the start of any future session.
