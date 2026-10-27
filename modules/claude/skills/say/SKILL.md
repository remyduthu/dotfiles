---
name: say
description: Hear a hallway explanation of the work, spoken aloud through macOS say.
argument-hint: "[what to talk about: current state, findings, a problem, options, a PR...]"
allowed-tools: Bash(say:*), Write
disable-model-invocation: true
---

# Say

The user wants to **listen** instead of read. Give a **hallway explanation**: a senior
engineer telling a smart colleague from another team the idea, out loud, in words they
already know.

Talk about whatever the user asked. No topic → recap where things stand and what needs
the user next.

## How to talk

- **Open with the point.** What this is about and why it matters, before any mechanism.
- **Signpost.** Say how many parts are coming ("Two problems, then the fix.") and
  keep that order.
- **Name things by what they do**, not their code name: "the job that cleans old rows",
  not `PurgeWorker`. A term the user must learn gets a few-word definition once.
- **Concrete.** A small example, a rounded number, an everyday comparison that stays
  true to the facts.
- **Keep the facts.** Simplify the words, keep every caveat and risk.
- **Close with the ask.** What you recommend, or what the user should decide, look at,
  or do next.

A big topic gets the overview plus an offer to go deeper on one part.

## Speaking

1. Write the script to a file in your scratchpad directory. Done when it applies every
   rule under How to talk, runs 200 to 500 words, and is pure prose a listener can
   follow: numbers phrased as spoken ("about three seconds"), acronyms expanded, and no
   markdown, symbols, code, paths, URLs or IDs (`say` reads them literally).
2. Run `say -f <file>` with a 600000 ms Bash timeout.
3. Reply with one line saying you spoke, plus anything that only works in writing
   (links, commands, exact names) the user may want to copy.
