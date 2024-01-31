AUTHOR = "Yaser Amiri"
SITENAME = "Yaser Amiri - Personal Blog"
SITEURL = ""
SITETITLE = "Yaser Amiri"
SITESUBTITLE = "Software Engineer"
SITEDESCRIPTION = "Yaser Amiri's Thoughts and Writings"
SITELOGO = SITEURL + "/images/profile.png"
FAVICON = SITELOGO

PATH = "content"

TIMEZONE = "Asia/Tehran"

DEFAULT_LANG = "en"

# Feed generation is usually not desired when developing
FEED_ATOM = 'atom.xml'
FEED_RSS = 'rss.xml'
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = tuple()

# Social widget
SOCIAL = (
    ("github", "https://github.com/Yaser-Amiri"),
    ("linkedin", "https://www.linkedin.com/in/yaser-amiri"),
    ("rss", "./atom.xml"),
)

DEFAULT_PAGINATION = 10

THEME = "Flex"

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

MAIN_MENU = True
CC_LICENSE = {
    "name": "Creative Commons Attribution-ShareAlike",
    "version": "4.0",
    "slug": "by-sa",
}
COPYRIGHT_YEAR = 2021
BROWSER_COLOR = "#333"
CUSTOM_CSS = "styles/custom.css"
MAIN_MENU = False
STATIC_PATHS = ['images', 'styles', 'docs']
