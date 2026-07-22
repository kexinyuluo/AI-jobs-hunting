# Email store git policy — what does the private overlay repo track?

- **Status**: folding
- **Filed**: 2026-07-21
- **Blocking?**: only the git-policy piece of the email sync stage
  (execution-plan stage 5b); nothing else

## The question

When the email store lands under `private/data/email/`, which zones does
the private overlay git repo track? The overlay pushes to a private GitHub
remote, so "tracked" means "in pushed, effectively permanent git history".

## Your clarifying question, answered

You asked: *"shouldn't we push to my private repo? Is that's the concern?
Can you provide more examples of what actual data looks like and what's the
consequence?"* Yes — the concern is exactly the push. What a tracked
message-metadata file would contain (fictional example, realistic shape):

```yaml
subject: "Re: Jordan Rivers — ExampleCorp onsite + comp expectations"
from: "sam.chen@example.com"   # a real third party
snippet: "following up on the 185k base we discussed, and whether
          Thursday works for the panel with Dana Wu…"
category: interview_scheduling
```

Multiplied by every synced message, tracking this means a permanent pushed
history of every company you talked to, every recruiter's and interviewer's
name, every scheduling and compensation snippet. Why "it's a private repo"
doesn't fully cover it: (1) git history is effectively unremovable after
push — deleting a file later doesn't remove it from history; (2) a leaked
GitHub token or any compromised clone exposes the *entire history*, not one
laptop's current state; (3) the benefit is asymmetric — derived metadata is
rebuildable from local raw anytime, so the offsite copy duplicates data you
can already regenerate, while your *annotations* (judgments) are the only
part git history genuinely protects.

## Options

| | Option | What you get | What it costs / risks |
| --- | --- | --- | --- |
| A | Track only index *headers* + `annotations/` (minus the evidence sidecar); `derived/` and `raw/` git-ignored (recommended) | Offsite history of your judgments and the store's shape; third-party content never enters git | Message metadata has no git history — a corrupted derived zone is rebuilt from raw instead of restored from git (the design supports that anyway) |
| B | Track derived + index + annotations | Full offsite history of all metadata | Every subject/snippet — other people's names included — permanently in pushed history; compromise exposes your whole correspondence graph |
| C | Track nothing under `email/` | Simplest | No offsite copy even of your own annotations |

**Recommendation.** A. (Mirrored decision block with identical options:
`docs/design/raw-data-layer/04-email-download-categorization.md` → Q-E.
Folding an answer updates both surfaces in the same commit; on conflict the
doc block wins.)

## Default path while pending

Option A. Agents plan on that assumption; flipping to B later is a one-line
gitignore change plus a deliberate first commit.

**Your answer:** ______
