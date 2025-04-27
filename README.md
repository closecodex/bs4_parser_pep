# Python Documentation Parser💻

## Project Description

**This project is a parser for various sections of the Python documentation.
The parser supports multiple operating modes, which can be selected via command-line arguments.
It is designed to gather up-to-date information about the development of Python and save the results in a convenient format.**

## Installation and Setup

1. **Clone the repository:**
    
    ```bash
    git clone git@github.com:closecodex/bs4_parser_pep.git
    cd bs4_parser_pep
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv\Scripts\activate
    ```

3. **Upgrade pip and install dependencies:**
   
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Positional Arguments:

1. **whats-new: Parse the "What's New" section of Python documentation.**

2. **latest-versions: Collect information about the latest Python versions.**

3. **download: Download PDF documentation.**

4. **pep: Parse the statuses of PEP documents.**

## Running the Project

To run the parser, use the following command:

   ```bash
   python main.py <argument>
   ```

## Accessing Help

To see available arguments and options, use the -h flag::

   ```bash
   python main.py -h
   ```

## Additional Information

1. **Автор: Mariia Osmolovskaia (closecodex@github.com)**

2. **Tech Stack: Python, BeautifulSoup4, requests, argparse, logging**
