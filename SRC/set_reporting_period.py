# PROPLENS REPORTING PERIOD ENTRY POINT
#
# This deliberately tiny script makes the date-selection step easy to run
# from the command line and from update_all.py. The actual calculation lives
# in reporting_window.py so other scripts can reuse the same logic.

# Select and save the common reporting window before generating reports.
from reporting_window import save_window

if __name__ == "__main__":
    save_window()
