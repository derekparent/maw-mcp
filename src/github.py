"""
GitHub Integration for MAW
Uses `gh` CLI for PR fetching and conflict detection
"""
import json
import subprocess
from pathlib import Path
from typing import Optional


def run_gh(args: list[str], cwd: str = ".") -> tuple[bool, str]:
    """Run gh CLI command, return (success, output)"""
    try:
        result = subprocess.run(
            ["gh"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except FileNotFoundError:
        return False, "gh CLI not found. Install with: brew install gh"
    except subprocess.TimeoutExpired:
        return False, "GitHub API request timed out"
    except Exception as e:
        return False, str(e)


def get_open_prs(project_path: str = ".") -> tuple[bool, list[dict] | str]:
    """Get all open PRs for the repo"""
    success, output = run_gh([
        "pr", "list",
        "--state", "open",
        "--json", "number,title,headRefName,body,additions,deletions,files,author,createdAt,url"
    ], cwd=project_path)
    
    if not success:
        return False, output
    
    try:
        prs = json.loads(output)
        return True, prs
    except json.JSONDecodeError:
        return False, f"Failed to parse PR list: {output}"


def get_pr_details(pr_number: int, project_path: str = ".") -> tuple[bool, dict | str]:
    """Get detailed info for a specific PR"""
    success, output = run_gh([
        "pr", "view", str(pr_number),
        "--json", "number,title,headRefName,body,additions,deletions,files,state,mergeable,mergeStateStatus,author,url"
    ], cwd=project_path)
    
    if not success:
        return False, output
    
    try:
        pr = json.loads(output)
        return True, pr
    except json.JSONDecodeError:
        return False, f"Failed to parse PR details: {output}"


def get_agent_prs(project_path: str = ".") -> tuple[bool, list[dict] | str]:
    """Get all open PRs that look like agent branches"""
    success, prs = get_open_prs(project_path)
    if not success:
        return False, prs
    
    agent_prs = []
    for pr in prs:
        branch = pr.get("headRefName", "")
        # Match agent branches: agent/1-*, agent/2-*, etc.
        if branch.startswith("agent/"):
            # Extract agent number
            parts = branch.split("/")[1].split("-")
            try:
                agent_num = int(parts[0])
                pr["agent_num"] = agent_num
                agent_prs.append(pr)
            except (ValueError, IndexError):
                # Not a numbered agent branch, skip
                pass
    
    # Sort by agent number
    agent_prs.sort(key=lambda x: x.get("agent_num", 999))
    return True, agent_prs


def detect_conflicts(prs: list[dict]) -> list[dict]:
    """Detect file conflicts between PRs"""
    conflicts = []
    file_to_prs = {}
    
    for pr in prs:
        files = pr.get("files", [])
        for f in files:
            path = f.get("path", "") if isinstance(f, dict) else str(f)
            if path not in file_to_prs:
                file_to_prs[path] = []
            file_to_prs[path].append(pr.get("number"))
    
    for path, pr_numbers in file_to_prs.items():
        if len(pr_numbers) > 1:
            conflicts.append({
                "file": path,
                "prs": pr_numbers
            })
    
    return conflicts


def get_local_branches(project_path: str = ".") -> list[str]:
    """Get list of local git branches"""
    try:
        result = subprocess.run(
            ["git", "branch", "--list", "agent/*"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        branches = []
        for line in result.stdout.strip().split("\n"):
            branch = line.strip().lstrip("* ")
            if branch:
                branches.append(branch)
        return branches
    except Exception:
        return []


def format_pr_dashboard(prs: list[dict], conflicts: list[dict]) -> str:
    """Format PRs into a status dashboard"""
    lines = ["## 📊 Agent Status Dashboard (from GitHub)\n"]
    
    if not prs:
        lines.append("No agent PRs found.\n")
        lines.append("Either agents haven't created PRs yet, or branches don't follow `agent/N-*` pattern.")
        return "\n".join(lines)
    
    # Summary table
    lines.append("### Summary")
    lines.append(f"| PRs Found | Files Changed | Conflicts |")
    lines.append(f"|-----------|---------------|-----------|")
    total_files = sum(len(pr.get("files", [])) for pr in prs)
    lines.append(f"| {len(prs)} | {total_files} | {len(conflicts)} |")
    lines.append("")
    
    # PR details
    lines.append("### Agent PRs")
    lines.append("| Agent | PR | Branch | +/- | Status |")
    lines.append("|-------|----|---------|----|--------|")
    
    for pr in prs:
        agent_num = pr.get("agent_num", "?")
        number = pr.get("number", "?")
        branch = pr.get("headRefName", "?")
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        url = pr.get("url", "")
        
        lines.append(f"| {agent_num} | [#{number}]({url}) | `{branch}` | +{additions}/-{deletions} | ✅ Open |")
    
    lines.append("")
    
    # Files changed per PR
    lines.append("### Files Changed")
    for pr in prs:
        agent_num = pr.get("agent_num", "?")
        files = pr.get("files", [])
        lines.append(f"\n**Agent {agent_num}:**")
        for f in files[:10]:  # Limit to first 10
            path = f.get("path", str(f)) if isinstance(f, dict) else str(f)
            lines.append(f"- `{path}`")
        if len(files) > 10:
            lines.append(f"- ... and {len(files) - 10} more")
    
    lines.append("")
    
    # Conflicts
    if conflicts:
        lines.append("### ⚠️ Potential Conflicts")
        lines.append("These files are modified by multiple PRs:")
        lines.append("")
        lines.append("| File | PRs |")
        lines.append("|------|-----|")
        for c in conflicts:
            pr_list = ", ".join(f"#{n}" for n in c["prs"])
            lines.append(f"| `{c['file']}` | {pr_list} |")
        lines.append("")
        lines.append("**Recommendation:** Merge these PRs one at a time, rebasing after each merge.")
    else:
        lines.append("### ✅ No Conflicts Detected")
        lines.append("No files are modified by multiple PRs. Safe to merge in any order.")
    
    lines.append("")
    
    # Suggested merge order
    lines.append("### Suggested Merge Order")
    
    # Sort by: docs first, tests second, smallest changes third
    def merge_priority(pr):
        branch = pr.get("headRefName", "").lower()
        changes = pr.get("additions", 0) + pr.get("deletions", 0)
        
        if "doc" in branch:
            return (0, changes)
        elif "test" in branch:
            return (1, changes)
        elif "security" in branch or "auth" in branch:
            return (2, changes)
        else:
            return (3, changes)
    
    sorted_prs = sorted(prs, key=merge_priority)
    
    for i, pr in enumerate(sorted_prs, 1):
        number = pr.get("number")
        branch = pr.get("headRefName", "")
        lines.append(f"{i}. PR #{number} (`{branch}`)")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Next Steps")
    if conflicts:
        lines.append("1. Review conflicts above")
        lines.append("2. Decide merge order to minimize rebasing")
        lines.append("3. Run `maw_integrate` for merge commands and test plan")
    else:
        lines.append("1. Review PR changes on GitHub")
        lines.append("2. Run `maw_integrate` for merge commands and test plan")
    
    return "\n".join(lines)
