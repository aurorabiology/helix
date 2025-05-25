# helixlang/cli/helix_cli.py

import sys
import argparse
import logging
from helixlang.runtime import run_script, simulate_protein, export_model
from helixlang.cli import repl
from helixlang.plugins import load_plugins

# Setup logger
logger = logging.getLogger("helixlang.cli")
def main():
    # your CLI argument parsing and dispatch logic here
    import argparse

    parser = argparse.ArgumentParser(description="HelixLang CLI")
    parser.add_argument("command", nargs="?", default="repl", help="Command to run (run, simulate, export, repl)")
    parser.add_argument("--version", action="version", version="HelixLang 1.0")
    args = parser.parse_args()

    if args.command == "repl":
        from cli.repl import repl_loop
        repl_loop()
    elif args.command == "run":
        # your run logic here
        pass
    # Add other commands accordingly

    # For demonstration, just print
    print(f"Running command: {args.command}")

def setup_logging(verbosity: int):
    level = logging.WARNING  # default
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=level)

def cmd_run(args):
    logger.info(f"Running HelixLang script: {args.file}")
    try:
        result = run_script(args.file)
        logger.info("Script executed successfully.")
        if args.output:
            with open(args.output, 'w') as f:
                f.write(str(result))
            logger.info(f"Output written to {args.output}")
    except Exception as e:
        logger.error(f"Error running script: {e}")
        sys.exit(1)

def cmd_simulate(args):
    logger.info(f"Running simulation on protein: {args.protein}")
    try:
        result = simulate_protein(args.protein, duration=args.duration)
        logger.info(f"Simulation completed. Total energy: {result.total_energy}")
        if args.output:
            with open(args.output, 'w') as f:
                f.write(str(result))
            logger.info(f"Simulation output saved to {args.output}")
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        sys.exit(1)

def cmd_export(args):
    logger.info(f"Exporting model from {args.file} as {args.format}")
    try:
        model = run_script(args.file)  # Or a dedicated loader
        export_model(model, args.format, args.output)
        logger.info("Export successful.")
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)

def cmd_repl(args):
    logger.info("Launching HelixLang interactive shell...")
    try:
        repl.start_shell()
    except Exception as e:
        logger.error(f"REPL error: {e}")
        sys.exit(1)

def cmd_version(args):
    print("HelixLang version 1.0.0")

def main():
    parser = argparse.ArgumentParser(
        description="HelixLang CLI - Biological Programming Language"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity (e.g., -v, -vv)")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # run command
    parser_run = subparsers.add_parser("run", help="Run a HelixLang script")
    parser_run.add_argument("file", help="HelixLang script file path")
    parser_run.add_argument("-o", "--output", help="Save script output to file")
    parser_run.set_defaults(func=cmd_run)

    # simulate command
    parser_sim = subparsers.add_parser("simulate", help="Run simulation")
    parser_sim.add_argument("--protein", required=True, help="Protein accession or sequence")
    parser_sim.add_argument("-d", "--duration", type=int, default=100, help="Simulation duration")
    parser_sim.add_argument("-o", "--output", help="Save simulation results")
    parser_sim.set_defaults(func=cmd_simulate)

    # export command
    parser_exp = subparsers.add_parser("export", help="Export model in various formats")
    parser_exp.add_argument("file", help="Model input file")
    parser_exp.add_argument("-f", "--format", choices=["gltf", "pdb", "json", "obj"], default="gltf")
    parser_exp.add_argument("-o", "--output", required=True, help="Export output file path")
    parser_exp.set_defaults(func=cmd_export)

    # repl command
    parser_repl = subparsers.add_parser("repl", help="Launch interactive REPL")
    parser_repl.set_defaults(func=cmd_repl)

    # version command
    parser_version = subparsers.add_parser("version", help="Show version info")
    parser_version.set_defaults(func=cmd_version)

    # Load plugins if any (example, no-op if none)
    load_plugins()

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)
    args.func(args)

if __name__ == "__main__":
    main()
