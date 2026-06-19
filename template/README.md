# Keepsake page template

`index.html` is the master template for a Heartstrings Studio keepsake page.
To build a new page, copy it into a new folder (e.g. `the-song-name/index.html`)
and replace each `{{TOKEN}}` with that song's content.

## Intake variables

| Token                | What goes here                                                        |
|----------------------|----------------------------------------------------------------------|
| `{{SONG_TITLE}}`     | Song title (appears in the tab title, headline, video label, filenames). |
| `{{DEDICATION}}`     | The "For ___" dedication line under the title.                       |
| `{{OCCASION}}`       | Occasion label, e.g. *Celebration of Life*, *Military Tribute*.       |
| `{{ALBUM_ART}}`      | Album art as a base64 data URI (`data:image/png;base64,XXXX`).        |
| `{{YOUTUBE_ID}}`     | YouTube video ID (the part after `watch?v=`).                         |
| `{{STORY_BEHIND_IT}}`| The opening line of the story behind the song.                        |
| `{{LYRICS}}`         | Lyrics — one `<p class="stanza">` per section, `<br />` between lines. |
| `{{LYRICS_PDF}}`     | Lyric-sheet PDF as a base64 data URI (`data:application/pdf;base64,XXXX`). |
| `{{SONG_MP3}}`       | Song audio as a base64 data URI (`data:audio/mpeg;base64,XXXX`).      |

## Downloads section

The page ends (just before the footer) with a **Keepsake downloads** section
offering the lyric PDF and the MP3. Both files are embedded directly in the
page as base64 data URIs, so the whole keepsake still travels as a single
self-contained file and the downloads work even offline.

If a keepsake has no files to offer, delete the entire
`<!-- DOWNLOADS -->` … `</section>` block.

### Turning a file into a data URI

```bash
# Lyric sheet (PDF)
echo "data:application/pdf;base64,$(base64 -w0 lyrics.pdf)"

# Song (MP3)
echo "data:audio/mpeg;base64,$(base64 -w0 song.mp3)"
```

Paste the full `data:...` string in place of `{{LYRICS_PDF}}` / `{{SONG_MP3}}`.
(On macOS, use `base64 -i lyrics.pdf` — there is no `-w0` flag.)

Note: embedding an MP3 makes the HTML file several MB larger. That's expected
and keeps everything in one file.
