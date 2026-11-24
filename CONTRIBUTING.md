# Contributing feeds

Edit the Markdown file for the feed’s primary subject under [`feeds/`](feeds/). Link to related category pages when a feed is relevant to more than one subject. A publisher can have several entries if each endpoint covers a distinct stream.

## Verify a feed

1. Find the public feed on the publisher’s site or in its feed directory. A service used by the publisher to host its own feed is fine.
2. Fetch the URL, follow redirects, and confirm it returns RSS, Atom, or RSS 1.0 (RDF) XML with at least one item. Prefer a working HTTPS URL. Check what the feed actually covers and the language of its entries.
3. Record the verification date and any unresolved URLs in the pull request. If an existing feed fails, retry it later before removing it. Update moved feeds in place when a replacement is confirmed.

Use directories to find candidates, then verify the publisher endpoints directly. The initial catalog drew on [Weekly Frontier’s source list](https://github.com/cyborgoat/weekly-frontier/blob/main/config/sources.yaml), [Inoreader](https://www.inoreader.com/rss-feeds), [Korbyt](https://product.korbyt.com/help/articles/7374531-popular-rss-feeds), the [Meta RSS directory](https://about.fb.com/wp-content/uploads/2016/05/rss-urls-1.pdf), and [The RSS Endpoint List](https://gist.github.com/thefranke/63853a6f8c499dc97bc17838f6cedcc2).

## Edit a category

Start each category page with a `#` heading, a short description, and links to its raw OPML file and the root category index. In each feed table, keep this column order and sort entries by name, ignoring case.

```markdown
| Name | Website | Feed | Format | Language | Description |
| --- | --- | --- | --- | --- | --- |
| Le Monde – À la une | [Website](https://www.lemonde.fr/) | [Feed](https://www.lemonde.fr/rss/une.xml) | RSS | fr | Headlines from the French edition of Le Monde. |
```

Use plain text for the name and description. Use inline Markdown links for the website and feed URL. Begin and end each row with a pipe, escape literal pipes in cells as `\|`, and leave a blank line after the table before adding more text. Use `RSS`, `Atom`, or `RDF` for the format and a [BCP 47 language tag](https://www.rfc-editor.org/info/bcp47) for the language, such as `en`, `zh-Hans`, or `mul` for a multilingual feed. Keep the feed name in its original language.

For a new category, choose a lowercase, hyphenated directory name and a unique display title. Add it to the root README with its raw OPML link. The `all` name is reserved for the full export. If you remove or rename a category, remove its old OPML file and update the affected links.

## Regenerate OPML

Run these commands from the repository root with Python 3.9 or later.

```sh
python3 scripts/build_opml.py
python3 scripts/build_opml.py --check
```

Include the Markdown and generated OPML changes in the same pull request. GitHub Actions runs the same check without contacting publishers.
