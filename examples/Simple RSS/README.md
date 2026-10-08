# Simple RSS

A simple RSS reader application for Windows built with wxPython.

## Features

- **Windows-only application** with platform check at startup
- **Simple interface** with two panels:
  - Left panel: RSS feeds listed alphabetically
  - Right panel: Articles from selected feed (newest first)
- **Menu system** with keyboard shortcuts:
  - `Ctrl+A`: Add new RSS feed
  - `Delete`: Remove selected feed
  - `F5`: Refresh selected feed
  - `Ctrl+1`: View all articles
  - `Ctrl+2`: View unread articles only
  - `Ctrl+R`: Mark selected articles as read
  - `Ctrl+U`: Mark selected articles as unread
  - `Enter`: Open selected article in default browser
- **Article filtering**: Use View menu to show all articles or only unread ones
- **Manual feed refresh**: No automatic updates, user-controlled refresh
- **SQLite database**: Stores feeds and articles locally

## Installation

1. Make sure you have Python 3.13 or higher installed
2. Install uv (Python package manager)
3. Clone or download this project
4. Run `uv sync` to install dependencies
5. Run the application with `uv run python -m simple_rss`

## Build with PyRetort

The `[tool.pyretort]` section of `pyproject.toml` describes a Windows build
with an embedded Python 3.13.9 (amd64) and no console window. From the
PyRetort repository root:

```powershell
uv run pyretort check -p "examples/Simple RSS/pyproject.toml"
uv run pyretort build -p "examples/Simple RSS/pyproject.toml"
```

The first build downloads the embeddable Python package from python.org into
`examples/Simple RSS/downloads/`; later builds reuse it. The build installs the
application with its dependencies (wxPython, httpx, peewee, fastfeedparser)
into that Python and creates `examples/Simple RSS/build/simple-rss-0.1.0-amd64/`:

- `simple-rss.exe`, the launcher that starts the application;
- `simple-rss/`, the embedded Python with the installed packages.

`create_dist_zip_file = true` also packs that folder into
`examples/Simple RSS/dist/simple-rss-0.1.0-amd64.zip`, which unpacks into a
single `simple-rss-0.1.0-amd64/` folder. Copy the folder or share the archive
to run Simple RSS on another Windows PC without an installed Python. To remove
`build/`, `dist/` and `downloads/` from `examples/Simple RSS/`, run
`uv run pyretort cleanup -p "examples/Simple RSS/pyproject.toml"`.

## Default RSS Feeds

The application includes the following default RSS feeds on first startup:

1. **BBC News** (English)
   - https://feeds.bbci.co.uk/news/rss.xml

2. **CNN Top Stories** (English)
   - http://rss.cnn.com/rss/cnn_topstories.rss

3. **Українська Правда** (Ukrainian)
   - https://www.pravda.com.ua/rss/

## Usage

### Adding RSS Feeds

1. Press `Ctrl+A` or use the Feed menu → Add Feed
2. Enter the RSS feed URL
3. The title will be auto-detected (you can change it)
4. Click "Add Feed" to add it to your list

### Managing Feeds

- **Select a feed**: Click on a feed in the left panel to see its articles
- **Auto-selection**: First feed is automatically selected and focused when the application starts
- **Remove a feed**: Select a feed and press `Delete` or use Feed menu → Remove Feed
- **Refresh a feed**: Select a feed and press `F5` or use Feed menu → Refresh

### Reading Articles

- **View articles**: Select a feed to see its articles in the right panel (only titles are shown)
- **Auto-selection**: First article is automatically selected and focused when loading articles
- **Open article**: Double-click an article or press `Enter` to open it in your default browser
- **Mark as read/unread**: Select articles and use `Ctrl+R` (mark read) or `Ctrl+U` (mark unread)
- **Filter articles**: Use View menu to show all articles or only unread ones (`Ctrl+1` for all, `Ctrl+2` for unread)
- **Refresh feeds**: Press `F5` to refresh selected feed (no success dialog shown)

### Database

The application stores its data in:
```
%APPDATA%\SimpleRSS\simple_rss.db
```

This includes:
- RSS feed information (title, URL)
- Article data (title, URL, content, publication date, read status)

## Technology Stack

- **GUI Framework**: wxPython
- **List Widget**: wxPython ListCtrl
- **HTTP Client**: httpx
- **Database**: SQLite with Peewee ORM
- **RSS Parser**: FastFeedParser
- **Package Manager**: uv

## Project Structure

```
src/simple_rss/
├── __init__.py          # Main entry point
├── main.py              # Application class
├── database.py          # Database setup and connection
├── models/
│   ├── base.py          # Base model class
│   ├── feed.py          # Feed model
│   └── article.py       # Article model
├── gui/
│   ├── main_frame.py    # Main application window
│   ├── panels/
│   │   ├── feed_panel.py    # Left panel with feed list
│   │   └── article_panel.py # Right panel with article list
│   ├── dialogs/
│   │   └── add_feed_dialog.py  # Dialog for adding feeds
│   └── menus/
│       └── main_menu.py  # Main menu bar
├── parsers/
│   └── rss_parser.py    # RSS parsing logic
└── utils/
    └── platform.py      # Windows platform check
```

## License

This project is provided as-is for educational and personal use.