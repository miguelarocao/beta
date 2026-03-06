"""Display images inline in iTerm2 using imgcat protocol."""

import base64
import os
import sys


def imgcat(data: bytes, filename: str = "chart.png") -> None:
    """Display image data inline in iTerm2.

    Uses iTerm2's proprietary escape sequence for inline images.
    Falls back to saving file path if not in iTerm2.
    """
    if "iTerm" not in (os.environ.get("TERM_PROGRAM") or ""):
        print(f"[Image saved but cannot display inline - not in iTerm2]")
        return

    b64_data = base64.b64encode(data).decode("ascii")

    # iTerm2 inline image protocol
    # \033]1337;File=[args]:base64data\007
    osc = "\033]"
    st = "\007"

    args = f"name={base64.b64encode(filename.encode()).decode()};inline=1"

    sys.stdout.write(f"{osc}1337;File={args}:{b64_data}{st}\n")
    sys.stdout.flush()
