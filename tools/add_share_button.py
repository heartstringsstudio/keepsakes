#!/usr/bin/env python3
"""Add the "Share this song" button to delivered keepsake pages.

A keepsake ships as one self-contained index.html: the album art, the
lyric-sheet PDF and the master MP3 all ride along inside it as base64. That is
what makes it a keepsake -- the client can save the whole thing and it keeps
working forever, with no server behind it.

But the client also wants to show the song to family and friends, and the
downloads are theirs, not the whole world's. So the Share button hands out the
page's own URL with `?share` on the end, and the page hides the keepsake
downloads (and the in-page player, on pages that have one) when it sees that
marker.

This hides; it does not remove. The MP3 and the PDF are still inside the one
file either way, and someone determined could read them out of the page
source. That is the deliberate trade for keeping the keepsake a single file
and the builder's workflow untouched -- it is what the client hands out, not a
privacy boundary.

Everything injected sits between SHARE:BEGIN / SHARE:END markers, so running
this again updates the block in place instead of stacking copies.

Usage:  python3 tools/add_share_button.py [slug ...]
        python3 tools/add_share_button.py --check     # verify, write nothing
"""

import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://heartstringsstudio.github.io/keepsakes"

# ----------------------------------------------------------------- fragments

HEAD = """  <!-- SHARE:HEAD:BEGIN -->
  <!-- A shared link carries ?share (or #share). Marking the page here, before
       anything renders, is what keeps the keepsake downloads from flashing up
       on someone else's screen before the stylesheet can hide them. -->
  <script>(function(){try{var m=window.location.search+window.location.hash;if(/(?:^|[?&#])share(?:[=&]|$)/.test(m)){document.documentElement.className+=" sharing";}}catch(e){}})();</script>
  <!-- SHARE:HEAD:END -->
"""

CSS = """
    /* ---------- Share ---------- */
    /* SHARE:BEGIN */
    /* What a shared link leaves out. The files are still inside this one
       file -- this is what the client hands out, not a privacy boundary. */
    html.sharing section[aria-labelledby="downloads-heading"],
    html.sharing section[aria-labelledby="listen-heading"] { display: none; }

    .share { max-width: 460px; margin: 0 auto; text-align: center; }
    .share-note {
      font-family: var(--serif); font-style: italic;
      font-size: 1.08rem; line-height: 1.6;
      color: var(--text-muted); margin: 0 0 1.7rem;
    }
    /* The page says one thing to the client and another to the person they
       sent it to. Swapped in CSS so it costs no extra script. */
    .share-note-guest { display: none; }
    html.sharing .share-note-owner { display: none; }
    html.sharing .share-note-guest { display: block; }

    /* The button only does something with scripts, so scripts are what
       reveal it. Without them the plain link below is shown instead. */
    .share-btn { display: none; }
    .share.share-ready .share-btn { display: inline-block; }
    .share-btn {
      font-family: var(--serif); font-style: italic; font-weight: 600;
      letter-spacing: 0.04em; font-size: 1.08rem;
      color: var(--rose-deep); background: transparent;
      border: 1px solid rgba(192,69,90,0.5);
      padding: 0.85rem 2.5rem; cursor: pointer;
      transition: color 0.4s var(--ease), background-color 0.4s var(--ease),
                  border-color 0.4s var(--ease), transform 0.3s var(--ease);
    }
    /* Filling with --rose-deep, not --rose: cream text needs the darker one
       to stay readable at every weight of the palette. */
    .share-btn:hover { color: var(--cream); background: var(--rose-deep); border-color: var(--rose-deep); transform: translateY(-1px); }
    .share-btn:focus-visible { outline: 2px solid var(--rose); outline-offset: 3px; }
    /* Reserved height so the confirmation does not shove the footer down. */
    .share-status {
      min-height: 1.6em; margin: 1rem 0 0;
      font-family: var(--serif); font-style: italic;
      font-size: 1rem; color: var(--rose-deep);
    }
    .share-link { margin: 1.2rem 0 0; }
    .share.share-ready .share-link { display: none; }
    .share.share-ready .share-link.is-shown { display: block; }
    .share-link input {
      width: 100%; padding: 0.7rem 0.8rem;
      font-family: var(--sans); font-size: 0.9rem; color: var(--text-body);
      background: var(--cream-warm); border: 1px solid rgba(184,149,106,0.42);
      border-radius: 2px; text-align: center;
    }
    .share-link input:focus-visible { outline: 2px solid var(--rose); outline-offset: 2px; }
    @media (prefers-reduced-motion: reduce) { .share-btn { transition: none; } }
    /* SHARE:END */
"""

PRINT_CSS = """      /* A share button means nothing on paper. */
      section[aria-labelledby="share-heading"] { display: none; }
"""

SECTION = """    <!-- ========================== SHARE ========================== -->
    <!-- SHARE:BEGIN -->
    <!-- Hands out this page's own URL with ?share on it, which hides the
         keepsake downloads. Generated by tools/add_share_button.py. -->
    <section class="section reveal" aria-labelledby="share-heading">
      <div class="label-row"><h2 id="share-heading" class="section-label">Share this song</h2></div>
      <div class="share">
        <p class="share-note share-note-owner">{owner_note}</p>
        <p class="share-note share-note-guest">Pass the song and the story along to anyone who should hear it.</p>
        <button class="share-btn" type="button"
                data-share-url="{url}"
                data-share-title="{share_title}"
                data-share-text="{share_text}">Share this song</button>
        <p class="share-status" role="status" aria-live="polite"></p>
        <p class="share-link">
          <input type="text" readonly aria-label="Link to share" value="{url}" />
        </p>
      </div>
    </section>
    <!-- SHARE:END -->
"""

JS = """
    // SHARE:BEGIN
    // The share button. It hands out this page's own address with ?share on
    // the end, which is what tells the page to leave the keepsake downloads
    // out of what the visitor sees.
    //
    // Three ways down, in order: the phone's own share sheet, the clipboard,
    // and failing both, the link itself, selected and ready to copy by hand.
    (function () {
      var box = document.querySelector('.share');
      if (!box) { return; }

      var btn = box.querySelector('.share-btn');
      if (!btn) { return; }
      // The button only works with scripts, so scripts are what reveal it.
      box.className += ' share-ready';
      var status = box.querySelector('.share-status');
      var manual = box.querySelector('.share-link');
      var field = manual ? manual.querySelector('input') : null;

      var url = btn.getAttribute('data-share-url') || window.location.href;
      var title = btn.getAttribute('data-share-title') || document.title;
      var text = btn.getAttribute('data-share-text') || '';

      function say(message) {
        if (status) { status.textContent = message; }
      }

      // Last resort: show the link and select it so a copy is one keystroke.
      function showLink() {
        say('Copy this link and send it however you like.');
        if (!manual) { return; }
        manual.className += ' is-shown';
        if (field) {
          field.value = url;
          try { field.focus(); field.select(); } catch (e) {}
        }
      }

      function copyLink() {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(function () {
              say('Link copied \\u2014 paste it anywhere.');
            }, showLink);
            return;
          }
        } catch (e) {}
        showLink();
      }

      btn.addEventListener('click', function () {
        say('');
        try {
          if (navigator.share) {
            navigator.share({ title: title, text: text, url: url }).then(function () {
              say('Thank you for passing it on.');
            }, function (err) {
              // Closing the share sheet is a choice, not a failure.
              if (err && err.name === 'AbortError') { return; }
              copyLink();
            });
            return;
          }
        } catch (e) {}
        copyLink();
      });
    })();
    // SHARE:END
"""

NOTE_WITH_DOWNLOADS = ("Send the song and the story to anyone you like. The link you share "
                       "opens this page without your keepsake downloads on it.")
NOTE_PLAIN = "Send the song and the story to anyone you like."

# ------------------------------------------------------------------- helpers


class BuildError(Exception):
    pass


def marked_body(fragment, begin, end):
    """The begin-marker-to-end-marker span of a fragment, markers included."""
    start = fragment.index(begin)
    return fragment[start:fragment.index(end, start) + len(end)]


def replace_marked(text, begin, end, replacement):
    """Swap whatever sits between two markers. Returns (text, found)."""
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        return text, False
    return pattern.sub(lambda _: replacement, text, count=1), True


def insert_before(text, anchor, addition, label):
    found = text.count(anchor)
    if found != 1:
        raise BuildError("expected one %s anchor, found %d" % (label, found))
    return text.replace(anchor, addition + anchor, 1)


def song_title(text):
    match = re.search(r"<h1>(.*?)</h1>", text, re.DOTALL)
    if not match:
        raise BuildError("no <h1> song title")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def ensure_link_preview(text, slug):
    """A shared link is only as good as its preview card.

    Every page carries og:title and og:description, but one was built before
    the art was embedded and is missing og:url / og:image -- the difference
    between a link that unfurls with the album cover and a bare grey box.
    """
    page_url = "%s/%s/" % (BASE_URL, slug)
    additions = []
    if 'property="og:url"' not in text:
        additions.append('  <meta property="og:url" content="%s" />' % page_url)
    if ('property="og:image"' not in text
            and os.path.isfile(os.path.join(ROOT, slug, "cover.jpg"))):
        additions.append('  <meta property="og:image" content="%scover.jpg" />' % page_url)
    if not additions:
        return text

    anchor = '  <meta name="twitter:card"'
    if anchor not in text:
        raise BuildError("could not find the link-preview block")
    return text.replace(anchor, "\n".join(additions) + "\n" + anchor, 1)


def share_section(url, owner_note, title):
    return SECTION.format(
        url=html.escape(url, quote=True),
        owner_note=html.escape(owner_note),
        share_title=html.escape("%s · Heartstrings Studio" % title, quote=True),
        share_text=html.escape(
            "“%s” — a song written by hand at Heartstrings Studio." % title,
            quote=True),
    )


def add_share_ui(text, url, owner_note, title):
    """Put the share styles, markup and script into a page, or refresh them."""
    text, found = replace_marked(text, "<!-- SHARE:HEAD:BEGIN -->", "<!-- SHARE:HEAD:END -->",
                                 HEAD.strip())
    if not found:
        anchor = '  <script>document.documentElement.className += " js";</script>\n'
        if anchor not in text:
            raise BuildError("could not find the js-flag script")
        text = text.replace(anchor, anchor + "\n" + HEAD, 1)

    text, found = replace_marked(text, "/* SHARE:BEGIN */", "/* SHARE:END */",
                                 marked_body(CSS, "/* SHARE:BEGIN */", "/* SHARE:END */"))
    if not found:
        text = insert_before(text, "    /* ---------- Footer CTA ---------- */",
                             CSS.lstrip("\n") + "\n", "footer CSS")

    if 'section[aria-labelledby="share-heading"]' not in text:
        anchor = '      section[aria-labelledby="downloads-heading"] { display: none; }\n'
        if anchor not in text:
            raise BuildError("could not find the print rules")
        text = text.replace(anchor, anchor + PRINT_CSS, 1)

    section = share_section(url, owner_note, title)
    text, found = replace_marked(text, "<!-- SHARE:BEGIN -->", "<!-- SHARE:END -->",
                                 marked_body(section, "<!-- SHARE:BEGIN -->",
                                             "<!-- SHARE:END -->"))
    if not found:
        text = insert_before(text, "\n  </main>", "\n" + section, "</main>")

    text, found = replace_marked(text, "// SHARE:BEGIN", "// SHARE:END",
                                 marked_body(JS, "// SHARE:BEGIN", "// SHARE:END"))
    if not found:
        text = insert_before(text, "  </script>\n</body>", JS.rstrip("\n") + "\n",
                             "</script>")
    return text


def build(slug, check_only):
    index_path = os.path.join(ROOT, slug, "index.html")
    original = open(index_path, encoding="utf-8").read()

    title = song_title(original)
    prepared = ensure_link_preview(original, slug)
    has_downloads = 'aria-labelledby="downloads-heading">' in prepared
    note = NOTE_WITH_DOWNLOADS if has_downloads else NOTE_PLAIN

    updated = add_share_ui(prepared, "%s/%s/?share" % (BASE_URL, slug), note, title)
    stale = updated != original

    if not check_only and stale:
        open(index_path, "w", encoding="utf-8").write(updated)

    print("%-32s %-24s %s" % (
        slug,
        "hides downloads" if has_downloads else "(no downloads to hide)",
        "updated" if stale else "already current"))
    return stale


def main(argv):
    check_only = "--check" in argv
    slugs = [a for a in argv if not a.startswith("-")]
    if not slugs:
        slugs = sorted(d for d in os.listdir(ROOT)
                       if os.path.isfile(os.path.join(ROOT, d, "index.html")))

    stale = []
    for slug in slugs:
        try:
            if build(slug, check_only):
                stale.append(slug)
        except BuildError as err:
            print("%-32s SKIPPED: %s" % (slug, err), file=sys.stderr)
            return 1

    if check_only and stale:
        print("\nOut of date: %s\nRun: python3 tools/add_share_button.py" % ", ".join(stale),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
