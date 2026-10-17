# Keepsake tooling

## Adding a new song (audio-first pages)

New keepsake pages play the song right on the page, so the client hears it
there first. Each song gets its own folder holding three files:

```
keepsakes/<page-code>/index.html   the page
keepsakes/<page-code>/art.jpg      square album art
keepsakes/<page-code>/song.mp3     the song (under 15 MB; 192 kbps is plenty)
```

1. **Export the song** as an MP3. If it comes out over 15 MB, re-export it at
   192 kbps.
2. **Open the Keepsake Builder** (it lives in the main site repo:
   `heartstringsstudio.github.io/heartstringsstudio/keepsake-builder.html`).
3. **Fill in the form**: title, dedication, occasion, story, lyrics, alt
   text. Pick the album art, the song MP3 and the lyric-sheet PDF.
   - **Video link** (optional): a Google Drive share link. Fill it in and the
     page shows a "Watch the video" button; leave it blank and there's no button.
   - **YouTube link** (optional): fill it in and a small "Also on YouTube"
     link sits at the very bottom. YouTube is never embedded.
4. Tick the client-approval box, then press **Download finished page**. The
   browser saves three files: `index.html`, `art.jpg`, `song.mp3` (say yes if
   it asks to allow several downloads). The bar above the preview shows the
   folder name, `keepsakes/<page-code>/`.
5. **Make that folder in this repo** and drop all three files into it. The
   names must stay exactly `index.html`, `art.jpg`, `song.mp3`.
6. **Publish**: on GitHub, **Add file → Upload files**, drag the whole folder
   in, and commit. The page is live at
   `https://heartstringsstudio.github.io/keepsakes/<page-code>/` a minute or
   two later.

That's all. Every upload is checked automatically (the "Check keepsakes"
workflow in `.github/workflows/`). If a page is missing `song.mp3` or
`art.jpg`, a video file got in, a song is over 15 MB, or the site has passed
800 MB, the check fails and GitHub emails you. It doesn't block publishing;
it tells you what to fix. To run the same check by hand:
`python3 tools/check_keepsakes.py`.

Videos never go in this repo, ever. `.gitignore` skips `.mp4`/`.mov` files
and the check script refuses them; put the video on Google Drive and use the
share link.

### The size limit

GitHub Pages sites cap at **1 GB**. The automatic check reports the site's
size on every upload and emails you once it passes **800 MB**. When it does, start a second
keepsakes repo for new songs. Older pages stay where they are, links and all.
A song at 192 kbps is about 5–8 MB, so that's roughly 100 more songs from here.

## Older pages

Pages published before the audio-first layout carry the song, art and lyric
sheet inside `index.html` and link the song out to YouTube. They're left
exactly as they are. `check_keepsakes.py` counts them toward the size and
otherwise ignores them.

## The share button

A delivered keepsake is one self-contained `index.html`: the album art, the
lyric-sheet PDF and the master MP3 all ride along inside it as base64. That is
what makes it a keepsake — the client can save the whole thing, and it keeps
working offline, forever, with no server behind it.

The client also wants to show the song to family and friends, and the
downloads are theirs rather than the whole world's. So each page carries a
**Share this song** button above the footer. It hands out the page's own
address with `?share` on the end:

```
https://heartstringsstudio.github.io/keepsakes/iseeyou/          the client's link
https://heartstringsstudio.github.io/keepsakes/iseeyou/?share    the one they share
```

Opened with that marker, the page hides the "Keepsake downloads" section (and
the in-page player, on pages that have one). Audio-first pages keep the player
for guests and hide only the "Download your song" button and the downloads. Everything else — the song, the
story, the lyrics, the artwork, the YouTube link — is exactly as it was. The
page also swaps a line of text, so the client reads *"the link you share opens
this page without your keepsake downloads on it"* and the person they sent it
to reads *"pass the song and the story along."*

The button tries the phone's own share sheet first, falls back to copying the
link, and failing both shows the link selected and ready to copy by hand.
Without JavaScript the button never appears and the plain link is shown
instead. `#share` works as well as `?share`.

### What this is and isn't

It **hides**; it does not remove. The MP3 and the PDF are inside the one file
either way, and someone determined could read them out of the page source.
That is the deliberate trade for keeping a keepsake a single self-contained
file. On audio-first pages it's even plainer: `song.mp3` sits at
its own public address next to the page. Treat it as what the client hands out, not as a privacy boundary — the
same caveat that already applies to `noindex` in `KEEPSAKE-OPERATIONS.md`.

Two consequences worth knowing:

- A shared link opened **with JavaScript off** shows the downloads, because
  nothing is there to apply the marker.
- The recipient still downloads the whole page, MP3 and all. On the larger
  keepsakes that is 8–13 MB over whatever signal they have.

If either becomes a real problem, the fix is a second, genuinely download-free
file rather than a hidden section — a bigger change, since the builder would
have to publish two files per keepsake.

### Adding it to a page

The block is injected by a script, and is safe to re-run — everything it
writes sits between `SHARE:BEGIN` / `SHARE:END` markers and is replaced in
place rather than stacked:

```sh
python3 tools/add_share_button.py                  # every keepsake
python3 tools/add_share_button.py iseeyou          # just one
python3 tools/add_share_button.py --check          # verify, write nothing
```

`--check` exits non-zero if any page is missing the block or has an outdated
one, so it works as a pre-commit or CI check.

`add_share_button.py` skips audio-first pages: they come out of the builder
with the share button already on them.

> The keepsake **builder** lives in the main site repo — see
> `KEEPSAKE-OPERATIONS.md` there. It emits the same share button on newly
> built pages, so this script is for keepsakes delivered before that landed,
> and for refreshing the block if the wording or styling changes.
