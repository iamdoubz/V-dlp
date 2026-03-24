import argparse
import logging
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import string
import sys

__version__ = "2026.3.24.0"

# Helper for logging
def setup_logging(mode="syslog", logfile=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # remove default handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    if mode == "none":
        logging.disable(logging.CRITICAL)
        return
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    if mode in ("syslog", "all"):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        logger.addHandler(console)
    if mode in ("file", "all"):
        if not logfile:
            raise ValueError("File logging requires a logfile path")
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# Setup pass in arguments
def main():
    # Create the parser and add a description
    parser = argparse.ArgumentParser(
        description="V-dlp UG options and variables...",
        epilog="End of help documentation..."
    )
    parser.add_argument("--log", "-l", type=str, help="Choose logging option", default="syslog", choices=["syslog","file","all","none"])
    parser.add_argument("--logfile", "-lf", help="If log is file/all need to specify file to log to")
    parser.add_argument("--chrome_port", "-p", type=float, help="Specify already running Chrome Driver port", default=54321)
    parser.add_argument("--platform", type=str, help="Platform to generate list from (required, case sensitive)")
    parser.add_argument("--letter", type=str, help="The letter to search for matched roms (required)")
    parser.add_argument("--file", "-f", type=str, help="File with links inside", default="urls.txt")
    parser.add_argument("--min_rating", "-minr", type=float, help="Minimum rating to match (non-inclusive)", default=8.6)
    parser.add_argument("--max_rating", "-maxr", type=float, help="Maximum rating to match (non-inclusive)", default=10.1)
    parser.add_argument("--use_headless", "-uh", type=bool, help="Use headless Chrome", default=False)
    parser.add_argument("--version", "-v", action='store_true', help="Display version information")
    args = parser.parse_args()
    
    if args.version:
        sys.exit(f"v{__version__}")

    setup_logging(args.log, args.logfile)
    url_file = args.file
    chrome_port = args.chrome_port
    min_rating = args.min_rating
    max_rating = args.max_rating
    platform = args.platform
    letter = args.letter.upper()
    headless = args.use_headless
    message = f""
    
    if platform is None:
        message = f"Platform is a mandatory argument. i.e. PS2, Xbox, etc."
        logging.error(message)
        sys.exit(f"{message}\n")
    if letter is None:
        message = f"Letter is a mandatory argument. i.e. A, B, etc."
        logging.error(message)
        sys.exit(f"{message}\n")

    logging.info(f"Using ChromeD Port: {chrome_port}")
    logging.info(f"Platform: {platform}")
    logging.info(f"Letter: {letter}")
    logging.info(f"Min Rating: {min_rating}")
    logging.info(f"Max Rating: {max_rating}")

    # Generate list of random screen resolutions
    display_resolutions = ["2560,1440","1920,1080","1600,1200"]
    # Create and add Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={random.choice(display_resolutions)}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Remote(
        command_executor=f"http://127.0.0.1:{chrome_port}",
        options=chrome_options
    )
    
    # Function to read platform/letter and write links to file
    def get_links(pf, lets):
        driver.get(f"https://vimm.net/vault/{pf}/{lets}")
        data = []
        # Locate the main table
        table = driver.find_element(By.CSS_SELECTOR, "table.rounded")
        # Grab the second tbody
        try:
            tbody = table.find_elements(By.TAG_NAME, "tbody")[1]
            # Get all rows
            rows = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            logging.warning(f"Nothing found for {pf} and {lets}!")
            rows = []
            pass

        # Convert rating value to float
        def safe_to_float(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.1
        # Loop through table and add to array
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            name = cols[0].find_element(By.TAG_NAME, "a").text
            url = cols[0].find_element(By.TAG_NAME, "a").get_attribute("href")
            rating = cols[4].text
            data.append({
                "name": name,
                "url": url,
                "rating": rating
            })
        # Filter data
        rating_filter = [row for row in data if safe_to_float(row["rating"]) > min_rating and safe_to_float(row["rating"]) < max_rating]
        logging.info(rating_filter)
        # Add URL links to a file
        fn = f""
        fnt = 'w'
        if url_file is not None:
            if url_file == '':
                fn = f"{pf}-{lets}.txt"
            else:
                fn = f"{url_file}"
                fnt = 'a'
        else:
            fn = f"{pf}-{lets}.txt"
        with open(f"{fn}", fnt) as f:
            for item in rating_filter:
                f.write(item['url'] + '\n')
            

    if letter == 'ALL':
        for l in string.ascii_uppercase:
            get_links(platform, l)
    else:
        get_links(platform, letter)

    # Close Chrome session
    driver.quit()

if __name__ == "__main__":
    main()