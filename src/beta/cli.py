"""CLI entry point for BETA."""

import argparse
import sys

import altair as alt
import vl_convert as vlc
from dotenv import load_dotenv

from beta.display import imgcat

# Load .env file (for ANTHROPIC_API_KEY, etc.)
load_dotenv()


def make_example_chart() -> alt.Chart:
    """Generate an example Altair chart to verify setup."""
    data = alt.Data(values=[
        {"grade": "V0", "count": 12},
        {"grade": "V1", "count": 18},
        {"grade": "V2", "count": 15},
        {"grade": "V3", "count": 10},
        {"grade": "V4", "count": 7},
        {"grade": "V5", "count": 4},
        {"grade": "V6", "count": 2},
    ])

    chart = alt.Chart(data).mark_bar(color="#e85d04").encode(
        x=alt.X("grade:N", sort=["V0", "V1", "V2", "V3", "V4", "V5", "V6"], title="Grade"),
        y=alt.Y("count:Q", title="Sends"),
    ).properties(
        title="Example: Sends by Grade",
        width=1000,
        height=600,
    )

    return chart


def cmd_check(_args: argparse.Namespace) -> int:
    """Run setup check - display example chart."""
    print("BETA setup check")
    print("-" * 40)
    print("Generating example Altair chart...")

    chart = make_example_chart()
    png_data = vlc.vegalite_to_png(chart.to_dict())

    imgcat(png_data)

    print("If you see a bar chart above, setup is complete!")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import data from Google Sheets."""
    from beta.import_sheets import import_all, HeaderMismatchError

    if not args.yes:
        print("This will replace all existing data in the database.")
        response = input("Continue? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return 0

    print("Importing from Google Sheets...")
    try:
        counts = import_all()
    except EnvironmentError as e:
        print(f"Error: {e}")
        return 1
    except HeaderMismatchError as e:
        print(f"Header validation failed: {e}")
        return 1

    print("Import complete:")
    for table, count in counts.items():
        print(f"  {table}: {count} rows")
    return 0


def cmd_chat(_args: argparse.Namespace) -> int:
    """Start interactive chat session."""
    from beta.repl import run_repl
    run_repl()
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Run a single query and exit."""
    from beta.agent import BetaAgent

    agent = BetaAgent()
    response = agent.send_message(args.query)
    print(response)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="beta",
        description="CLI agent for climbing data queries and visualizations",
    )
    subparsers = parser.add_subparsers(dest="command")

    # beta check
    check_parser = subparsers.add_parser("check", help="Verify setup by displaying an example chart")
    check_parser.set_defaults(func=cmd_check)

    # beta import
    import_parser = subparsers.add_parser("import", help="Import data from Google Sheets")
    import_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    import_parser.set_defaults(func=cmd_import)

    # beta chat
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat session")
    chat_parser.set_defaults(func=cmd_chat)

    # beta query "question"
    query_parser = subparsers.add_parser("query", help="Run a single query and exit")
    query_parser.add_argument("query", help="Query to run")
    query_parser.set_defaults(func=cmd_query)

    args = parser.parse_args()

    if hasattr(args, "func"):
        return args.func(args)

    # Default to chat if no command given
    return cmd_chat(args)


if __name__ == "__main__":
    sys.exit(main())
