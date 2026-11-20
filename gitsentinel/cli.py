"""Command Line Interface for GitSentinel."""

import sys
import argparse
import subprocess
from pathlib import Path

from gitsentinel import __version__
from gitsentinel.scanner import SecurityScanner
from gitsentinel.commit_gen import CommitGenerator
from gitsentinel.doctor import RepoDoctor
from gitsentinel.hooks import install_pre_commit_hook

# ANSI Color codes for clean terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
   ____ _ _   ____             _   _            _ 
  / ___(_) |_/ ___|  ___ _ __ | |_(_)_ __   ___| |
 | |  _| | __\___ \ / _ \ '_ \| __| | '_ \ / _ \ |
 | |_| | | |_ ___) |  __/ | | | |_| | | | |  __/ |
  \____|_|\__|____/ \___|_| |_|\__|_|_| |_|\___|_|
{RESET}{CYAN}  Autonomous Pre-Flight Security Scanner & AI Git Copilot (v{__version__}){RESET}
"""
    print(banner)


def cmd_scan(args):
    target = Path(args.path).resolve()
    scanner = SecurityScanner(target)
    print(f"{BOLD}🔍 Scanning directory:{RESET} {target}\n")

    findings = scanner.scan_path()

    if not findings:
        print(f"{GREEN}✅ No security leaks, bloat, or critical code smells found. Clean repo!{RESET}\n")
        return 0

    critical_count = 0
    print(f"{BOLD}Found {len(findings)} item(s):{RESET}\n")
    for idx, f in enumerate(findings, 1):
        if f.severity == "CRITICAL":
            critical_count += 1
            color = RED
            badge = "🚨 CRITICAL"
        elif f.severity == "HIGH":
            color = YELLOW
            badge = "⚠️  HIGH"
        else:
            color = CYAN
            badge = "ℹ️  INFO"

        loc = f"{f.file_path}:{f.line_number}" if f.line_number else f.file_path
        print(f"{idx}. {color}{badge}{RESET} [{f.category}] in {BOLD}{loc}{RESET}")
        print(f"   {f.message}")
        if f.snippet:
            print(f"   Snippet: {color}{f.snippet}{RESET}")
        print()

    print(f"{BOLD}Summary:{RESET} {critical_count} critical, {len(findings) - critical_count} non-critical.")

    if args.fail_on_critical and critical_count > 0:
        print(f"{RED}{BOLD}Scan failed: Critical security issues must be resolved before proceeding.{RESET}")
        return 1
    return 0


def cmd_commit(args):
    repo_dir = Path(".").resolve()
    generator = CommitGenerator(repo_dir)

    print(f"{BOLD}🤖 Synthesizing Conventional Commit Message...{RESET}\n")
    res = generator.generate_message(context_hint=args.hint)

    print(f"{GREEN}{BOLD}Proposed Commit Title:{RESET}")
    print(f"  {CYAN}{res['title']}{RESET}\n")

    if res.get("body"):
        print(f"{BOLD}Change Description:{RESET}")
        for line in res["body"].splitlines():
            print(f"  {line}")
        print()

    if args.auto:
        msg = f"{res['title']}\n\n{res.get('body', '')}"
        try:
            subprocess.run(["git", "commit", "-m", msg], check=True)
            print(f"{GREEN}✅ Successfully committed changes with GitSentinel!{RESET}")
            return 0
        except subprocess.SubprocessError as e:
            print(f"{RED}❌ Git commit failed: {e}{RESET}")
            return 1
    else:
        print(f"{BOLD}To apply this commit manually:{RESET}")
        print(f'  git commit -m "{res["title"]}"')
        print(f"{YELLOW}(Or run 'gitsentinel commit --auto' to commit directly){RESET}\n")
        return 0


def cmd_doctor(args):
    target = Path(args.path).resolve()
    doctor = RepoDoctor(target)
    print(f"{BOLD}🩺 Diagnosing repository health:{RESET} {target}\n")

    report = doctor.diagnose()
    score = report["score"]

    score_color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)
    print(f"{BOLD}Repository Health Score: {score_color}{score}/100{RESET}\n")

    for check in report["checks"]:
        if check.status == "PASS":
            mark = f"{GREEN}✓ PASS{RESET}"
        elif check.status == "WARN":
            mark = f"{YELLOW}▲ WARN{RESET}"
        else:
            mark = f"{RED}✗ FAIL{RESET}"

        print(f"[{mark}] {BOLD}{check.check_name}{RESET}: {check.message}")
        if check.recommendation and check.recommendation != "None.":
            print(f"       👉 {CYAN}Fix:{RESET} {check.recommendation}")
    print()
    return 0


def cmd_hook(args):
    repo_dir = Path(".").resolve()
    success, msg = install_pre_commit_hook(repo_dir)
    if success:
        print(f"{GREEN}✅ {msg}{RESET}")
        return 0
    else:
        print(f"{RED}❌ {msg}{RESET}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="gitsentinel",
        description="Autonomous Pre-Flight Security Scanner & AI Git Copilot"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    # scan command
    p_scan = subparsers.add_parser("scan", help="Scan directory for secrets, bloat, and code smells")
    p_scan.add_argument("path", nargs="?", default=".", help="Target path to scan (default: current directory)")
    p_scan.add_argument("--fail-on-critical", action="store_true", help="Exit with non-zero status if critical secrets found")

    # commit command
    p_commit = subparsers.add_parser("commit", help="Generate AI-powered conventional commit message from git diff")
    p_commit.add_argument("--hint", help="Optional intent or context hint for commit message")
    p_commit.add_argument("--auto", action="store_true", help="Automatically execute git commit with generated message")

    # doctor command
    p_doc = subparsers.add_parser("doctor", help="Run repository health and hygiene checkup")
    p_doc.add_argument("path", nargs="?", default=".", help="Target path (default: current directory)")

    # install-hook command
    p_hook = subparsers.add_parser("install-hook", help="Install GitSentinel as a git pre-commit hook")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        return 0

    if args.command == "scan":
        return cmd_scan(args)
    elif args.command == "commit":
        return cmd_commit(args)
    elif args.command == "doctor":
        return cmd_doctor(args)
    elif args.command == "install-hook":
        return cmd_hook(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
