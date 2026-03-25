import argparse
import glob
import logging
import os
from pathlib import Path
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import sys
import time

__version__ = "2026.3.25.0"

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
    parser.add_argument("-l", type=str, help="Choose logging option", default="syslog", choices=["syslog","file","all","none"])
    parser.add_argument("-lf", help="If log is file/all need to specify file to log to")
    parser.add_argument("-d", type=str, help="Download directory to use", default=f"{Path.home() / 'Downloads'}")
    parser.add_argument("-u", type=str, help="File with links inside", default="urls.txt")
    parser.add_argument("-p", type=float, help="Specify already running Chrome Driver port", default=54321)
    parser.add_argument("-uh", type=bool, help="Use headless Chrome", default=False)
    parser.add_argument("-tl", type=float, help="How long to wait for webpage to load before timeout", default=10)
    parser.add_argument("-r", type=float, help="How often to refresh statistics on screen", default=2)
    parser.add_argument("-tw", type=float, help="Number of seconds to pause between downloads", default=4)
    parser.add_argument("-nm", type=bool, help="Do not monitor download statistics", default=False)
    parser.add_argument("-gc", type=int, help="Download cover image (0: don't download, 1: small, 2: large, 3: both)", default=0, choices=[0, 1, 2, 3])
    parser.add_argument("-v", action='store_true', help="Display version information")
    args = parser.parse_args()
    
    if args.v:
        sys.exit(f"v{__version__}\n")

    setup_logging(args.l, args.lf)

    download_dir = args.d
    url_file = args.u
    chrome_port = args.p
    headless = args.uh
    page_load_time = args.tl
    refresh_rate = args.r
    wait_time = args.tw
    monitor = args.nm
    cover = args.gc
    
    logging.info(f"Download Directory: {download_dir}")
    logging.info(f"Reading URLs from: {url_file}")
    logging.info(f"Using ChromeD Port: {chrome_port}")

    emessage = f""
    # URLs to process
    try:
        with open(url_file) as f:
            urls = [line.strip() for line in f]
    except Exception as e:
        emessage = f"Could not find url file: {e}!"
        logging.error(emessage)
        sys.exit(emessage)
    urls = list(dict.fromkeys(urls))
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
                    if args.l in ("syslog", "all"):
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
                return last_size, tsec
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
    total_size = 0
    total_time = 0
    failed_urls = []
    for url in urls:
        def download_it(monitor, wait_time, download_dir, total_size, total_time, cur_url, dtitle, durl, cover, ddisc=0):
            def download_img(download_dir, title, itype, baseurl):
                def save_img(download_dir, title, itype, iurl, baseurl, iform):
                    headers: dict[str, str] = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br, zstd',
                        'Connection': 'keep-alive',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0',
                        'Referer': f'{url}'
                    }
                    response = requests.get(iurl, headers=headers, allow_redirects=True, stream=True)
                    response.raise_for_status()
                    if response.status_code == 200:
                        fext = 'avif'
                        if iform == 2:
                            fext = 'webp'
                        save_path = os.path.join(download_dir, f"{title}.{fext}")
                        with open(save_path, 'wb') as file:
                            for chunk in response.iter_content(1024):
                                file.write(chunk)
                    else:
                        logging.warning(f"Could not download box image: {response.status_code} - {response.reason}")
                        pass
                try:
                    img_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//img[@alt="Box"]'))
                    )
                    if itype in [1,3]:
                        img_url = img_element.get_attribute('src')
                        if img_url:
                            save_img(download_dir, title, itype, img_url, baseurl, 1)
                        else:
                            logging.warning("No box image url found.")
                    if itype in [2,3]:
                        body_element = driver.find_element(By.TAG_NAME, "body")
                        img_element.click()
                        try:
                            dialog_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.ID, "imageDialog"))
                            )
                            img_element2 = dialog_element.find_element(By.TAG_NAME, "img")
                            img_url2 = img_element2.get_attribute('src')
                            if img_url2:
                                save_img(download_dir, title, itype, img_url2, baseurl, 2)
                            else:
                                logging.warning("No large box image found.")
                            actions = ActionChains(driver)
                            actions.move_to_element_with_offset(body_element, random.randint(1, 100), random.randint(1, 100)).click().perform()
                        except Exception as e:
                            logging.warning(f"No large box image found! {e}")
                except:
                    logging.warning("No box image exists. Skipping...")
            # Get Vimm file size
            size = 0
            try:
                size_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "dl_size"))
                )
                size_raw = size_element.text
            except:
                logging.warning("Could not determine download size from webpage")
                size_raw = '1 GB'
                pass
            logging.info(f"{title} {size_raw}")
            # Download box cover
            if cover > 0:
                raw_title = driver.title.replace("The Vault: ", "")
                download_img(download_dir, raw_title, cover, url)
            # Click Download button
            try:
                download_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Download']"))
                )
                download_button.click()
            except:
                logging.warning(f"Download button not found for {title}!")
                failed_urls.append(url)
                pass
            if " KB" in size_raw:
                size = float(size_raw.replace(" KB", "")) * 1024
            elif " MB" in size_raw:
                size = float(size_raw.replace(" MB", "")) * 1024 ** 2
            elif " GB" in size_raw:
                size = float(size_raw.replace(" GB", "")) * 1024 ** 3
            elif " TB" in size_raw:
                size = float(size_raw.replace(" TB", "")) * 1024 ** 4
            else:
                size = 500 * 1024 * 1024
            # Try to click Continue if it appears
            try:
                continue_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='Continue']"))
                )
                continue_button.click()
            except:
                pass
            # Monitor current download
            argmonitor = monitor
            argwait = wait_time
            ctime = 0
            csize = 0
            if size < 33554432:
                monitor = True
                wait_time = 15
                if total_size > 0 and total_time > 0:
                    wait_time = min((size / total_size / total_time) * 1.25, wait_time)
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
                csize, ctime = monitor_download(download_dir, size*1.01)
                total_size += csize
                total_time += ctime
            # Wait to call next URL
            if cur_url < url_length:
                if size < 33554432:
                    logging.warning(f"File size was too small to monitor! (Less than 32MB). Waiting {round(wait_time, 1)} seconds...")
                time.sleep(wait_time)
            else:
                if size < 33554432:
                    logging.warning(f"File size was too small to monitor! (Less than 32MB).")
            cur_url += 1
            monitor = argmonitor
            wait_time = argwait
            return csize, ctime
        # Open URL
        driver.get(url)
        # Wait to open URL
        wait = WebDriverWait(driver, page_load_time)
        # Multiple discs?
        try:
            disc_element = driver.find_element(By.ID, "disc_number")
            disc_select = Select(disc_element)
            url_length += len(disc_select.options) - 1
            for option in disc_select.options:
                disc_value = option.get_attribute("value")
                disc_text = option.get_attribute("text")
                disc_replace = f"{cur_url}/{url_length}: ({disc_text}) "
                if len(disc_select.options) == 1:
                    disc_replace = f"{cur_url}/{url_length}: "
                disc_select.select_by_value(disc_value)
                title = driver.title.replace("The Vault: ", disc_replace)
                osize, otime = download_it(monitor, wait_time, download_dir, total_size, total_time, cur_url, title, url, cover, disc_value)
                total_size += osize
                total_time += otime
                cur_url += 1
        except:
            title = driver.title.replace("The Vault: ", f"{cur_url}/{url_length}: ")
            osize, otime = download_it(monitor, wait_time, download_dir, total_size, total_time, cur_url, title, url, cover)
            total_size += osize
            total_time += otime
            cur_url += 1
    # Close Chrome session
    driver.quit()
    if total_size > 0:
        if total_time == 0:
            total_time = 1
        ttmin, ttmsec = divmod(total_time, 60)
        tavg_speed = round((total_size/total_time/1024/1024)*8, 1)
        logging.info(f"Downloaded {round((total_size/1024/1024), 2)}MB in {int(ttmin)}m {int(ttmsec)}s ({tavg_speed} Mbps).")
    if failed_urls:
        # Add URL links to a file
        fn = f"failed_downloads.txt"
        logging.warning(f"Writing failed downloads to {fn}")
        fnt = 'a'
        with open(f"{fn}", fnt) as f:
            for item in failed_urls:
                f.write(item + '\n')

if __name__ == "__main__":
    main()