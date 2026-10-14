# Vastu Master Studio

A browser-based floor-plan consultation workspace. Upload an image or a PDF page, mark the property boundary and center, set north, and classify rooms, objects and entrances into directional sectors.

## Run

Requires Node.js 20+ and Python 3.

```sh
npm ci --cache /tmp/vastu-npm-cache
npm start
```

Open port 8080 in your browser. Serve the application over HTTP; opening the HTML directly from disk will prevent the PDF module from loading. No account, database or external API credentials are required. Uploaded files are processed in the browser.

## Workflow

1. Name the project and upload a floor plan (PNG, JPG, WebP or PDF, up to 20 MB). Select a page for multipage PDFs.
2. Mark boundary corners in perimeter order and finish. Use **Boundary Center** for a polygon centroid, or mark four center corners in perimeter order.
3. Enter the north bearing clockwise from map up. Side buttons align north toward a marked center side.
4. Mark room corners and finish; place objects with one click; mark entrances with two clicks.
5. Review Chart and Analyse Map. Changing north recalculates feature classifications.
6. Select report sections in Download, enter client notes in Premium Report, and use Print / Save as PDF. The report includes the selected floor, not all floors.
7. Save a JSON project to retain images, floors, notes and report preferences. Open Project restores it. Browser storage provides best-effort recovery; large images can exceed its quota, so save a file for reliable backup.

Mouse wheel zooms; Pan / View allows dragging. Enter finishes marking, Escape exits the mode, and Ctrl/Cmd+Z undoes marks in the active mode.

## Validation

```sh
npm test
```

Browser tests cover directional recalculation, report selection, project restoration, invalid imports, invalid geometry, and PDF conversion. The bundled test configuration uses `/usr/bin/chromium`; adjust the executable path for another machine.

## Scope

Areas use approximate image pixels squared by default. Optional pixels-per-meter or pixels-per-foot calibration converts them to m² or ft²; verify the drawing scale before using physical areas. Devta names are a reference list rather than an authoritative placement overlay. Marathi report headings are supported; room names and reference labels remain in English. Reports provide directional geometry and practitioner notes rather than automated remedies. This application does not provide consultation booking, payments or a backend.

PDF rendering uses locally installed PDF.js. Keep `node_modules/pdfjs-dist` available when hosting the app. No deployment has been performed.

## Workspace additions

Use **Explore sample** for a fully editable illustrative home. The four-step guide tracks the current floor. Floors can be renamed, duplicated independently, or deleted (one must remain). Drawing review summarizes directional shares and flags room/object/entrance centers outside the boundary; it does not check the entire shape for containment. The optional drawing scale is saved with each floor and included in charts and reports. New Project starts a blank workspace after confirmation.
