# memory/facts/ — durable constraints

One file per fact that is true of this project's environment and **not
derivable from the code or git history**: external-service behavior,
tooling quirks, owner-stated invariants. State current truth plainly;
update the file when reality changes (git remembers the old state), and
delete facts that stop being true.

Schema: copy `templates/memory/fact.md` (validated by `automation/reconcile/reconcile.py`).
