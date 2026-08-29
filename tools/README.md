# Keepsake tooling

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
the in-page player, on pages that have one). Everything else — the song, the
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
file. Treat it as what the client hands out, not as a privacy boundary — the
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

> The keepsake **builder** lives in the main site repo — see
> `KEEPSAKE-OPERATIONS.md` there. It emits the same share button on newly
> built pages, so this script is for keepsakes delivered before that landed,
> and for refreshing the block if the wording or styling changes.
