#!/usr/bin/env python3
"""
ShadowScribe 2.0 - Application Management Script

A cross-platform (macOS/Windows/Linux) script for managing the ShadowScribe application.

Usage:
    python manage.py start          # Start all services
    python manage.py stop           # Stop all services
    python manage.py restart        # Restart all services
    python manage.py status         # Show service status
    python manage.py logs           # Tail all logs
    python manage.py logs api       # Tail specific service logs
    python manage.py health         # Check service health
    python manage.py migrate        # Run database migrations
    python manage.py shell          # Open interactive shell
    python manage.py demo           # Run demo central engine
"""

import argparse
import os
import subprocess
import sys
import time
import shutil
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# ANSI color codes (works on most terminals)
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    
    @classmethod
    def disable(cls):
        """Disable colors for terminals that don't support them."""
        cls.RESET = cls.RED = cls.GREEN = cls.YELLOW = ""
        cls.BLUE = cls.MAGENTA = cls.CYAN = cls.BOLD = ""


# Detect if terminal supports colors
if sys.platform == "win32":
    # Enable ANSI colors on Windows 10+
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.disable()


# Project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()
LOGS_DIR = PROJECT_ROOT / "logs"
ENV_FILE = PROJECT_ROOT / ".env"


def print_banner():
    """Print the ShadowScribe banner."""
    banner = f"""
{Colors.MAGENTA}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║   🎲 ShadowScribe 2.0 - D&D Character Management System   ║
╚═══════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


def log(message: str, level: str = "info"):
    """Print a formatted log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {
        "info": f"{Colors.BLUE}ℹ️ ",
        "success": f"{Colors.GREEN}✅",
        "warning": f"{Colors.YELLOW}⚠️ ",
        "error": f"{Colors.RED}❌",
        "wait": f"{Colors.CYAN}⏳",
        "rocket": f"{Colors.MAGENTA}🚀",
    }
    icon = icons.get(level, icons["info"])
    print(f"{Colors.BOLD}[{timestamp}]{Colors.RESET} {icon} {message}{Colors.RESET}")


def run_command(
    cmd: List[str], 
    capture_output: bool = False, 
    check: bool = True,
    cwd: Optional[Path] = None
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check,
            cwd=cwd or PROJECT_ROOT
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            log(f"Command failed: {' '.join(cmd)}", "error")
            if e.stderr:
                print(e.stderr)
        raise
    except FileNotFoundError:
        log(f"Command not found: {cmd[0]}", "error")
        raise


def check_docker() -> bool:
    """Check if Docker is installed and running."""
    # Check if docker is installed
    if not shutil.which("docker"):
        log("Docker is not installed. Please install Docker Desktop.", "error")
        return False
    
    # Check if docker is running
    try:
        result = run_command(["docker", "info"], capture_output=True, check=False)
        if result.returncode != 0:
            log("Docker is not running. Please start Docker Desktop.", "error")
            return False
    except Exception:
        log("Failed to check Docker status.", "error")
        return False
    
    return True


def check_env_file() -> bool:
    """Check if .env file exists with required keys."""
    if not ENV_FILE.exists():
        log(".env file not found", "error")
        print(f"\n  Please create {ENV_FILE} with your API keys:")
        print(f"    OPENAI_API_KEY=sk-...")
        print(f"    ANTHROPIC_API_KEY=sk-ant-...")
        return False
    
    # Check for required keys
    env_content = ENV_FILE.read_text()
    missing_keys = []
    
    if "OPENAI_API_KEY" not in env_content:
        missing_keys.append("OPENAI_API_KEY")
    if "ANTHROPIC_API_KEY" not in env_content:
        missing_keys.append("ANTHROPIC_API_KEY")
    
    if missing_keys:
        log(f"Missing API keys in .env: {', '.join(missing_keys)}", "warning")
        # Not a hard failure - some configs might not need both
    
    return True


def check_prerequisites() -> bool:
    """Check all prerequisites before starting."""
    log("Checking prerequisites...", "info")
    
    if not check_env_file():
        return False
    
    if not check_docker():
        return False
    
    log("All prerequisites satisfied", "success")
    return True


def get_docker_compose_cmd() -> List[str]:
    """Get the appropriate docker-compose command."""
    # Try docker compose (v2) first, then docker-compose (v1)
    if shutil.which("docker"):
        # Check if 'docker compose' works
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                check=True
            )
            return ["docker", "compose"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    
    log("Neither 'docker compose' nor 'docker-compose' found", "error")
    sys.exit(1)


def wait_for_service(name: str, check_fn, timeout: int = 60) -> bool:
    """Wait for a service to become healthy."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if check_fn():
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def check_mysql_health() -> bool:
    """Check if MySQL is healthy."""
    compose = get_docker_compose_cmd()
    try:
        result = run_command(
            compose + ["exec", "-T", "mysql", "mysqladmin", "ping", "-h", "localhost", "--silent"],
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def check_api_health() -> bool:
    """Check if the API is healthy."""
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
        return req.status == 200
    except Exception:
        return False


def check_frontend_health() -> bool:
    """Check if the frontend is healthy."""
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:3000", timeout=5)
        return req.status == 200
    except Exception:
        return False


# ============================================================================
# Commands
# ============================================================================

def cmd_start(args):
    """Start all services."""
    print_banner()
    
    if not check_prerequisites():
        sys.exit(1)
    
    compose = get_docker_compose_cmd()
    
    log("Starting Docker Compose services...", "rocket")
    run_command(compose + ["up", "-d"])
    
    print()
    log("Waiting for services to be healthy...", "wait")
    
    # Wait for MySQL
    if wait_for_service("MySQL", check_mysql_health, timeout=60):
        log("MySQL is ready", "success")
    else:
        log("MySQL failed to start", "error")
        return cmd_logs(argparse.Namespace(service="mysql", follow=False, lines=50))
    
    # Wait for API
    if wait_for_service("API", check_api_health, timeout=60):
        log("API is ready", "success")
    else:
        log("API failed to start", "error")
        return cmd_logs(argparse.Namespace(service="api", follow=False, lines=50))
    
    # Wait for Frontend
    if wait_for_service("Frontend", check_frontend_health, timeout=90):
        log("Frontend is ready", "success")
    else:
        log("Frontend failed to start (may still be building)", "warning")
    
    # Run migrations if needed
    if args.migrate:
        cmd_migrate(args)
    
    print()
    log("ShadowScribe 2.0 is ready!", "success")
    print(f"""
{Colors.BOLD}📍 Access points:{Colors.RESET}
   Frontend:  {Colors.CYAN}http://localhost:3000{Colors.RESET}
   API Docs:  {Colors.CYAN}http://localhost:8000/docs{Colors.RESET}
   MySQL:     {Colors.CYAN}localhost:3306{Colors.RESET}

{Colors.BOLD}📝 Quick commands:{Colors.RESET}
   View logs:     {Colors.YELLOW}python manage.py logs{Colors.RESET}
   Stop services: {Colors.YELLOW}python manage.py stop{Colors.RESET}
   Check status:  {Colors.YELLOW}python manage.py status{Colors.RESET}
""")


def cmd_stop(args):
    """Stop all services."""
    print_banner()
    compose = get_docker_compose_cmd()
    
    log("Stopping Docker Compose services...", "info")
    run_command(compose + ["down"])
    log("All services stopped", "success")


def cmd_restart(args):
    """Restart all services."""
    cmd_stop(args)
    print()
    cmd_start(args)


def cmd_status(args):
    """Show status of all services."""
    print_banner()
    compose = get_docker_compose_cmd()
    
    log("Service status:", "info")
    print()
    run_command(compose + ["ps"])
    
    print()
    log("Health checks:", "info")
    
    services = [
        ("MySQL", check_mysql_health),
        ("API", check_api_health),
        ("Frontend", check_frontend_health),
    ]
    
    for name, check_fn in services:
        try:
            if check_fn():
                print(f"   {Colors.GREEN}✓{Colors.RESET} {name}: healthy")
            else:
                print(f"   {Colors.RED}✗{Colors.RESET} {name}: unhealthy")
        except Exception as e:
            print(f"   {Colors.YELLOW}?{Colors.RESET} {name}: unknown ({e})")


def cmd_logs(args):
    """View service logs."""
    compose = get_docker_compose_cmd()
    
    cmd = compose + ["logs"]
    
    if args.follow:
        cmd.append("-f")
    
    if args.lines:
        cmd.extend(["--tail", str(args.lines)])
    
    if args.service:
        cmd.append(args.service)
    
    try:
        # Use subprocess.call for interactive log viewing
        subprocess.call(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print()  # Clean exit on Ctrl+C


def cmd_health(args):
    """Detailed health check of all services."""
    print_banner()
    log("Running health checks...", "info")
    print()
    
    checks = [
        ("Docker", lambda: check_docker()),
        ("Environment", lambda: check_env_file()),
        ("MySQL", check_mysql_health),
        ("API", check_api_health),
        ("Frontend", check_frontend_health),
    ]
    
    all_healthy = True
    for name, check_fn in checks:
        try:
            if check_fn():
                print(f"   {Colors.GREEN}✓{Colors.RESET} {name}")
            else:
                print(f"   {Colors.RED}✗{Colors.RESET} {name}")
                all_healthy = False
        except Exception as e:
            print(f"   {Colors.RED}✗{Colors.RESET} {name}: {e}")
            all_healthy = False
    
    print()
    if all_healthy:
        log("All systems healthy", "success")
    else:
        log("Some systems are unhealthy", "warning")
        sys.exit(1)


def cmd_migrate(args):
    """Run database migrations."""
    compose = get_docker_compose_cmd()
    
    log("Running character migration...", "info")
    try:
        run_command(
            compose + ["exec", "-T", "api", "python", "scripts/migrate_characters_to_db.py"]
        )
        log("Migration complete", "success")
    except subprocess.CalledProcessError:
        log("Migration failed", "error")
        sys.exit(1)


def cmd_shell(args):
    """Open an interactive Python shell with project context."""
    log("Starting interactive shell...", "info")
    
    shell_cmd = [
        sys.executable, "-i", "-c",
        """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print("\\n🐍 ShadowScribe Interactive Shell")
print("   Project modules are available for import.")
print("   Example: from src.config import get_config\\n")
"""
    ]
    
    try:
        subprocess.call(shell_cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print()


def cmd_demo(args):
    """Run the demo central engine."""
    log("Starting demo central engine...", "rocket")
    
    cmd = [sys.executable, "demo_central_engine.py"]
    
    if args.query:
        cmd.extend(["-q", args.query])
    
    if args.quiet:
        cmd.append("--quiet")
    
    try:
        subprocess.call(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print()


def cmd_build(args):
    """Rebuild Docker images."""
    compose = get_docker_compose_cmd()
    
    log("Rebuilding Docker images...", "info")
    
    cmd = compose + ["build"]
    if args.no_cache:
        cmd.append("--no-cache")
    if args.service:
        cmd.append(args.service)
    
    run_command(cmd)
    log("Build complete", "success")


def cmd_clean(args):
    """Clean up Docker resources."""
    compose = get_docker_compose_cmd()
    
    log("Cleaning up Docker resources...", "info")
    
    # Stop containers
    run_command(compose + ["down", "-v" if args.volumes else ""], check=False)
    
    if args.images:
        log("Removing images...", "info")
        run_command(compose + ["down", "--rmi", "local"], check=False)
    
    log("Cleanup complete", "success")


def cmd_feedback(args):
    """View and manage routing feedback dataset."""
    import json
    import tempfile
    import webbrowser
    compose = get_docker_compose_cmd()
    
    # Handle reprocess mode
    if args.reprocess:
        _reprocess_feedback_entities(args, compose)
        return
    
    # Handle export mode separately - needs different data
    if args.export:
        _export_feedback(args, compose)
        return
    
    # Build the command to run inside the API container
    python_code = '''
import asyncio
import json
import sys
sys.path.insert(0, "/app")

from api.database.connection import AsyncSessionLocal, init_db
from api.database.repositories.feedback_repo import FeedbackRepository

async def main():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        repo = FeedbackRepository(db)
        
        mode = "{mode}"
        limit = {limit}
        show_stats = {show_stats}
        corrections_only = {corrections_only}
        pending_only = {pending_only}
        
        if show_stats:
            stats = await repo.get_stats()
            print("STATS_JSON:" + json.dumps(stats))
            return
        
        if corrections_only:
            records = await repo.get_corrected(limit=limit)
        elif pending_only:
            records = await repo.get_pending_review(limit=limit)
        else:
            records = await repo.get_recent(limit=limit)
        
        output = []
        for r in records:
            output.append({{
                "id": r.id,
                "query": r.user_query,
                "character": r.character_name,
                "is_correct": r.is_correct,
                "predicted_tools": r.predicted_tools,
                "corrected_tools": r.corrected_tools,
                "predicted_entities": r.predicted_entities,
                "notes": r.feedback_notes,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }})
        print("RECORDS_JSON:" + json.dumps(output))

asyncio.run(main())
'''.format(
        mode="stats" if args.stats else "list",
        limit=args.limit,
        show_stats=str(args.stats),
        corrections_only=str(args.corrections),
        pending_only=str(args.pending)
    )
    
    try:
        result = run_command(
            compose + ["exec", "-T", "api", "python", "-c", python_code],
            capture_output=True,
            check=True
        )
        output = result.stdout
        
        # Parse the output
        if "STATS_JSON:" in output:
            stats_line = [l for l in output.split('\n') if l.startswith("STATS_JSON:")][0]
            stats = json.loads(stats_line.replace("STATS_JSON:", ""))
            
            print(f"\n{Colors.BOLD}📊 Routing Feedback Statistics{Colors.RESET}")
            print("=" * 50)
            print(f"  Total records:        {Colors.CYAN}{stats['total_records']:,}{Colors.RESET}")
            print(f"  Pending review:       {Colors.YELLOW}{stats['pending_review']:,}{Colors.RESET}")
            print(f"  Confirmed correct:    {Colors.GREEN}{stats['confirmed_correct']:,}{Colors.RESET}")
            print(f"  User corrections:     {Colors.MAGENTA}{stats['corrected']:,}{Colors.RESET}")
            print(f"  Already exported:     {Colors.BLUE}{stats['exported']:,}{Colors.RESET}")
            print("=" * 50)
            
            unexported = stats['confirmed_correct'] + stats['corrected'] - stats['exported']
            print(f"  Available for export: {Colors.BOLD}{max(0, unexported):,}{Colors.RESET}")
            print()
            
        elif "RECORDS_JSON:" in output:
            records_line = [l for l in output.split('\n') if l.startswith("RECORDS_JSON:")][0]
            records = json.loads(records_line.replace("RECORDS_JSON:", ""))
            
            if not records:
                log("No feedback records found", "info")
                return
            
            # Determine title
            if args.corrections:
                title = "User Corrections"
            elif args.pending:
                title = "Pending Review"
            else:
                title = "Recent Feedback"
            
            # Web view - open in browser
            if args.web:
                _show_feedback_web(records, title, stats=None)
                return
            
            # Table format - compact view
            if args.table:
                _show_feedback_table(records, title)
                return
            
            # Default: detailed view with pager for large results
            output_lines = _format_feedback_detailed(records, title)
            
            # Use pager if output is large
            if len(records) > 10:
                _show_with_pager(output_lines)
            else:
                print('\n'.join(output_lines))
        else:
            # Just print raw output if format is unexpected
            print(output)
            
    except subprocess.CalledProcessError as e:
        log("Failed to query feedback database", "error")
        if e.stderr:
            print(e.stderr)
        sys.exit(1)


def _format_feedback_detailed(records: list, title: str) -> list:
    """Format records in detailed view, returns list of lines."""
    lines = []
    lines.append(f"\n{Colors.BOLD}📋 {title} ({len(records)} records){Colors.RESET}")
    lines.append("=" * 80)
    
    for i, record in enumerate(records, 1):
        # Status indicator
        if record['is_correct'] is None:
            status = f"{Colors.YELLOW}⏳ Pending{Colors.RESET}"
        elif record['is_correct']:
            status = f"{Colors.GREEN}✓ Correct{Colors.RESET}"
        else:
            status = f"{Colors.MAGENTA}✏️  Corrected{Colors.RESET}"
        
        # Format tools
        predicted_tools = record['predicted_tools'] or []
        tool_strs = [f"{t.get('tool', '?')}:{t.get('intention', '?')}" for t in predicted_tools]
        predicted_str = ", ".join(tool_strs) if tool_strs else "none"
        
        corrected_str = ""
        if record['corrected_tools']:
            corrected_tool_strs = [f"{t.get('tool', '?')}:{t.get('intention', '?')}" for t in record['corrected_tools']]
            corrected_str = f"\n      → Corrected: {Colors.CYAN}{', '.join(corrected_tool_strs)}{Colors.RESET}"
        
        # Truncate query
        query = record['query']
        if len(query) > 70:
            query = query[:67] + "..."
        
        lines.append(f"\n{Colors.BOLD}[{i}]{Colors.RESET} {status}")
        lines.append(f"    Query: {Colors.BOLD}{query}{Colors.RESET}")
        lines.append(f"    Predicted: {predicted_str}{corrected_str}")
        lines.append(f"    Character: {record['character']}")
        if record['notes']:
            lines.append(f"    Notes: {Colors.YELLOW}{record['notes']}{Colors.RESET}")
    
    lines.append("\n" + "=" * 80)
    return lines


def _show_feedback_table(records: list, title: str):
    """Show records in compact table format."""
    print(f"\n{Colors.BOLD}📋 {title} ({len(records)} records){Colors.RESET}\n")
    
    # Header
    print(f"{'#':>3} {'Status':^10} {'Query':<45} {'Predicted':<25}")
    print("-" * 85)
    
    for i, record in enumerate(records, 1):
        # Status
        if record['is_correct'] is None:
            status = "⏳ Pending"
        elif record['is_correct']:
            status = "✓ Correct"
        else:
            status = "✏️ Fixed"
        
        # Query (truncate)
        query = record['query'][:42] + "..." if len(record['query']) > 45 else record['query']
        
        # Tools (just show tool names, not intentions)
        tools = record['predicted_tools'] or []
        tool_names = [t.get('tool', '?')[:3] for t in tools]  # Abbreviate: char, sess, rule
        tools_str = ",".join(tool_names)[:24]
        
        print(f"{i:>3} {status:<10} {query:<45} {tools_str:<25}")
        
        # Show correction on next line if exists
        if record['corrected_tools']:
            corrected = [t.get('tool', '?')[:3] for t in record['corrected_tools']]
            print(f"{'':>3} {'':^10} {'→ Corrected to:':<45} {','.join(corrected):<25}")
    
    print("-" * 85)


def _show_feedback_web(records: list, title: str, stats: dict = None):
    """Generate and open an HTML view of feedback records."""
    import tempfile
    import webbrowser
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>ShadowScribe - Routing Feedback</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #9d4edd; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat {{ background: #16213e; padding: 15px 25px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ color: #888; }}
        table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }}
        th {{ background: #0f3460; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-top: 1px solid #333; }}
        tr:hover {{ background: #1f4068; }}
        .status-pending {{ color: #f39c12; }}
        .status-correct {{ color: #27ae60; }}
        .status-corrected {{ color: #9b59b6; }}
        .query {{ max-width: 400px; }}
        .tools {{ font-family: monospace; font-size: 0.9em; }}
        .correction {{ color: #3498db; margin-top: 5px; }}
        .filter-bar {{ margin-bottom: 20px; }}
        input[type="text"] {{ padding: 10px; width: 300px; border-radius: 5px; border: 1px solid #333; background: #16213e; color: #eee; }}
    </style>
</head>
<body>
    <h1>🎲 ShadowScribe - {title}</h1>
    
    <div class="filter-bar">
        <input type="text" id="search" placeholder="Filter queries..." onkeyup="filterTable()">
    </div>
    
    <table id="feedbackTable">
        <thead>
            <tr>
                <th>#</th>
                <th>Status</th>
                <th>Query</th>
                <th>Predicted Tools</th>
                <th>Character</th>
            </tr>
        </thead>
        <tbody>
'''
    
    for i, record in enumerate(records, 1):
        if record['is_correct'] is None:
            status_class = "status-pending"
            status_text = "⏳ Pending"
        elif record['is_correct']:
            status_class = "status-correct"
            status_text = "✓ Correct"
        else:
            status_class = "status-corrected"
            status_text = "✏️ Corrected"
        
        tools = record['predicted_tools'] or []
        tools_html = "<br>".join([f"{t.get('tool')}:{t.get('intention')}" for t in tools])
        
        correction_html = ""
        if record['corrected_tools']:
            corrected = "<br>".join([f"{t.get('tool')}:{t.get('intention')}" for t in record['corrected_tools']])
            correction_html = f'<div class="correction">→ {corrected}</div>'
        
        query_escaped = record['query'].replace('<', '&lt;').replace('>', '&gt;')
        
        html += f'''
            <tr>
                <td>{i}</td>
                <td class="{status_class}">{status_text}</td>
                <td class="query">{query_escaped}</td>
                <td class="tools">{tools_html}{correction_html}</td>
                <td>{record['character']}</td>
            </tr>
'''
    
    html += '''
        </tbody>
    </table>
    
    <script>
        function filterTable() {
            const filter = document.getElementById('search').value.toLowerCase();
            const rows = document.querySelectorAll('#feedbackTable tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        }
    </script>
</body>
</html>
'''
    
    # Write to temp file and open
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        temp_path = f.name
    
    webbrowser.open(f'file://{temp_path}')
    log(f"Opened feedback viewer in browser", "success")


def _show_with_pager(lines: list):
    """Show output with a pager (less) if available."""
    import tempfile
    
    content = '\n'.join(lines)
    
    # Try to use less with color support
    if shutil.which('less'):
        try:
            # Write to temp file to preserve colors
            process = subprocess.Popen(
                ['less', '-R', '-S'],  # -R for colors, -S for no wrap
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=content)
            return
        except Exception:
            pass
    
    # Fallback: just print
    print(content)


def _export_feedback(args, compose: list):
    """Export feedback records to JSONL for model training."""
    import json
    from pathlib import Path
    
    unexported_only = not args.all
    corrections_only = args.corrections
    
    # Build export command that runs inside the container
    python_code = """
import asyncio
import json
import sys
sys.path.insert(0, "/app")

from api.database.connection import AsyncSessionLocal, init_db
from api.database.repositories.feedback_repo import FeedbackRepository

UNEXPORTED_ONLY = """ + str(unexported_only) + """
CORRECTIONS_ONLY = """ + str(corrections_only) + """

async def main():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        repo = FeedbackRepository(db)
        
        records = await repo.get_for_training_export(
            include_corrections_only=CORRECTIONS_ONLY,
            include_confirmed_correct=True,
            unexported_only=UNEXPORTED_ONLY
        )
        
        examples = []
        record_ids = []
        
        for r in records:
            record_ids.append(r.id)
            tools = r.corrected_tools if r.corrected_tools else r.predicted_tools
            
            # user_query already has placeholders applied at storage time
            for tool_info in tools:
                examples.append({
                    'query': r.user_query,
                    'tool': tool_info['tool'],
                    'intent': tool_info['intention'],
                    'is_correction': r.corrected_tools is not None
                })
        
        print("EXPORT_JSON:" + json.dumps({"examples": examples, "record_ids": record_ids}))

asyncio.run(main())
"""
    
    try:
        result = run_command(
            compose + ["exec", "-T", "api", "python", "-c", python_code],
            capture_output=True,
            check=True
        )
        output = result.stdout
        
        if "EXPORT_JSON:" not in output:
            log("Unexpected output from export", "error")
            print(output)
            return
        
        export_line = [l for l in output.split('\n') if l.startswith("EXPORT_JSON:")][0]
        data = json.loads(export_line.replace("EXPORT_JSON:", ""))
        examples = data['examples']
        record_ids = data['record_ids']
        
        if not examples:
            log("No records to export", "info")
            return
        
        # Write to JSONL file
        output_file = Path(args.export)
        with open(output_file, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')
        
        # Count corrections vs confirmed
        corrections_count = sum(1 for e in examples if e.get('is_correction'))
        confirmed_count = len(examples) - corrections_count
        
        log(f"Exported {len(examples)} training examples to {output_file}", "success")
        print(f"   - From {len(record_ids)} feedback records")
        print(f"   - Corrections: {corrections_count}")
        print(f"   - Confirmed correct: {confirmed_count}")
        
        # Mark as exported (unless --no-mark)
        if not args.no_mark and record_ids:
            record_ids_str = str(record_ids)
            mark_code = f"""
import asyncio
import sys
sys.path.insert(0, "/app")

from api.database.connection import AsyncSessionLocal, init_db
from api.database.repositories.feedback_repo import FeedbackRepository

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        repo = FeedbackRepository(db)
        await repo.mark_as_exported({record_ids_str})
        await db.commit()
        print("MARKED")

asyncio.run(main())
"""
            run_command(
                compose + ["exec", "-T", "api", "python", "-c", mark_code],
                capture_output=True,
                check=True
            )
            print(f"   - Marked {len(record_ids)} records as exported")
            
    except subprocess.CalledProcessError as e:
        log("Failed to export feedback", "error")
        if e.stderr:
            print(e.stderr)
        sys.exit(1)


def _reprocess_feedback_entities(args, compose: list):
    """Re-extract entities and apply placeholders to existing feedback records."""
    
    # This script runs inside the container where all dependencies are available
    python_code = """
import asyncio
import json
import re
import sys
sys.path.insert(0, "/app")

from pathlib import Path
from api.database.connection import AsyncSessionLocal, init_db
from api.database.repositories.feedback_repo import FeedbackRepository
from sqlalchemy import update
from api.database.feedback_models import RoutingFeedback

# Import entity extraction components
from src.classifiers.gazetteer_ner import GazetteerEntityExtractor
from src.rag.character.character_manager import CharacterManager
from src.rag.session_notes.session_notes_storage import SessionNotesStorage


def apply_placeholders(query, character_name, entities):
    \"\"\"Apply placeholder substitution to query.\"\"\"
    replacements = []
    
    if character_name:
        replacements.append((character_name, '{CHARACTER}'))
        parts = character_name.split()
        if len(parts) > 0:
            first_name = parts[0]
            if first_name != character_name:
                replacements.append((first_name, '{CHARACTER}'))
            if len(first_name) > 4:
                replacements.append((first_name[:4], '{CHARACTER}'))
    
    if entities:
        for entity in entities:
            entity_type = entity.get('type', '')
            entity_text = entity.get('text', '') or entity.get('name', '')
            
            if not entity_text:
                continue
            
            placeholder = None
            if entity_type == 'CHARACTER':
                placeholder = '{CHARACTER}'
            elif entity_type == 'PARTY_MEMBER':
                placeholder = '{PARTY_MEMBER}'
            elif entity_type == 'NPC':
                placeholder = '{NPC}'
            
            if placeholder:
                replacements.append((entity_text, placeholder))
    
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    
    result = query
    for original_text, placeholder in replacements:
        pattern = re.compile(re.escape(original_text), re.IGNORECASE)
        result = pattern.sub(placeholder, result)
    
    return result


async def main():
    await init_db()
    
    # Initialize entity extractor with hardcoded paths
    cache_path = Path("src/classifiers/data/srd_cache")
    extractor = GazetteerEntityExtractor(cache_path)
    
    # Load character for context
    char_manager = CharacterManager()
    characters = char_manager.list_saved_characters()
    character = None
    if characters:
        character = char_manager.load_character(characters[0])
        print(f"Loaded character: {character.character_base.name if character and character.character_base else 'None'}")
    
    # Load session notes for context
    campaign_storage = None
    storage = SessionNotesStorage("knowledge_base/processed_session_notes")
    campaigns = storage.get_all_campaigns()
    if campaigns:
        campaign_storage = storage.get_campaign(campaigns[0])
        entity_count = len(campaign_storage.entities) if campaign_storage and campaign_storage.entities else 0
        print(f"Loaded campaign '{campaigns[0]}' with {entity_count} entities")
    
    # Add character context to extractor
    if character or campaign_storage:
        counts = extractor.add_character_context(character, campaign_storage)
        print(f"Added dynamic entities: {counts}")
    
    async with AsyncSessionLocal() as db:
        repo = FeedbackRepository(db)
        
        # Get all records
        records = await repo.get_recent(limit=1000)
        print(f"\\nProcessing {len(records)} feedback records...\\n")
        
        updated = 0
        for r in records:
            original_query = r.user_query
            
            # Re-extract entities from the query
            raw_entities = extractor.extract_simple(original_query)
            
            # Convert to storage format
            new_entities = [
                {
                    'name': e['canonical'],
                    'text': e['text'],
                    'type': e['type'],
                    'confidence': e['confidence']
                }
                for e in raw_entities
            ]
            
            # Apply placeholder substitution to the query
            new_query = apply_placeholders(original_query, r.character_name, new_entities)
            
            # Update the record with both new entities and placeholdered query
            await db.execute(
                update(RoutingFeedback)
                .where(RoutingFeedback.id == r.id)
                .values(
                    predicted_entities=new_entities,
                    user_query=new_query
                )
            )
            updated += 1
            
            # Show progress
            query_preview = new_query[:60] + "..." if len(new_query) > 60 else new_query
            entity_preview = [f"{e['text']}:{e['type']}" for e in new_entities[:3]]
            print(f"  [{updated}/{len(records)}] {query_preview}")
            if entity_preview:
                print(f"      entities: {entity_preview}")
        
        await db.commit()
        print(f"\\n✅ Done! Updated {updated} records with entities and placeholders.")

asyncio.run(main())
"""
    
    log("Re-processing entity extraction and applying placeholders...", "info")
    print()
    
    try:
        result = run_command(
            compose + ["exec", "-T", "api", "python", "-c", python_code],
            capture_output=False,  # Show progress in real-time
            check=True
        )
        log("Reprocessing complete!", "success")
    except subprocess.CalledProcessError as e:
        log("Failed to reprocess", "error")
        sys.exit(1)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ShadowScribe 2.0 Management Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage.py start           Start all services
  python manage.py logs -f api     Follow API logs
  python manage.py demo -q "What is my AC?"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start all services")
    start_parser.add_argument("--migrate", action="store_true", help="Run migrations after start")
    start_parser.set_defaults(func=cmd_start)
    
    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop all services")
    stop_parser.set_defaults(func=cmd_stop)
    
    # restart
    restart_parser = subparsers.add_parser("restart", help="Restart all services")
    restart_parser.add_argument("--migrate", action="store_true", help="Run migrations after restart")
    restart_parser.set_defaults(func=cmd_restart)
    
    # status
    status_parser = subparsers.add_parser("status", help="Show service status")
    status_parser.set_defaults(func=cmd_status)
    
    # logs
    logs_parser = subparsers.add_parser("logs", help="View service logs")
    logs_parser.add_argument("service", nargs="?", help="Service name (mysql, api, frontend)")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow log output")
    logs_parser.add_argument("-n", "--lines", type=int, default=100, help="Number of lines to show")
    logs_parser.set_defaults(func=cmd_logs)
    
    # health
    health_parser = subparsers.add_parser("health", help="Check service health")
    health_parser.set_defaults(func=cmd_health)
    
    # migrate
    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.set_defaults(func=cmd_migrate)
    
    # shell
    shell_parser = subparsers.add_parser("shell", help="Open interactive Python shell")
    shell_parser.set_defaults(func=cmd_shell)
    
    # demo
    demo_parser = subparsers.add_parser("demo", help="Run demo central engine")
    demo_parser.add_argument("-q", "--query", help="Query to run")
    demo_parser.add_argument("--quiet", action="store_true", help="Minimal output")
    demo_parser.set_defaults(func=cmd_demo)
    
    # build
    build_parser = subparsers.add_parser("build", help="Rebuild Docker images")
    build_parser.add_argument("service", nargs="?", help="Service to build")
    build_parser.add_argument("--no-cache", action="store_true", help="Build without cache")
    build_parser.set_defaults(func=cmd_build)
    
    # clean
    clean_parser = subparsers.add_parser("clean", help="Clean up Docker resources")
    clean_parser.add_argument("--volumes", action="store_true", help="Also remove volumes")
    clean_parser.add_argument("--images", action="store_true", help="Also remove images")
    clean_parser.set_defaults(func=cmd_clean)
    
    # feedback
    feedback_parser = subparsers.add_parser("feedback", help="View/manage routing feedback dataset")
    feedback_parser.add_argument("--stats", action="store_true", help="Show statistics only")
    feedback_parser.add_argument("--corrections", action="store_true", help="Show only user corrections")
    feedback_parser.add_argument("--pending", action="store_true", help="Show pending reviews only")
    feedback_parser.add_argument("-n", "--limit", type=int, default=20, help="Number of records to show")
    feedback_parser.add_argument("--export", type=str, metavar="FILE", help="Export to JSONL file")
    feedback_parser.add_argument("--all", action="store_true", help="Include already-exported records")
    feedback_parser.add_argument("--no-mark", action="store_true", help="Don't mark records as exported")
    feedback_parser.add_argument("--table", action="store_true", help="Compact table format")
    feedback_parser.add_argument("--web", action="store_true", help="Open in browser (HTML view)")
    feedback_parser.add_argument("--reprocess", action="store_true", help="Re-extract entities and apply placeholders to all records")
    feedback_parser.set_defaults(func=cmd_feedback)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print()
        log("Interrupted", "warning")
        sys.exit(130)
    except Exception as e:
        log(f"Error: {e}", "error")
        sys.exit(1)


if __name__ == "__main__":
    main()
