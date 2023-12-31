from flask import render_template, redirect, url_for, request
from markdown import markdown
from loguru import logger
from pictrs_safety_api.flask import APP
import pictrs_safety_api.exceptions as e

@logger.catch(reraise=True)
@APP.route('/')
# @cache.cached(timeout=300)
def index():
    with open(f'fedi_safety_api/templates/index.md') as index_file:
        index = index_file.read()
    findex = index.format()

    style = """<style>
        body {
            max-width: 120ex;
            margin: 0 auto;
            color: #333333;
            line-height: 1.4;
            font-family: sans-serif;
            padding: 1em;
        }
        </style>
    """

    head = f"""<head>
    <title>Pict-rs Safety</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {style}
    </head>
    """
    return(head + markdown(findex))
