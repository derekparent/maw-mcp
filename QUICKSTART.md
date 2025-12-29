# MAW Quickstart Guide

Get multiple AI agents working on your code at the same time.

---

## What Does This Do?

Instead of Claude doing one thing at a time, MAW lets you have multiple Claudes working in parallel:

| Without MAW | With MAW |
|-------------|----------|
| Fix bug → wait → write tests → wait → update docs | Fix bug + write tests + update docs (all at once) |
| 3 hours | 1 hour |

Each agent works on its own copy of the code (a "branch"), then you combine them when done.

---

## The Workflow

```
You: "Review my code"
        ↓
   Claude analyzes, creates task list
        ↓
You: "Launch the agents"  
        ↓
   You copy prompts to separate Claude windows
   Each one works independently
        ↓
You: "Check in" (paste their reports)
        ↓
   Dashboard shows who's done
        ↓
You: "Integrate"
        ↓
   Merge order + test checklist
        ↓
You: "What's next?"
        ↓
   Deploy, or do another round
```

---

## Step 1: Setup (One Time)

Tell Claude Desktop where to find MAW. 

Open this file (create if it doesn't exist):
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Paste this:
```json
{
  "mcpServers": {
    "maw": {
      "command": "python3",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/maw-mcp"
    }
  }
}
```

Change `/path/to/maw-mcp` to wherever you put this folder.

Restart Claude Desktop.

---

## Step 2: Review

Open a chat and say:

> "Review this codebase for improvements. Focus on security. Call it Wave 1."

Claude will:
1. Look at your code
2. Identify 3-5 things to fix
3. Create a folder called `AGENT_PROMPTS/` with one file per task

**Stop here and read the prompts.** Make sure they make sense before continuing.

---

## Step 3: Launch

Say:

> "Show me the launch sequence"

Claude gives you:
- Which agent to start first
- Which can run in parallel
- Copy-paste prompts for each

**Open separate Claude windows** (or Cursor sessions) and paste each prompt. Each agent works on its own branch.

---

## Step 4: Check In

When agents finish, they give you a completion report. Collect them all and say:

> "Here are the agent reports: [paste all reports]"

Claude shows a dashboard:
```
✅ Complete: 3 agents
⚠️ Partial: 1 agent  
❌ Blocked: 0 agents
```

---

## Step 5: Integrate

When all agents are done:

> "Show me how to integrate"

Claude gives you:
- Order to merge the branches
- Test checklist to verify everything works
- Commands to run

---

## Step 6: Decide

After integration:

> "What should I do next?"

Claude recommends:
- **Deploy** if everything works
- **Iterate** if more fixes needed
- **Add features** if the foundation is solid

---

## Commands Reference

| You Say | What Happens |
|---------|--------------|
| "Check workflow status" | Shows current phase and next step |
| "Review this codebase" | Analyzes code, creates agent tasks |
| "Show launch sequence" | Gives copy-paste prompts for agents |
| "Here are the reports..." | Aggregates progress, shows dashboard |
| "How do I integrate?" | Merge order + test plan |
| "What's next?" | Deploy/iterate/add features recommendation |
| "Save this learning..." | Captures notes for future reference |
| "Search patterns for X" | Finds relevant past learnings |

---

## Tips

**Start small.** Try it on a simple project first.

**Read the prompts.** The pause between review and launch exists so you can edit the tasks.

**One branch per agent.** Never let two agents work on the same branch.

**Check in regularly.** Don't wait until the end to see if agents are stuck.

---

## Files Created in Your Project

```
your-project/
├── WORKFLOW_STATE.json    ← Tracks progress
├── AGENT_PROMPTS/         ← Task files for each agent
│   ├── 1_Backend.md
│   ├── 2_Testing.md
│   ├── COORDINATION.md
│   └── README.md
└── PROJECT_LEARNINGS.md   ← Notes from this project
```

---

## Troubleshooting

**"maw tools not found"**  
Restart Claude Desktop after editing the config file.

**"Review not complete"**  
Run the review step first before trying to launch.

**Agent stuck**  
Check their completion report for blockers. Answer their question and relaunch just that agent.

**Merge conflicts**  
Follow the merge order from integrate step. Simpler changes first.

---

## Example Session

```
You: Review this Flask app for improvements, call it "Security Wave"

Claude: [analyzes code, creates AGENT_PROMPTS/]
        Done! Review the prompts in AGENT_PROMPTS/ then ask for launch sequence.

You: Show me the launch sequence

Claude: Launch Order:
        1. Agent 1 (Backend Security) - run first
        2. Agents 2, 3 - run in parallel after
        
        [copy-paste prompts for each]

You: [opens 3 Claude windows, pastes prompts, agents work]

You: Here are the completion reports:
     [pastes all 3 reports]

Claude: 📊 Dashboard
        ✅ Complete: 3/3
        Ready for integration!

You: How do I integrate?

Claude: Merge order:
        1. Agent 3 (docs) - lowest risk
        2. Agent 2 (tests)  
        3. Agent 1 (backend)
        
        Test plan:
        ☐ App starts
        ☐ All tests pass
        ☐ Login works
        ...

You: [merges PRs, runs tests]
     What's next?

Claude: All tests passing, no critical issues.
        Recommendation: ✅ Deploy
```

---

## Need Help?

Check the full README.md for detailed tool documentation.
