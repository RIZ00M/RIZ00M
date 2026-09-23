"""Everything you're likely to edit lives here."""
import os

USERNAME = os.environ.get("GH_USER", "RIZ00M")
HANDLE = USERNAME.lower()          # shown in the terminal prompt / title bars

# Info-card lines: (key, value). An empty key continues the previous line.
# Values must stay <= 38 characters or the card generator will refuse to build.
CARD = [
    ("Roles",     "Cyber Security"),
    ("",         "Aspiring Security Engineer"),
    ("Also",     "Software Engineering"),
    ("Building", "Domain Protection Algorithms"),
    ("Stack",    "Python, Bash, Linux, Docker"),
    ("Fav Tools",  "Nmap, Wireshark, Nuclei"),
    ("Into",     "CTFs, Threat Hunting, Purple Team"),
    ("Location", "United Kingdom"),
]

# Portrait source. MODE=logo colour-keys a flat background; MODE=photo uses rembg.
PORTRAIT_SRC = os.environ.get("PORTRAIT_SRC", "assets/source.png")
