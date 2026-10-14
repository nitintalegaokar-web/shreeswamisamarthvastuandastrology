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

Areas use approximate image pixels squared by default. Optional pixels-per-meter or pixels-per-foot calibration converts them to m² or ft²; verify the drawing scale before using physical areas. The 45-Devta view is an explicitly labeled concentric schematic (1 center + 4 inner + 8 middle + 32 outer), not an authoritative traditional placement overlay. Marathi report headings are supported; room names and reference labels remain in English. Reports provide directional geometry and practitioner notes rather than automated remedies. This application does not provide consultation booking, payments or a backend.

PDF rendering uses locally installed PDF.js. Keep `node_modules/pdfjs-dist` available when hosting the app. No deployment has been performed.

## Workspace additions

Use **Explore sample** for a fully editable illustrative home. Use the workspace tabs and shared action toolbar to work with the current floor. Floors can be renamed, duplicated independently, or deleted (one must remain). Drawing review summarizes directional shares and flags room/object/entrance centers outside the boundary; it does not check the entire shape for containment. The optional drawing scale is saved with each floor and included in charts and reports. New Project starts a blank workspace after confirmation.

## Image upload troubleshooting

Extract the complete ZIP before opening the application. Keep `index.html`, `studio.js`, `workspace.js`, and `workspace.css` together. Image uploads do not require PDF.js or a network connection, and remain usable when browser recovery storage is blocked. Accepted image contents are PNG, JPEG, and WebP, up to 20 MB and 40 megapixels. HEIC must first be exported as JPG. On small screens, a successful upload scrolls the plan into view. PDF editing requires the HTTP setup above. Direct file-URL operation could not be browser-tested in this cloud environment because its browser policy blocks file URLs.

## Visual analysis and drawing tools

- **Chart:** a 16-zone area bar chart with mean and adjustable upper/lower reference lines. The defaults are 1.5× and 0.65× the mean; these are comparison thresholds, not suitability or outcome scores. Thresholds are saved in the project. Polygon geometry supplies total area; sampling estimates its directional shares.
- **32 Entry:** a floor-plan overlay with 32 selectable, labeled sectors. Each spans 11.25°. Drag to pan, scroll or use +/− to zoom, and Fit to reset. The cardinal axis starts sector 5.
- **45 Devtas:** selectable numbered reference regions and a name legend. The geometry is a schematic concentric layout and must be verified against the practitioner's chosen tradition.
- **Analyse Map:** mark rooms, objects, and entrances directly in the map beside the analysis controls. Rooms use multiple corners; objects one point; entrances two endpoints.
- **Compass:** rotate the dial, use the slider, or enter a bearing. The map and classifications update together. Directional themes and editable element/deity/association/review cards support practitioner discussion. These cultural associations do not establish medical or financial outcomes; school-specific references should be reviewed.
- **Device compass:** requires a secure browser context, compatible sensors, and browser permission. The app accepts absolute headings and rejects relative-only orientation events. Physical sensor behavior has not been tested on a phone. If no absolute reading arrives, use the manual control.
- **Build Plan:** create a separate drawing floor if the current floor already has an uploaded map. Generate a rectangle from dimensions in feet or meters, or click boundary corners manually. Click the first corner or Finish Boundary to close it. Drag boundary handles to adjust; click near an edge to insert a corner.
- **Walls and doors:** walls use two snapped endpoints with a live length preview. Door endpoints must be near the same wall or boundary edge; openings snap to it and are classified as entrances. Double-click a wall/door to select it, or remove a feature from its list.
- **Rooms and labels:** Draw Room Zones creates polygons for analysis. Label Rooms adds a text label at a chosen point; Enter saves and Escape cancels.
- **Furniture:** choose from bedroom, living, kitchen, and utility catalogs, then click to place. Drag the footprint to move; select it to resize, rotate 90°, or delete. Catalog dimensions are reference sizes in feet and are converted when the drawing uses meters.
- **Undo/redo:** the shared toolbar handles builder changes; history is local to the session and not included in project files. Editor mark undo remains available. Redo applies to builder operations only.
- **Export:** use the single Export SVG button. It exports the current drawing/map, the distribution chart on Chart, or the reference map on 32 Entry/45 Devtas. Use the Include Legend checkbox for reference exports. SVGs contain embedded map images. Choose report sections in Download, then print from Premium Report for PDF.

Builder geometry, furniture footprints, labels, calibrated units, and reference notes are preserved in Save Project / Open Project. Keep all shipped HTML, CSS, and JavaScript files together.
