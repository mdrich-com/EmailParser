# Email Parser

This python script was designed for use in parsing large email exports from Thunderbird using the ImportExportTool plugin.

That plugin exports emails in a number of formats, including a single CSV of email contents and details, and HTML files, one per email. 

Email addresses are notoriously difficult to parse reliably and for the whole extent of what they can be (Special characters, domain names, multiple '.' that are ignored by some providers but not all). 

Thanks to this (https://emailregex.com/) guide and some friends helping me discover the complete extent of email naming limits, I've managed to produce a script that collects many emails from these exports and provides some analysis of the addresses.

This project was built for a project combing through hundreds of thousands of marketing emails. It's a quick and dirty build that will likely need fine tuning and reduction of redundancies, moving things to into classes and other functions called instead of rewritten.
## Features

- Extracts email addresses from CSV and HTML files (Specifically Thunderbird exports using ImportExportTools plugin)
- Produces list of unique email addresses
- Detects similar email addresses (≥90% similarity by default, modify with -s or --similarity) for later review
- Calculates probability of malformed email addresses utilizing tldextract
- Cross-platform compatible (Windows, macOS, Linux)
- Handles both single files and directories, including subdirectories
- Processes files and lines in batches
- Source file tracking for each email address
- Ability to supply a custom list of email addresses to exclude (internal emails, company emails, known bad emails, etc.)

## Requirements

- Python 3.6 or higher
- Dependencies:
  - tldextract: For domain and TLD validation
  - Built-in Python modules used:
    - csv: For CSV file handling
    - os: For operating system operations
    - sys: For system-specific parameters
    - re: For regular expression operations
    - time: For timing operations
    - typing: For type hints
    - datetime: For timestamp generation
    - pathlib: For file path handling
    - argparse: For command-line argument parsing
    - html.parser: For HTML parsing
    - difflib: For string similarity comparison
  - Exclude file should be a simple CSV containing one email per line
  - ImportExportTools plugin for Thunderbird is suggested. This is untested on other HTML and CSV sources. (See potential_improvements.md)

## Installation

1. Clone the repository or download the source code
2. Install required dependencies:
pip3 install tldextract
3. Run the script:
python3 email_parser.py [options] <file_or_directory> [-e] <exclude_file>