# ValScanner React Frontend Experiment

This folder is an optional proof-of-concept renderer for the existing PySide app. It is not used unless `VALSCANNER_FRONTEND_RENDERER=web` is set.

## Test locally

1. Install dependencies:
   `npm install`
2. Build the static React app:
   `npm run build`
3. Launch ValScanner with the web renderer:
   `VALSCANNER_FRONTEND_RENDERER=web`
4. Return to the current UI:
   `VALSCANNER_FRONTEND_RENDERER=qt`

Normal Python startup does not run npm and does not require Node. If Qt WebEngine or `frontend_web/dist/index.html` is missing, ValScanner falls back to the existing Qt UI.
