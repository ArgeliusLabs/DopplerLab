# Quick start: download, run, inspect

**Goal:** generate a fictional recording and open your first Doppler report.
Allow about five minutes after downloading; startup can take longer on some systems.
Python is bundled with the executable. This example runs offline and generates its own
audio and flight tracks. No flight-data account or FFmpeg is needed for the practice.

**Experimental — testing in progress.** This practice uses generated audio. Successful
practice does not establish real-world location accuracy: the
[first original-recording test](docs/FIELD_TEST_2026_11.md) returned insufficient evidence.
Treat search results as hypotheses requiring independent evidence.

## 1. Download your build

Use the [v0.4.1 release](https://github.com/ArgeliusLabs/DopplerLab/releases/tag/v0.4.1).
Choose one native archive, then extract it into a folder you can write to, such as Downloads:

| Your computer | Download |
| --- | --- |
| Windows, Intel/AMD 64-bit | [Windows ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.1/doppler-lab-0.4.1-windows-x86_64.zip) |
| Mac with Apple Silicon, such as M1/M2/M3/M4 | [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.1/doppler-lab-0.4.1-macos-arm64.tar.gz) |
| Mac with an Intel processor | [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.1/doppler-lab-0.4.1-macos-x86_64.tar.gz) |
| Linux, Intel/AMD 64-bit | [Linux archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.1/doppler-lab-0.4.1-linux-x86_64.tar.gz) |

The native archive contains the executable. GitHub's automatic **Source code** downloads
contain source, not a precompiled application. Keep the bundled license files.
See [platform requirements and checksum instructions](docs/BINARIES.md) if needed.
These commands also work with earlier 0.2.x binaries.

## 2. Open a terminal in the executable's folder

Open the extracted folder until you see `doppler-lab.exe` on Windows, or `doppler-lab`
on macOS/Linux. Some extraction tools create an extra outer folder. The application is
a command-line tool; double-clicking it is not how you start the exercise.

Open **PowerShell** on Windows, or **Terminal** on macOS/Linux. Use `cd` to enter the
folder containing that executable, replacing the example path with your actual path:

Windows PowerShell:

```powershell
cd "C:\path\to\folder-containing-doppler-lab.exe"
```

macOS/Linux:

```bash
cd "/path/to/folder-containing-doppler-lab"
```

The commands below use relative paths, so stay in this folder. Run one line at a time
and wait for it to finish. A one-file executable unpacks its runtime at each startup;
the first command can take a while before printing anything.

## 3. Generate and analyze the practice case

Choose **one** block for your OS. `practice/case` and `practice/report` must be new or empty.

Windows PowerShell:

```powershell
.\doppler-lab.exe --version
.\doppler-lab.exe demo --seed 7 --output practice/case
.\doppler-lab.exe run practice/case/case.json --output practice/report
Start-Process "practice/report/report.html"
```

macOS/Linux:

```bash
./doppler-lab --version
./doppler-lab demo --seed 7 --output practice/case
./doppler-lab run practice/case/case.json --output practice/report
```

Then open the report on macOS:

```bash
open practice/report/report.html
```

Or on a Linux desktop:

```bash
xdg-open practice/report/report.html
```

You can also open `practice/report/report.html` with your browser's file-open command.
On a machine without a desktop, copy the HTML file to a computer with a browser; its
plots are embedded. No local web server is needed.

**Checkpoint:** the version should say `0.4.1`; earlier 0.2.x binaries also support these commands.
The report should show **289 declared locations**, **2 independent flyovers**, a
spectrogram, a location score map, and **Accepted location: no**. That last label is
expected: a ranked hypothesis is not an independently verified location.

## 4. Know what you created

| File | Purpose |
| --- | --- |
| `practice/case/recording.wav` | Original generated, fictional audio; open with an audio player |
| `practice/case/tracks.csv` | Fictional aircraft trajectories and decoys |
| `practice/case/case.json` | Audio windows, search bounds and model settings |
| `practice/case/truth.json` | Hidden fictional answer; leave closed until the evaluation step |
| `practice/report/report.html` | Your self-contained report |
| `practice/report/results.json` | Detailed machine-readable results and input hashes |
| `practice/report/candidates.csv` | Full local grid of ranked hypotheses |

Continue with the [15–20 minute guided practice](docs/PRACTICE.md). It uses this case,
shows where to look in the report, and adds a noise-only comparison. For the longer
course exercise, see the [110-minute lab](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/STUDENT_LAB.md).

## If something does not work

| What you see | What to do |
| --- | --- |
| “Not recognized” or “No such file” | Check that `cd` put you in the folder containing the executable. Keep the `./` or `.\` prefix. |
| A window opens and closes | Start from PowerShell/Terminal so the output stays visible. |
| “Use an empty output directory” | Preserve the previous run. Replace `practice` with `practice-02` in **every** path in the command block. |
| A macOS/Linux executable lost its execute permission | In its folder, use `chmod u+x ./doppler-lab`, then retry. This does not bypass operating-system trust checks. |
| The OS blocks the unsigned application | Read [native-build limitations](docs/BINARIES.md). Do not disable system protections; the [source installation route](https://github.com/ArgeliusLabs/DopplerLab#install-from-source-optional) is also available. |
| The report did not open automatically | Open the HTML file directly in a browser. Check the terminal for an earlier error. |

For a different failure, keep the complete error, OS, tool version and command when
[reporting an issue](https://github.com/ArgeliusLabs/DopplerLab/issues).

## After the practice

Start an original video with the bundled [recording walkthrough](docs/REAL_RECORDING.md).
Version 0.4.1 can review a long recording and retrieve a small historical flight window:

```powershell
.\doppler-lab.exe review-media "C:\recordings\owned-video.mov" --output work\review-01
Start-Process "work\review-01\review.html"
```

This command needs separate FFmpeg/ffprobe executables. The walkthrough covers timestamp
review, both audio channels, `download-window`, terrain and case preparation. Read the
[first field-test outcome](docs/FIELD_TEST_2026_11.md): the real pipeline ran, but the
recording did not support an accepted location.

For an original recording, follow the
[investigation workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/INVESTIGATION_WORKFLOW.md)
and [data-preparation guide](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/DATA.md).
Video extraction needs a separate FFmpeg installation. A real case also needs supported
recording times, flight data and analyst-selected audio events. The fictional demo does
not automatically analyze an arbitrary video.

For terrain, follow the bundled [DEM download and preparation guide](docs/TERRAIN.md).
The tool can retrieve USGS elevation tiles and apply their heights during broad
screening and detailed local preparation. Download once, then reuse the files offline.
