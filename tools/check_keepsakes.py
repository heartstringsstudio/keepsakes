#!/usr/bin/env python3
"""Check the keepsakes repo before publishing.

    python3 tools/check_keepsakes.py
    python3 tools/check_keepsakes.py --strict   # warnings fail too (used on GitHub)

Checks every keepsake folder built in the audio-first layout (the page plays
song.mp3 from its own folder):

- song.mp3 must be there                            -> ERROR, exits 1
- art.jpg must be there                             -> ERROR, exits 1
- song.mp3 over 15 MB                               -> warning: re-export at 192 kbps
- page links video.mp4 but the file isn't there     -> ERROR, exits 1
- video.mp4 over 25 MB                              -> warning: re-export at 720p
  (GitHub's Upload files page won't take a bigger file)

And the repo as a whole:

- any video that isn't a page's own video.mp4      -> ERROR, exits 1
- total size of the published site, and of git history
- over 800 MB published                             -> warning: start a second keepsakes repo
  (GitHub Pages sites cap at 1 GB)

Older pages, with the song tucked inside index.html, are counted toward the
size but otherwise left alone.
"""

import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MB = 1024 * 1024
MP3_WARN = 15 * MB
VIDEO_WARN = 25 * MB
SITE_WARN = 800 * MB
SITE_CAP = 1024 * MB
VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mov")

# The audio-first page plays the song from its own folder.
AUDIO_FIRST = re.compile(r'<audio[^>]*\bsrc="song\.mp3"')
# ...and, on a keepsake delivery, the share video beside it.
LINKS_VIDEO = re.compile(r'href="video\.mp4"')


def published_files():
    """Every file the site would serve: everything outside .git."""
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            yield os.path.join(folder, name)


def git_history_bytes():
    try:
        out = subprocess.run(["git", "count-objects", "-v"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    sizes = dict(line.split(": ", 1) for line in out.strip().splitlines())
    return (int(sizes.get("size", 0)) + int(sizes.get("size-pack", 0))) * 1024


def mb(n):
    return "%.1f MB" % (n / MB)


def main(argv):
    strict = "--strict" in argv
    errors, warnings = [], []

    pages = sorted(d for d in os.listdir(ROOT)
                   if os.path.isfile(os.path.join(ROOT, d, "index.html")))
    page_videos = set()
    print("Keepsake pages")
    for slug in pages:
        folder = os.path.join(ROOT, slug)
        page = open(os.path.join(folder, "index.html"), encoding="utf-8").read()
        if not AUDIO_FIRST.search(page):
            print("  %-34s older layout, left as is" % slug)
            continue

        song = os.path.join(folder, "song.mp3")
        notes = []
        if not os.path.isfile(song):
            errors.append("%s/ is missing song.mp3. Drop the song in that folder, "
                          "named exactly song.mp3." % slug)
            notes.append("MISSING song.mp3")
        else:
            size = os.path.getsize(song)
            notes.append("song.mp3 " + mb(size))
            if size > MP3_WARN:
                warnings.append("%s/song.mp3 is %s, over 15 MB. Re-export it at 192 kbps "
                                "and replace the file." % (slug, mb(size)))
        video = os.path.join(folder, "video.mp4")
        if os.path.isfile(video):
            page_videos.add(video)
            size = os.path.getsize(video)
            notes.append("video.mp4 " + mb(size))
            if size > VIDEO_WARN:
                warnings.append("%s/video.mp4 is %s, over 25 MB. Re-export it at 720p "
                                "and replace the file." % (slug, mb(size)))
        elif LINKS_VIDEO.search(page):
            errors.append("%s/ is missing video.mp4. Drop the share video in that folder, "
                          "named exactly video.mp4." % slug)
            notes.append("MISSING video.mp4")
        if not os.path.isfile(os.path.join(folder, "art.jpg")):
            errors.append("%s/ is missing art.jpg. Drop the album art in that folder, "
                          "named exactly art.jpg." % slug)
            notes.append("MISSING art.jpg")
        print("  %-34s %s" % (slug, ", ".join(notes)))

    total = 0
    for path in published_files():
        total += os.path.getsize(path)
        if path.lower().endswith(VIDEO_EXTENSIONS) and path not in page_videos:
            errors.append("%s is a stray video. The only video a page uses is the "
                          "video.mp4 in its own folder: rename or delete this one."
                          % os.path.relpath(path, ROOT))

    print("\nSize")
    print("  Published site: %s of the 1 GB GitHub Pages limit (%d%%)"
          % (mb(total), round(100.0 * total / SITE_CAP)))
    history = git_history_bytes()
    if history is not None:
        print("  Git history:    %s" % mb(history))
    if total > SITE_WARN:
        warnings.append("The site is %s, past 800 MB. Time to start a second keepsakes "
                        "repo for new songs before it reaches the 1 GB limit." % mb(total))

    if warnings:
        print("\nWarnings")
        for w in warnings:
            print("  ! " + w)
    if strict and warnings:
        errors.extend(warnings)
    if errors:
        print("\nNot ready to publish")
        for e in errors:
            print("  x " + e)
        return 1
    print("\nAll good." if not warnings else "\nOK to publish, but see the warnings above.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
