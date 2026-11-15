"""Rich interactive CLI for HyperUnlock (Supporting Snapdragon 8 Gen 3 & 8 Gen 2)."""
import argparse
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .backup import BackupManager
from .device import ADB, Fastboot, UnlockError
from .offline import OfflineBypassEngine
from .official import OfficialUnlockClient, DATA_CENTERS, choose_zone
from .profiles import get_profile, list_profiles

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True)


def print_banner():
    banner = """[bold cyan]
    __  __                          __  __          __               __       ____   ______ _____
   / / / /__  __ ____   ___   _____/ / / /____     / /____   _____  / /__    ( __ ) / ____//__  /
  / /_/ // / / // __ \ / _ \ / ___// / / // __ \   / // __ \ / ___/ / //_/   / __  |/ / __   /_ < 
 / __  // /_/ // /_/ //  __// /   / /_/ // / / /  / // /_/ // /__  / ,<     / /_/ // /_/ / ___/ / 
/_/ /_/ \__, // .___/ \___//_/    \____//_/ /_/  /_/ \____/ \___/ /_/|_|    \____/ \____/ /____/  
       /____//_/                                                                                    
    [/bold cyan]
    [bold yellow]Universal Bootloader Unlock & Bypass Suite for Xiaomi SM8650 (8G3) & SM8550 (8G2)[/bold yellow]
    [dim]Author credits: @Kernix (Linuxoid-cn), @offici5l (MiForge), @MlgmXyysd[/dim]
    """
    console.print(banner)


def cmd_supported(args):
    """List all supported Snapdragon 8 Gen 3 and 8 Gen 2 devices."""
    print_banner()

    for soc_name, soc_title in [("SM8650", "Snapdragon 8 Gen 3 (SM8650)"), ("SM8550", "Snapdragon 8 Gen 2 (SM8550)")]:
        table = Table(title=f"Supported {soc_title} Devices", box=box.ROUNDED)
        table.add_column("Codename", style="cyan bold")
        table.add_column("Commercial Model", style="green")
        table.add_column("SoC", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Notes", style="white")

        for p in list_profiles(soc=soc_name):
            status = "[bold green]VERIFIED[/bold green]" if p.codename == "aurora" else "[cyan]SUPPORTED[/cyan]"
            notes = p.description
            if p.max_patch_date:
                notes += f" (Offline bypass up to {p.max_patch_date})"
            table.add_row(p.codename, p.commercial_name, p.soc, status, notes)

        console.print(table)
        console.print("")


def cmd_inspect(args):
    """Inspect connected device Fastboot status."""
    print_banner()
    fb = Fastboot(serial=args.serial)
    devices = fb.list_devices()
    if not devices:
        console.print("[bold red]❌ No device found in Fastboot mode.[/bold red]")
        console.print("Please put your phone/tablet into Fastboot mode (Hold Power + Volume Down) and connect via USB.")
        return 1

    serial = args.serial or devices[0]
    fb.serial = serial
    info = fb.inspect()
    product = info.get("product", "")
    profile = get_profile(product)

    table = Table(title=f"Connected Device Details ({serial})", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green bold")

    for k, v in info.items():
        table.add_row(k, str(v))

    if profile:
        table.add_row("Identified Model", f"{profile.commercial_name} ({profile.soc})")
        table.add_row("Compatibility", f"[bold green]YES ({profile.soc})[/bold green]")
    else:
        table.add_row("Identified Model", "[bold yellow]Unknown / Non-Qualcomm[/bold yellow]")
        table.add_row("Compatibility", "[bold red]NO (Restricted to SM8650 and SM8550)[/bold red]")

    console.print(table)
    return 0


def cmd_official(args):
    """Execute official server unlock via Xiaomi Account."""
    print_banner()
    fb = Fastboot(serial=args.serial)
    devices = fb.list_devices()
    if not devices:
        console.print("[bold red]❌ No device found in Fastboot mode.[/bold red]")
        console.print("Please put your device into Fastboot mode (Hold Power + Volume Down).")
        return 1

    serial = args.serial or devices[0]
    fb.serial = serial
    info = fb.inspect()
    product = info.get("product", "")

    if info.get("unlocked") == "yes":
        console.print("[bold green]✅ Device bootloader is ALREADY UNLOCKED![/bold green]")
        return 0

    console.print(Panel(
        f"[bold green]Connected Device:[/bold green] {product} ({serial})\n"
        f"[bold green]Server Zone:[/bold green] {args.zone}\n\n"
        "Official unlock requires logging into the Xiaomi Account currently bound to this device.",
        title="[bold yellow]Official Xiaomi Server Unlock[/bold yellow]",
        box=box.ROUNDED
    ))

    # Authenticate with migate
    try:
        from migate import get_dataCenterZone, get_passtoken, get_region, get_service
        console.print("[bold cyan]Please log in to your Xiaomi Account...[/bold cyan]")
        params = {"sid": "unlockApi", "checkSafeAddress": True}
        auth = get_passtoken(dict(params))
        if not auth:
            console.print("[bold red]❌ Login was cancelled or incomplete.[/bold red]")
            return 1
        service = get_service(auth, dict(params))
        if not service or not service.get("cookies") or not service.get("servicedata"):
            console.print("[bold red]❌ Could not obtain unlockApi service session.[/bold red]")
            return 1

        zone = args.zone
        if zone == "auto":
            region = get_region(auth)
            zone = choose_zone(region) if region else get_dataCenterZone(auth.get("userId", ""))
        if zone not in DATA_CENTERS:
            zone = "Singapore"

    except ImportError:
        console.print("[bold red]❌ migate library is missing. Install with 'pip install migate'.[/bold red]")
        return 1
    except Exception as e:
        console.print(f"[bold red]❌ Login failed:[/bold red] {e}")
        return 1

    user_id = service["cookies"].get("userId", "Unknown")
    console.print(f"[green]✅ Logged in as User ID:[/green] {user_id} (Data Center: {zone})")

    client = OfficialUnlockClient(fb, zone=zone)
    with console.status("[bold cyan]Requesting signed unlock ticket from Xiaomi server...[/bold cyan]"):
        try:
            signature = client.request_signature(service, product)
            console.print("[bold green]✅ Xiaomi Server granted unlock signature![/bold green]")
        except UnlockError as e:
            console.print(f"[bold red]❌ Server Request Failed:[/bold red] {e}")
            return 1

    console.print("[bold red]⚠️ Unlocking bootloader will factory reset the device and wipe all data.[/bold red]")
    if not Confirm.ask("Are you sure you want to unlock now?"):
        console.print("[yellow]Unlock cancelled by user.[/yellow]")
        return 0

    with console.status("[bold cyan]Sending unlock command to bootloader...[/bold cyan]"):
        try:
            success = client.unlock(signature)
            if success:
                console.print(Panel(
                    "[bold green]🎉 SUCCESS! Bootloader unlocked officially![/bold green]\n"
                    "Device is now unlocked and rebooting.",
                    title="[bold green]Unlocked[/bold green]",
                    box=box.ROUNDED
                ))
                fb.run("reboot", checked=False)
                return 0
            else:
                console.print("[bold red]❌ Unlock command sent, but device still reports locked.[/bold red]")
                return 1
        except Exception as e:
            console.print(f"[bold red]❌ Unlock command failed:[/bold red] {e}")
            return 1


def cmd_bypass(args):
    """Execute hardware-assisted offline bypass for SM8650/SM8550 devices."""
    print_banner()
    fb = Fastboot(serial=args.serial)
    engine = OfflineBypassEngine()

    try:
        profile, info = engine.get_device_profile(fb)
    except Exception as e:
        console.print(f"[bold red]❌ Pre-flight check failed:[/bold red] {e}")
        return 1

    console.print(Panel(
        f"[bold green]Target Device:[/bold green] {profile.commercial_name} ([cyan]{profile.codename}[/cyan])\n"
        f"[bold green]SoC:[/bold green] {profile.soc}\n"
        f"[bold green]Current Bootloader Status:[/bold green] {info.get('unlocked')}\n"
        f"[bold green]Anti-Rollback Version:[/bold green] {info.get('anti')}\n\n"
        "[bold red]⚠️ CRITICAL SAFETY NOTICE:[/bold red]\n"
        "1. This process will ERASE all user data on the device.\n"
        "2. A full official Fastboot ROM package is REQUIRED to restore the system.\n"
        "3. Stock GPT will be backed up automatically before any partition write.",
        title="[bold yellow]Device & Safety Assessment[/bold yellow]",
        box=box.ROUNDED
    ))

    if info.get("unlocked") == "yes":
        console.print("[bold green]✅ Device bootloader is ALREADY UNLOCKED![/bold green]")
        return 0

    # Safety check for patch limits on SM8550
    if profile.max_patch_date:
        console.print(f"[yellow]⚠️ Note: {profile.commercial_name} ({profile.soc}) offline bypass is validated on security patches up to {profile.max_patch_date}.[/yellow]")
        console.print("[dim]For newer patches, if ABL injection is blocked, please use 'python main.py official'.[/dim]\n")

    if not Confirm.ask("Do you have all personal data backed up and wish to proceed?"):
        console.print("[yellow]Operation cancelled by user.[/yellow]")
        return 0

    # Locate official ROM
    rom_dir = Path(args.rom_dir) if args.rom_dir else None
    while not rom_dir or not (rom_dir / "flash_all.bat").is_file():
        path_str = Prompt.ask("\nEnter absolute path to extracted Official Fastboot ROM folder")
        rom_dir = Path(path_str.strip().strip('"').strip("'"))
        if not (rom_dir / "flash_all.bat").is_file():
            console.print("[bold red]❌ flash_all.bat not found in that folder. Please check the path![/bold red]")

    # Validate ROM first
    with console.status("[bold cyan]Validating official ROM package and Anti-Rollback...[/bold cyan]"):
        try:
            commands = engine.verify_rom_directory(rom_dir, expected_anti=info.get("anti", "1"))
            console.print(f"[green]✅ Official ROM verified: {len(commands)} partition images validated.[/green]")
        except Exception as e:
            console.print(f"[bold red]❌ ROM verification failed:[/bold red] {e}")
            return 1

    # Stage 1: Payload
    console.print("\n[bold cyan]=== STAGE 1: Pre-flash Backup & Payload Execution ===[/bold cyan]")
    try:
        engine.run_stage_payload(fb, profile, progress_cb=lambda msg: console.print(f"  [yellow]•[/yellow] {msg}"))
    except Exception as e:
        console.print(f"[bold red]❌ Stage 1 failed:[/bold red] {e}")
        return 1

    console.print(Panel(
        "[bold yellow]👉 ACTION REQUIRED ON DEVICE:[/bold yellow]\n\n"
        "1. The screen will turn black as the Ennea payload executes in RAM.\n"
        "2. [bold]HOLD POWER + VOLUME DOWN[/bold] buttons simultaneously until the FASTBOOT screen reappears.\n"
        "3. Once the device is back in Fastboot mode, press Enter below to continue.",
        title="[bold cyan]Payload Booted[/bold cyan]",
        box=box.ROUNDED
    ))
    Prompt.ask("\nPress [bold green]Enter[/bold green] after your device is back on the FASTBOOT screen")

    # Wait for device
    with console.status("[bold cyan]Reconnecting to Fastboot...[/bold cyan]"):
        if not fb.wait_for_device(timeout=45):
            console.print("[bold red]❌ Device did not reconnect to Fastboot. Please check cable and driver.[/bold red]")
            return 1

    # Stage 2: Restore GPT and Flash ROM
    console.print("\n[bold cyan]=== STAGE 2: Restoring Stock GPT & Official Firmware ===[/bold cyan]")
    try:
        def cmd_progress(idx, total, cmd):
            console.print(f"  [dim][{idx}/{total}][/dim] [cyan]{cmd[0]}[/cyan] {' '.join(cmd[1:])[:60]}")

        engine.run_stage_restore(
            fb, profile, rom_dir,
            progress_cb=lambda msg: console.print(f"  [bold yellow]•[/bold yellow] {msg}"),
            cmd_cb=cmd_progress
        )
    except Exception as e:
        console.print(f"[bold red]❌ Stage 2 failed:[/bold red] {e}")
        console.print("[yellow]Tip: Use 'python main.py restore-gpt' if you need to restore partition:4 manually.[/yellow]")
        return 1

    console.print(Panel(
        "[bold green]🎉 CONGRATULATIONS! Bootloader Unlock & Restoration COMPLETED 100%![/bold green]\n\n"
        "• Stock GPT restored successfully.\n"
        "• Official HyperOS firmware flashed cleanly.\n"
        "• Bootloader state: [bold cyan]unlocked = yes[/bold cyan].\n"
        "• Device is rebooting into Android setup wizard.",
        title="[bold green]Success[/bold green]",
        box=box.ROUNDED
    ))
    return 0


def cmd_restore_gpt(args):
    """Emergency restore stock GPT to partition:4."""
    print_banner()
    fb = Fastboot(serial=args.serial)
    engine = OfflineBypassEngine()
    profile, _ = engine.get_device_profile(fb)

    _, stock_gpt = engine.get_gpt_files(profile)
    if Confirm.ask(f"Restore stock GPT to partition:4 for {profile.commercial_name}?"):
        engine.backup_mgr.restore_gpt(fb, stock_gpt)
        console.print("[bold green]✅ Stock GPT restored successfully![/bold green]")
    return 0


def cmd_assess(args):
    """Inspect Android device and evaluate compatibility."""
    print_banner()
    try:
        from .compatibility import inspect_android
        report = inspect_android(args.serial)
        console.print(Panel(
            f"Device Model: {report['properties'].get('ro.product.model')}\n"
            f"Device Codename: {report['properties'].get('ro.product.device')}\n"
            f"SoC Model: {report['properties'].get('ro.soc.model')}\n"
            f"Security Patch: {report['properties'].get('ro.build.version.security_patch')}\n"
            f"Status: {report.get('status')}\n"
            f"Assessment: {report.get('reason')}",
            title="[bold cyan]Android Compatibility Assessment[/bold cyan]",
            box=box.ROUNDED
        ))
    except Exception as e:
        console.print(f"[bold red]❌ Assessment failed:[/bold red] {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HyperUnlock: Universal Bootloader Unlock & Bypass Suite for Xiaomi SM8650 & SM8550",
    )
    parser.add_argument("--serial", help="Target device serial number")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("supported", help="List supported Snapdragon 8 Gen 3 & 8 Gen 2 devices")
    subparsers.add_parser("inspect", help="Inspect connected Fastboot device")
    subparsers.add_parser("assess", help="Inspect connected Android device and check patch compatibility")
    
    official_parser = subparsers.add_parser("official", help="Run official server unlock via Xiaomi Account")
    official_parser.add_argument("--zone", default="Singapore", choices=list(DATA_CENTERS.keys()) + ["auto"], help="Account data center")

    bypass_parser = subparsers.add_parser("bypass", help="Run hardware-assisted offline bypass for SM8650 / SM8550")
    bypass_parser.add_argument("--rom-dir", help="Path to extracted Official Fastboot ROM folder")

    subparsers.add_parser("restore-gpt", help="Emergency restore stock GPT layout")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        fb = Fastboot()
        if fb.list_devices():
            sys.exit(cmd_inspect(args))
        else:
            cmd_supported(args)
            parser.print_help()
            sys.exit(0)

    dispatch = {
        "supported": cmd_supported,
        "inspect": cmd_inspect,
        "assess": cmd_assess,
        "official": cmd_official,
        "bypass": cmd_bypass,
        "restore-gpt": cmd_restore_gpt,
    }

    if args.command in dispatch:
        sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
