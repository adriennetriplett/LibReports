import csv
import functools
import io
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import ui, app, run

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")

UNRESTRICTED_PATHS = {'/login'}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated'):
            if request.url.path not in UNRESTRICTED_PATHS and not request.url.path.startswith(('/_nicegui', '/static')):
                return RedirectResponse('/login')
        return await call_next(request)

app.add_middleware(AuthMiddleware)

BASE_DIR = Path(__file__).parent
QUERIES_DIR = BASE_DIR / 'queries'
app.add_static_files('/static', BASE_DIR / 'static')


def load_query(name: str) -> str:
    return (QUERIES_DIR / f'{name}.sql').read_text()


def run_query(query: str, params=None):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    writer.writerows(rows)
    return buf.getvalue().encode()

def button_row(label: str, help_text: str, on_click=None):
    """create a button with hover-text to the right."""
    with ui.element('div').classes('button-row'):
        ui.button(label, on_click=on_click, color=None).style(
            'background-color: #0C5449; color: white; font-weight:500; border-radius:5px; border:3px solid #FFCC33;'
        )
        ui.label(help_text).classes('info-text')

def prompt_button_row(label: str, help_text: str, prompt_label: str, on_submit=None):
    """create a button that opens a modal dialog to collect input"""
    def open_dialog():
        with ui.dialog() as dialog, ui.card().style('min-width:350px;'):
            ui.label(prompt_label).style('font-size:18px; font-weight:500; margin-bottom:8px;')
            text_input = ui.input(placeholder=prompt_label).style('width:100%;')

            async def submit():
                dialog.close()
                await on_submit(text_input.value)

            with ui.row().classes('justify-end').style('margin-top:12px; width:100%;'):
                ui.button('Cancel', on_click=dialog.close, color=None).style(
                    'background-color:#0C5449; color:white; border-radius:5px;'
                )
                ui.button('Run Report', color=None, on_click=submit).style(
                    'background-color:#0C5449; color:white; border-radius:5px;'
                )
        dialog.open()

    button_row(label, help_text, on_click=open_dialog)

def multi_prompt_button_row(label: str, help_text: str, on_submit=None):
    """create a button that opens a modal dialog to collect multiple inputs"""
    def open_dialog():
        with ui.dialog() as dialog, ui.card().style('min-width:400px;'):
            ui.label('Enter Report Parameters').style(
                'font-size:18px; font-weight:500; margin-bottom:8px;'
            )

            start_date = ui.input('Start Date (YYYY-MM-DD)').style('width:100%;')
            end_date = ui.input('End Date (YYYY-MM-DD)').style('width:100%;')
            locations = ui.input(
                'Location Codes (comma-separated)'
            ).style('width:100%;')

            async def submit():
                dialog.close()

                # Convert comma-separated string to Python list
                location_list = [
                    loc.strip() for loc in locations.value.split(',')
                    if loc.strip()
                ]

                await on_submit(
                    start_date.value,
                    end_date.value,
                    location_list
                )

            with ui.row().classes('justify-end').style('margin-top:12px; width:100%;'):
                ui.button('Cancel', on_click=dialog.close, color=None).style(
                    'background-color:#0C5449; color:white; border-radius:5px;'
                )
                ui.button('Run Report', on_click=submit, color=None).style(
                    'background-color:#0C5449; color:white; border-radius:5px;'
                )

        dialog.open()

    button_row(label, help_text, on_click=open_dialog)


async def run_report(query_name: str, filename: str, button_label: str, params=None):
    with ui.dialog() as progress_dialog, ui.card().style('min-width:300px;'):
        ui.label(f'Running {button_label}...').style('font-weight:500; margin-bottom:8px;')
        ui.linear_progress(value=None).props("indeterminate color='secondary'").style('width:100%;')
    progress_dialog.props('persistent')
    progress_dialog.open()
    try:
        data = await run.io_bound(run_query, load_query(query_name), params)
        ui.download(data, filename)
        ui.notify(f'{button_label} finished!')
    except Exception as e:
        ui.notify(f'{button_label} failed: {e}')
    finally:
        progress_dialog.close()

@ui.page('/login')
def login_page():
    def try_login():
        if username.value == APP_USERNAME and password.value == APP_PASSWORD:
            app.storage.user['authenticated'] = True
            ui.navigate.to('/')
        else:
            ui.notify('Invalid username or password', type='negative')

    with ui.card().classes('absolute-center').style('min-width:350px;'):
        ui.image('/static/ULS_horz_color.png').style('width:100%; margin:0 auto 16px auto; display:block;')
        ui.label('Library Reports Login').style('font-size:20px; font-weight:500; text-align:center; color:#0C5449; width:100%;')
        username = ui.input('Username').style('width:100%;')
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login).style('width:100%;')
        ui.button('Log in', on_click=try_login, color=None).style(
            'width:100%; background-color:#0C5449; color:white; font-weight:500; border-radius:5px; margin-top:12px;'
        )

@ui.page('/')
def main_page():
    ui.add_css("""
    .button-row { display:flex; align-items:center; margin-bottom:12px; }
    .button-row .info-text {
        margin-left: 20px;
        opacity:0;
        transition: opacity 0.15s ease-in-out;
        background:#f2f2f2;
        padding:8px 12px;
        border-radius:6px;
        min-width:320px;
    }
    .button-row:hover .info-text { opacity:1; }
    """, shared=True)

    with ui.element('div').style('''
        background:#0C5449;
        width:100vw;
        margin-left:calc(50% - 50vw);
        margin-top:calc(50% - 50vw);
    '''):
        with ui.row().classes('items-center').style('padding:10px 20px;'):
            ui.image('/static/wsuls.png').style('width:300px')

    ui.label('Library Reports').style('font-size:32px; color:#0C5449; margin-bottom:20px')

    prompt_button_row(
        'Sort by LOC Call Number',
        'Sort a Sierra list of item records by Library of Congress call number.',
        'Review File #',
        on_submit=lambda val: run_report('loc', 'sortLOC.csv', 'Sort by LOC', params=(val,))
    )

    prompt_button_row(
        'Sort By Accession Call Number',
        'Sort a Sierra list of item records by accession call number.',
        'Review File #',
        on_submit=lambda val: run_report('accession', 'sortAccession.csv', 'Sort by Accession', params=(val,))
    )

    button_row(
        'Paid Order Record Report',
        'Generate a report of paid order records for the fiscal year to date.',
        on_click=functools.partial(run_report, 'paid', 'paid_ord_recs.csv', 'Paid Order Records Report')
    )

    prompt_button_row(
        'Linked Records',
        'View relationships between bib, item, order, and checkin records.',
        'Review File # (bib)',
        on_submit=lambda val: run_report('linked', 'LinkedRecs.csv', 'Linked Records', params=(val,))
    )

    multi_prompt_button_row(
        'Checkout Statistics',
        'View checkout metrics for items in one or more locations.',
        on_submit=lambda start, end, locs: run_report(
            'checkouts',
            'checkouts.csv',
            'Checkout Statistics',
            params=(start, end, locs)
        )
    )

    button_row(
        'Course Reserves',
        'Generate report of all items currently on course reserve.',
        on_click=functools.partial(run_report, 'reserves', 'reserves.csv', 'Course Reserves')
    )

    def logout():
        app.storage.user.clear()
        ui.navigate.to('/login')

    with ui.footer().style('background:#0C5449; padding:12px 20px;'):
        with ui.row().classes('w-full justify-center'):
            ui.button('Log out', on_click=logout, color=None).style(
                'background:none; color:white; text-decoration:underline; font-weight:400;'
            )

ui.run(
    title='Library Reports',
    favicon='static/wsulogo2017_favicon.ico',
    storage_secret=os.getenv('STORAGE_SECRET', 'library-reports-dev-secret'),
)
