# Haven & Home - Home Decor Studio

A home decor catalog and AI room visualization app built with Python and Flet.

## What you can do

- Browse furniture and home decor from the store catalog.
- Manage decor items and stock in **Decor Catalog**.
- Select a piece, upload an empty-room photo, describe your preferred style or placement, and create an AI room preview.
- Use the included sample furniture catalog or add your own home decor products.

## Run the app

On Windows, run `run.bat` for the desktop app or `run_web.bat` for the browser version.

Or activate the virtual environment and run:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
# Browser version
python main.py --web
```

## Enable AI room previews

Set an OpenAI API key in `.env`:

```env
OPENAI_API_KEY=your_api_key
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

The room photo and design prompt are sent to the OpenAI image edit API. Image generation may incur API charges.

## Project structure

- `main.py` - Home decor app shell and navigation
- `database.py` - Local catalog and app data
- `views/inventory_view.py` - Decor catalog management
- `views/room_designer_view.py` - Furniture selection, room photo upload, and design chat
- `room_designer_service.py` - OpenAI image editing integration
