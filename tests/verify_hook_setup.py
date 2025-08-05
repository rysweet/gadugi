#!/usr/bin/env python3
"""
Verify TeamCoach hooks are properly set up and ready for use.
"""

import os
import json
import subprocess


def verify_setup():
    """Comprehensive verification of TeamCoach hook setup."""

    print("🔍 TeamCoach Hook Setup Verification")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(__file__))
    checks_passed = 0
    total_checks = 0

    # 1. Check hook files exist
    print("\n1️⃣  Checking hook files exist...")
    hooks = {
        "Stop Hook": ".claude/hooks/teamcoach-stop.py",
        "SubagentStop Hook": ".claude/hooks/teamcoach-subagent-stop.py",
    }

    for name, path in hooks.items():
        total_checks += 1
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path):
            print(f"   ✅ {name}: {path}")
            checks_passed += 1
        else:
            print(f"   ❌ {name}: NOT FOUND at {path}")

    # 2. Check hook permissions
    print("\n2️⃣  Checking hook permissions...")
    for name, path in hooks.items():
        total_checks += 1
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            print(f"   ✅ {name}: Executable")
            checks_passed += 1
        else:
            print(f"   ❌ {name}: Not executable")

    # 3. Check hook scripts have correct shebang
    print("\n3️⃣  Checking hook shebangs...")
    for name, path in hooks.items():
        total_checks += 1
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#!/") and "python" in first_line:
                    print(f"   ✅ {name}: Has Python shebang")
                    checks_passed += 1
                else:
                    print(f"   ❌ {name}: Missing or incorrect shebang")

    # 4. Check settings.json configuration
    print("\n4️⃣  Checking settings.json configuration...")
    settings_path = os.path.join(base_dir, ".claude", "settings.json")

    total_checks += 1
    if os.path.exists(settings_path):
        print("   ✅ settings.json exists")
        checks_passed += 1

        with open(settings_path, "r") as f:
            settings = json.load(f)

        # Check hooks section
        total_checks += 1
        if "hooks" in settings:
            print("   ✅ 'hooks' section present")
            checks_passed += 1

            # Check Stop hook
            total_checks += 1
            if "Stop" in settings["hooks"]:
                stop_config = settings["hooks"]["Stop"][0]["hooks"][0]
                if stop_config["command"].endswith("teamcoach-stop.py"):
                    print("   ✅ Stop hook configured correctly")
                    print(f"      • Command: {stop_config['command']}")
                    print(f"      • Timeout: {stop_config['timeout']}s")
                    checks_passed += 1
                else:
                    print("   ❌ Stop hook misconfigured")

            # Check SubagentStop hook
            total_checks += 1
            if "SubagentStop" in settings["hooks"]:
                subagent_config = settings["hooks"]["SubagentStop"][0]["hooks"][0]
                if subagent_config["command"].endswith("teamcoach-subagent-stop.py"):
                    print("   ✅ SubagentStop hook configured correctly")
                    print(f"      • Command: {subagent_config['command']}")
                    print(f"      • Timeout: {subagent_config['timeout']}s")
                    checks_passed += 1
                else:
                    print("   ❌ SubagentStop hook misconfigured")
        else:
            print("   ❌ 'hooks' section missing")
    else:
        print("   ❌ settings.json not found")

    # 5. Check hook script structure
    print("\n5️⃣  Checking hook script structure...")
    for name, path in hooks.items():
        total_checks += 1
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                content = f.read()

            required_elements = [
                ("invoke_teamcoach function", "def invoke_teamcoach"),
                ("main function", "def main()"),
                ("JSON output", "json.dumps"),
                ("continue action", '"action": "continue"'),
                ("claude invocation", "'/agent:teamcoach'"),
            ]

            all_present = True
            for element_name, search_str in required_elements:
                if search_str not in content:
                    all_present = False
                    print(f"   ❌ {name}: Missing {element_name}")
                    break

            if all_present:
                print(f"   ✅ {name}: Has all required elements")
                checks_passed += 1

    # 6. Check Claude command availability
    print("\n6️⃣  Checking Claude command availability...")
    total_checks += 1
    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Claude command found: {result.stdout.strip()}")
            checks_passed += 1

            # Get version
            version_result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True
            )
            if version_result.returncode == 0:
                print(f"      Version: {version_result.stdout.strip()}")
        else:
            print("   ❌ Claude command not found in PATH")
    except Exception as e:
        print(f"   ❌ Error checking claude: {e}")

    # Final summary
    print("\n" + "=" * 70)
    print(f"📊 VERIFICATION SUMMARY: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("\n✅ TeamCoach hooks are fully configured and ready!")
        print("   The hooks will automatically analyze performance when:")
        print("   • A Claude Code session ends (Stop hook)")
        print("   • A subagent completes its task (SubagentStop hook)")
        return True
    else:
        print(f"\n⚠️  Some checks failed ({total_checks - checks_passed} issues)")
        print("   Please review the issues above to ensure proper hook operation")
        return False


if __name__ == "__main__":
    success = verify_setup()
    exit(0 if success else 1)
