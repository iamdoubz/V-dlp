import argparse
import glob
import logging
import os
from pathlib import Path
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import time

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
        description="V-dlp options and variables...",
        epilog="End of help documentation..."
    )
    #parser = argparse.ArgumentParser()
    parser.add_argument("--log", "-l", type=str, help="Choose logging option", default="syslog", choices=["syslog","file","all","none"])
    parser.add_argument("--logfile", "-lf", help="If log is file/all need to specify file to log to")
    parser.add_argument("--dir_download", "-d", type=str, help="Download directory to use", default=f"{Path.home() / 'Downloads'}")
    parser.add_argument("--file_urls", "-u", type=str, help="File with links inside", default="urls.txt")
    parser.add_argument("--chrome_port", "-p", type=float, help="Specify already running Chrome Driver port", default=54321)
    parser.add_argument("--use_headless", "-uh", type=bool, help="Use headless Chrome", default=False)
    parser.add_argument("--page_load_time", "-tl", type=float, help="How long to wait for webpage to load before timeout", default=10)
    parser.add_argument("--refresh_rate", "-r", type=float, help="How often to refresh statistics on screen", default=2)
    parser.add_argument("--wait_time", "-tw", type=float, help="Number of seconds to pause between downloads", default=4)
    parser.add_argument("--no_monitor", "-nm", type=bool, help="Do not monitor download statistics", default=False)
    parser.add_argument("--version", "-v", action='store_true', help="Display version information")
    args = parser.parse_args()
    
    if args.version:
        sys.exit(f"v{__version__}\n")

    setup_logging(args.log, args.logfile)

    download_dir = args.dir_download
    url_file = args.file_urls
    chrome_port = args.chrome_port
    headless = args.use_headless
    page_load_time = args.page_load_time
    refresh_rate = args.refresh_rate
    wait_time = args.wait_time
    monitor = args.no_monitor
    
    logging.info(f"Download Directory: {download_dir}")
    logging.info(f"Reading URLs from: {url_file}")
    logging.info(f"Using ChromeD Port: {chrome_port}")

    # URLs to process
    try:
        with open(url_file) as f:
            urls = [line.strip() for line in f]
    except:
        logging.error(f"Could not find url file: {url_file}!")
        raise FileNotFoundError(f"Could not find url file: {url_file}!")
    url_length = len(urls)
    cur_url = 1
    ess = "s"
    if url_length == 0:
        logging.warning("There are no URLs to process!")
        sys.exit("There are no URLs to process!")
    if url_length == 1:
        ess = ""
    logging.info(f"Will process {url_length} URL{ess}...")
    # If directory does not exist, create it
    os.makedirs(download_dir, exist_ok=True)
    # Generate list of random screen resolutions
    display_resolutions = ["2560,1440","1920,1080","1600,1200"]
    # Create and add Chrome options
    chrome_options = Options()
    if headless == True:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size=2560,1440")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    #driver = webdriver.Chrome(service=Service(r"C:\Tools\Standalone\chromedriver.exe"), options=chrome_options)
    #driver = webdriver.Remote(
    #    command_executor=f"http://127.0.0.1:{chrome_port}",
    #    options=chrome_options
    #)
    if headless == True:
        # Chrome sometimes blocks downloads in headless mode
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": download_dir
            }
        )
    # Helper to calculate percentages
    def percentage_of_total(part, whole):
        if whole == 0:
            return 0  # Handle division by zero case
        return round(((part / whole) * 100), 1)
    # Display useful stats about ongoing downloads
    def monitor_download(folder, fsize):
        downloading = True
        last_size = 0
        tstart = time.time()
        while downloading:
            files = os.listdir(folder)
            partial = [f for f in files if f.endswith(".crdownload")]
            if partial:
                file_path = os.path.join(folder, partial[0])
                size = os.path.getsize(file_path)
                tot_perc = percentage_of_total(size, fsize)
                if size != last_size:
                    ct = time.time()
                    dt = ct - tstart
                    if dt == 0:
                        dt = 1
                    speed = round(((size - last_size)/1024/1024/refresh_rate)*8, 2)
                    etas = ((fsize - size) / (size / dt))
                    etam, etams = divmod(etas, 60)
                    if args.log in ("syslog", "all"):
                        print(F"Downloading at {speed} Mbps... {tot_perc}%. ETA: {int(etam)}m {int(etams)}s       ", end="\r")
                last_size = size
                time.sleep(refresh_rate)
            else:
                downloading = False
                tsec = time.time() - tstart
                if tsec == 0:
                    tsec = 1
                tmin, tmsec = divmod(tsec, 60)
                avg_speed = round((fsize/tsec/1024/1024)*8, 1)
                logging.info(f"Downloaded {round((fsize/1024/1024), 2)}MB in {int(tmin)}m {int(tmsec)}s ({avg_speed} Mbps).")
    def wait_for_file(pattern, delay=1, max=15):
        #print(f"Waiting for file matching: {pattern}...")
        i = 0
        while not glob.glob(pattern):
            time.sleep(delay)
            i += 1
            if i > max:
                break
        # Return the first matching file
        return glob.glob(pattern)[0]
    # For each URL in the file, run program
    for url in urls:
        # Open URL
        driver.get(url)
        # Wait to open URL
        wait = WebDriverWait(driver, page_load_time)
        # Click Download button
        download_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Download']"))
        )
        download_button.click()
        # Output page title to console
        title = driver.title.replace("The Vault: ", f"{cur_url}/{url_length}: ")
        # Get Vimm file size
        size_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dl_size"))
        )
        size_raw = size_element.text
        logging.info(f"{title} {size_raw}")
        size = 0
        if " KB" in size_raw:
            size = float(size_raw.replace(" KB", "")) * 1024
        elif " MB" in size_raw:
            size = float(size_raw.replace(" MB", "")) * 1024 ** 2
        elif " GB" in size_raw:
            size = float(size_raw.replace(" GB", "")) * 1024 ** 3
        elif " TB" in size_raw:
            size = float(size_raw.replace(" GB", "")) * 1024 ** 4
        else:
            size = 500 * 1024 * 1024
        # Try to click Continue if it appears
        try:
            continue_button = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Continue']"))
            )
            continue_button.click()
        except:
            pass

        # Monitor current download
        argmonitor = monitor
        argwait = wait_time
        if size < 33554432:
            monitor = True
            wait_time = 17
            logging.warning("File size was too small to monitor! (Less than 32MB)")
        if monitor == False:
            tempTime = time.time()
            file_pattern = download_dir + '/*.crdownload'
            while not os.path.exists(wait_for_file(file_pattern)):
                if time.time() - tempTime > wait_time:
                    logging.warning("Never found temp file for download...")
                    break
                else:
                    logging.warning(f"{time.time() - tempTime}")
                    time.sleep(refresh_rate)
        if monitor == False:
            monitor_download(download_dir, size+1024)
        # Wait to call next URL
        time.sleep(wait_time)
        cur_url += 1
        monitor = argmonitor
        wait_time = argwait
    # Close Chrome session
    driver.quit()

if __name__ == "__main__":
    main()