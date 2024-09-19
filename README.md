# OpenTube
Open-source alternative youtube client.

_______________________

# Installing
Everything is simple here, install the necessary libraries and run the client:
```python
pip install playwright requests pillow rich beautifulsoup4
```
Also don't forget about additional files for `playwright`:
```python
playwright install
```
________________________

# Additionally

## How it works

The interface is implemented through the `rich` library; in fact, the client is completely console-based.
Video search is implemented through regular `invidious` parsing using `beautifulsoup4`.
Video downloading is implemented by launching a site for downloading videos in `headless` mode (invisible browser).

## Video cleaning
`OpenTube` does not automatically delete downloaded videos, some may be too lazy to delete videos manually, so I left a file to clear all videos in the current directory
