"""CLI entry point for BETA."""

import argparse
import sys

import altair as alt
import vl_convert as vlc

from beta.display import imgcat


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


def cmd_check() -> int:
    """Run setup check - display example chart."""
    print("BETA setup check")
    print("-" * 40)
    print("Generating example Altair chart...")

    chart = make_example_chart()
    png_data = vlc.vegalite_to_png(chart.to_dict())

    imgcat(png_data)

    print("If you see a bar chart above, setup is complete!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="beta",
        description="CLI agent for climbing data queries and visualizations",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify setup by displaying an example chart",
    )

    args = parser.parse_args()

    if args.check:
        return cmd_check()

    # Default: show help for now
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
