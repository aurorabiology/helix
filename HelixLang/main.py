import sys
import argparse
import os

# Import CLI modules
from cli.helix_cli import main as cli_main
from cli.repl import start_repl
from cli.file_runner import run_file

# Import GUI launcher
from gui.helix_gui import launch_gui

# Settings management
from gui.settings import Settings

def main():
    parser = argparse.ArgumentParser(
        description="HelixLang: Next-gen biological computation platform"
    )
    parser.add_argument(
        "--version", action="version", version="HelixLang 1.0.0"
    )
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # Run a .hlx script or .hxir IR file
    run_parser = subparsers.add_parser("run", help="Run a HelixLang script or IR file")
    run_parser.add_argument("filepath", help="Path to .hlx or .hxir file")

    # Launch REPL interactive shell
    repl_parser = subparsers.add_parser("repl", help="Start interactive HelixLang shell")

    # Launch GUI app
    gui_parser = subparsers.add_parser("gui", help="Launch HelixLang GUI application")

    # Export command (optional, can delegate to CLI)
    export_parser = subparsers.add_parser("export", help="Export models/data")
    export_parser.add_argument("filepath", help="Source model file")
    export_parser.add_argument("--format", required=True, help="Export format (e.g. gltf, pdb)")

    # Simulation command
    sim_parser = subparsers.add_parser("simulate", help="Run simulation on input")
    sim_parser.add_argument("--protein", help="Protein identifier or file")
    sim_parser.add_argument("--duration", type=int, default=100, help="Simulation duration")

    # Settings management command
    settings_parser = subparsers.add_parser("settings", help="Manage HelixLang settings")
    settings_parser.add_argument("--show", action="store_true", help="Show current settings")
    settings_parser.add_argument("--reset", action="store_true", help="Reset settings to defaults")

    # Parse args
    args = parser.parse_args()

    # Settings instance
    settings = Settings()

    if args.command == "run":
        if not os.path.isfile(args.filepath):
            print(f"File not found: {args.filepath}")
            sys.exit(1)
        run_file(args.filepath)
    elif args.command == "repl":
        start_repl()
    elif args.command == "gui":
        launch_gui()
    elif args.command == "export":
        # Could invoke a CLI export function
        from cli.helix_cli import export_model
        export_model(args.filepath, args.format)
    elif args.command == "simulate":
        from cli.helix_cli import simulate_protein
        if not args.protein:
            print("Error: --protein required for simulation")
            sys.exit(1)
        simulate_protein(args.protein, args.duration)
    elif args.command == "settings":
        if args.show:
            for k, v in settings.all_settings().items():
                print(f"{k}: {v}")
        elif args.reset:
            settings.reset_to_defaults()
            print("Settings reset to defaults.")
        else:
            parser.print_help()
    else:
        # No command given: launch REPL by default or print help
        print("No command specified. Launching REPL by default.\n")
        start_repl()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting.")
        sys.exit(0)
