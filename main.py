"""Game Manager - Entry point."""

import sys

# Ensure project root is on the path when run directly
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
