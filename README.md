# Library Reports

A web application for running SQL reports against a PostgreSQL database and downloading the results as CSV files. Built with [NiceGUI](https://nicegui.io/).

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A PostgreSQL database

## Setup

1. **Install dependencies:**

   ```sh
   uv sync
   ```

2. **Configure environment variables:**

   Copy the example file and fill in your values:

   ```sh
   copy .env.example .env
   ```

   Edit `.env`:

   | Variable | Description |
   |---|---|
   | `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:password@host:5432/dbname` |
   | `APP_USERNAME` | Login username for the web interface |
   | `APP_PASSWORD` | Login password for the web interface |
   | `STORAGE_SECRET` | A long random string used to sign session cookies. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |

3. **Run the app:**

   ```sh
   uv run python main.py
   ```

   The app will be available at http://localhost:8080.

## Project Structure

```
main.py              # Application entry point and UI
queries/             # SQL files (one per report)
  products.sql
  orders.sql
  ...
static/              # Static assets (logo, favicon)
.env                 # Environment variables (not committed)
.env.example         # Template for .env
```

## Adapting for Your Database

### Replacing the SQL queries

Each report is a plain `.sql` file in the `queries/` directory. Replace these files with your own queries. The filename (without `.sql`) is used as the query name in `main.py`.

For example, to add an "Inventory" report:

1. Create `queries/inventory.sql`:

   ```sql
   SELECT item_name, quantity, location
   FROM inventory
   ORDER BY location, item_name
   ```

2. Add a button in `main_page()` in `main.py`:

   ```python
   button_row(
       'Inventory',
       'Export current inventory by location.',
       on_click=functools.partial(run_report, 'inventory', 'inventory.csv', 'Inventory')
   )
   ```

### Adding a report that takes user input

If a report needs a parameter from the user (e.g. filtering by date or category), use a named parameter in the SQL and `prompt_button_row` in the UI.

1. Create `queries/inventory_by_location.sql` using `%(param_name)s` syntax for parameters:

   ```sql
   SELECT item_name, quantity
   FROM inventory
   WHERE location ILIKE %(location)s
   ORDER BY item_name
   ```

2. Add a prompted button in `main_page()`:

   ```python
   prompt_button_row(
       'Inventory by Location',
       'Export inventory filtered by location name.',
       'Location',
       on_submit=lambda val: run_report(
           'inventory_by_location', 'inventory_by_location.csv',
           'Inventory by Location', params={'location': val}
       )
   )
   ```

   This opens a modal dialog asking the user for a value before running the query.

### Removing the example reports

Delete any `.sql` files from `queries/` that you don't need, and remove the corresponding `button_row` or `prompt_button_row` calls from `main_page()` in `main.py`.

## How It Works

- **`load_query(name)`** reads `queries/{name}.sql` and returns the SQL string.
- **`run_query(query, params)`** connects to PostgreSQL, executes the query, and returns the results as CSV bytes.
- **`run_report(query_name, filename, label, params)`** shows an indeterminate progress bar, runs the query in a background thread (so the UI stays responsive), then triggers a CSV file download in the user's browser.
- **`button_row(label, help_text, on_click)`** renders a styled button with hover help text.
- **`prompt_button_row(label, help_text, prompt_label, on_submit)`** renders a button that opens a modal to collect user input before running a report.
- **Authentication** is handled via middleware that redirects unauthenticated users to `/login`. Credentials are checked against `APP_USERNAME` and `APP_PASSWORD` from `.env`.