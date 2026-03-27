| [![V-dlplogo.png](helpers/V-dlpwide.png)](helpers/V-dlpwide.png) |
| :---: |

# V-dlp

A program to aid in queuing downloads from Vimm.net

## Prerequisites

### Shared

- [Google Chrome](https://www.google.com/chrome/)
- ~~[Chromedriver](https://googlechromelabs.github.io/chrome-for-testing/)~~

### Source

- Python 3.11 (others might work)
- Selenium `pip install selenium`
- Results `pip install results`
- Pathlib ` pip install pathlib`
- Pathvalidate `pip install pathvalidate`

## Programs

### V-dlp UG (URL Generator)

V-dlp UG can be used to generate a list of URL's to download given a few inputs.

#### Switches/arguments

| Arg | Descr. | Options | Default |
| :--- | :------ | :------- | :--- |
| -l | Choose logging option | ["syslog","file","all","none"] | syslog |
| -lf | If log is file/all need to specify file to log to | NA | none |
| -p | Specify already running Chrome Driver port | int | 54321 |
| --platform | Platform to generate list from (required, case sensitive) | string: PS1, Atari2600, etc. | none |
| --letter | The letter to search for matched roms (required) | string: A-Z, all | none |
| -f | File with links inside (where to save URLs found) | str: platform_letter.txt | urls.txt |
| -minr | Minimum rating to match (non-inclusive) | float | 8.6 |
| -maxr | Maximum rating to match (non-inclusive) | float | 10.1 |
| -uh | Use headless Chrome (If you do not want to use, do not pass in the flag) | boolean | False |
| -v | Display version information | NA | none |

### V-dlp (downloader)

V-dlp will parse a file and attempt to download each one at a time.

#### Switches/arguments

| Arg | Descr. | Options | Default |
| :--- | :------ | :------- | :--- |
| -l | Choose logging option | ["syslog","file","all","none"] | syslog |
| -lf | If log is file/all need to specify file to log to | NA | none |
| -p | Specify already running Chrome Driver port | int | 54321 |
| -u | File with links inside | str | urls.txt |
| -d | Download directory to use | str | %HOME%\Downloads |
| -r | How often to refresh statistics on screen | float | 2 |
| -tw | Number of seconds to pause between downloads | float | 4 |
| -nm | Do not monitor download statistics (set flag to True for small downloads <32MB) | boolean | False |
| -uh | Use headless Chrome (If you do not want to use, do not pass in the flag) | boolean | False |
| -gc | Download cover image (0: don't download, 1: small, 2: large, 3: both) | int | 0 |
| -v | Display version information | NA | none |

## Features

- [X] Download files
- [X] Handle multi-disc downloads
- [X] Download box cover art
- [X] Show download statistics (speed, ETA)
- [X] More download statistics
- [X] Show number of URLs
- [X] Show download name/size
- [X] Add headless option
- [X] Remove dependency of Chrome Driver
- [X] Show failed downloads
- [X] Remove duplicate URLs
- [X] Get all links (#, A-Z)
- [X] No more waiting for each download to finish

## Upcoming features

- [ ] Proper error handling
- [ ] Download manuals
- [ ] Email upon completion
- [ ] Click on ads
- [ ] OS agnostic (heavily Windows based as they need the most hand holding)


## Bonus

Powershell script to extract zips, delete zips, convert .cue, .gdi, .iso to .chd. `chd.ps1`

## Example executions

Create a list for all Atari2600 games.

```
python links.py --platform Atari2600 --letter all -f atari26roms.txt
```

Download the games.

```
python dlp.py -nm True -uh True -tw 1 -u atari26roms.txt
```

**NOTE**: if you are using the release, substitute "V-dlp" for "python dlp.py".

## Why was this created?

iamdoubz wanted to learn how to use python, selenium, and get data from a website. iamdoubz did not know where to start and generated a few lines of code using AI, then added the rest using StackOverflow and Google.