# Vastu Master Studio

A browser-based floor-plan consultation workspace. Upload an image or a PDF page, mark the property boundary and center, set north, and classify rooms, objects and entrances into directional sectors.

## Run

For the downloaded app, extract the complete ZIP and open `index.html`, keeping the `vendor` folder and all scripts/styles together. PDF.js, its worker, fonts and CMaps are bundled; normal use does not require npm installation or a CDN. If your browser blocks local files, serve the extracted folder with `python3 -m http.server 8080`.

For development, use Node.js 20+ and Python 3.

```sh
npm ci --cache /tmp/vastu-npm-cache
npm start
```

Open port 8080 in your browser. The shipped PDF runtime uses classic scripts and embedded font/CMap assets rather than ES module imports or node_modules paths. No account, database or external API credentials are required. Uploaded files are processed in the browser.

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

PDF rendering uses the bundled files under `vendor/`. Developers can regenerate them with `npm run build:pdf` after installing the locked dependencies. Preserve the accompanying PDF.js, CMap and font license files. No website deployment has been performed.

## Workspace additions

Use **Explore sample** for a fully editable illustrative home. Use the workspace tabs and shared action toolbar to work with the current floor. Floors can be renamed, duplicated independently, or deleted (one must remain). Drawing review summarizes directional shares and flags room/object/entrance centers outside the boundary; it does not check the entire shape for containment. The optional drawing scale is saved with each floor and included in charts and reports. New Project starts a blank workspace after confirmation.

## Image upload troubleshooting

Extract the complete ZIP before opening the application. Keep `index.html`, `studio.js`, `workspace.js`, and `workspace.css` together. Image uploads do not require PDF.js or a network connection, and remain usable when browser recovery storage is blocked. Accepted image contents are PNG, JPEG, and WebP, up to 20 MB and 40 megapixels. HEIC must first be exported as JPG. On small screens, a successful upload scrolls the plan into view. PDF editing uses the supplied vendor bundles; extract the complete ZIP rather than copying only index.html. Direct file-URL operation could not be browser-tested in this cloud environment because its browser policy blocks file URLs.

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

## Guided setup and area summary

The left panel provides Floors/Add, the five setup steps, one Change Image control, 4 Points / Rectangle / Auto center methods, A–D coordinates, separate center/boundary undo and reset, compass placement on AB/BC/CD/DA, bearing entry/slider, and Apply & Calculate Zones. Rectangle supports dragging opposite corners or two separate clicks. Auto uses the property-boundary centroid when available, otherwise the full image bounds; check image margins before using that selection. Side selection positions the compass on that edge; the degree remains north clockwise from image up.

The left setup panel and right option panels scroll independently. On smaller screens they use bounded-height scrolling sections. The chart uses a completed property boundary, or the four-point selection while no boundary is marked; it states which geometry is measured. With neither, the chart shows an actionable empty state rather than invented bars.

Zone Summary and the report's area summary show total and average zone area in square feet. Enter the surveyed total in **Known property area (sq ft)**, or configure a drawing scale. A meter-based scale is converted to square feet for the summary. An unscaled image cannot establish physical area; the summary displays a dash until calibrated. Entering a known total also calibrates chart shares to square feet.

## Boundary and wall drawing modes

**Single-line trace** adds one straight boundary segment per click and stays open; it never adds a closing edge automatically. Click the first point or Finish Boundary to close and enable area calculation. **Original polygon** retains the closed-shape preview; Quick Rectangle also remains available. Both manual modes require confirmation of the final boundary before area calculation. Internal walls snap to horizontal or vertical axes, with the same constraint applied to the live preview and final wall.

## Source-based Vastu interpretations

The current directional reference cards are editable practitioner references, not a verified extraction of the uploaded MahaVastu book. Book-specific automatic remedies have not been added: the supplied PDF exceeded the chat environment's 32 MiB file-reading limit. A compressed copy or smaller chapter files are needed to build rules with verifiable page references.

## Visual design library

In Build Plan, open **Open design library** once. Construction, Finishes, Furniture, Lighting and Fixtures are thumbnail category galleries. Choose a category and then an item. Construction includes doors, windows, columns/beams, ceilings, feature walls, stairs, railings, platforms, fireplaces, dividers, parametric ceilings and moldings. The thumbnails are original illustrations, not imported product photos or downloadable manufacturer models. Furniture and fixtures are editable reference footprints.

Doors and windows use two endpoints on the same drawn wall. Doors are included in entrance classification; windows are stored separately. Finishes apply a 2D material overlay to the room zone under the click, or to the floor if no room zone contains the point. The library includes tiles, flooring, carpet, paint, wallpaper, wood and coating styles. Save Project retains window geometry, catalog categories, and room/floor finishes.

## 3D plan viewer

Open **3D View** after creating a measured drawing or marking a boundary and configuring a scale/known area. The model extrudes the outer boundary and internal walls, creates marked door/window openings, and displays procedural furniture approximations from the placed footprints. Uploaded plan images are not automatically reconstructed: their boundaries, partitions, scale and features must be supplied. If no internal builder walls exist, marked room boundaries provide schematic partitions.

- **Orbit:** drag to rotate, wheel/pinch to zoom, and right-drag to pan.
- **Top:** view from above. **Reset view:** restore the initial perspective.
- **Walk:** WASD or arrow keys move; drag to look. This is a viewing mode without collision detection.
- Adjust wall height in the drawing unit, enable cutaway walls, or toggle furniture/fixtures. Wall height is stored with the project.
- **Save 3D snapshot:** PNG with WebGL, or SVG in the fallback renderer.

Three.js and its renderer controls are bundled locally. If WebGL is unavailable, a vector renderer still displays the 3D geometry. Model geometry, material patterns and furniture are schematic; the viewer does not provide photorealistic imported models, structural design, or automatic architectural reconstruction.

## Rebuild bundled assets

After `npm ci`, run `npm run build` to regenerate PDF.js bundles/font assets, the original catalog thumbnails and the local 3D runtime. The normal downloaded application uses the committed bundles and does not need npm or network requests. The browser file-URL restriction noted above prevented direct file-URL testing in this cloud environment; runtime behavior is tested through HTTP with local bundles.

## Construction tools and measured 2D drawings

Build Plan includes an independently scrolling construction palette. **Wall (B)** snaps each segment horizontally or vertically. **Room (F)** creates a rectangle with internal walls; the original room-zone polygon and both boundary tracing styles remain available. Doors include single, double, unequal, sliding, frame and open passage symbols. Window footprints include regular, French, bay, flip, L-shaped and U-shaped variants. Window/door styles are schematic plan symbols; they do not model manufacturer hardware. Beams, columns and flues are editable reference objects.

**Hole** marks a nonoverlapping opening inside the property boundary. Finish its polygon explicitly. Openings subtract from zone area and appear as holes in the 3D slab. **Import CAD** accepts ASCII DXF LINE and straight POLYLINE/LWPOLYLINE entities, with supported drawing units. The largest closed polyline becomes the candidate boundary; verify it. Unsupported entities are counted and skipped. DWG, curved polylines, blocks and automatic CAD room recognition are not supported. Import Image uses the existing image/PDF workflow.

**Floor Drawings** provides Modern minimal, Architectural palette, Standard living and Draft presentations; shadows, dimensions, text, pictures and two-point annotations; pan/zoom; SVG and HD PNG export. Calibrated wall lengths appear in feet/inches and marked room polygon areas in square feet. Accuracy depends on calibration and the marked coordinates, not screenshot resolution. Dimensions are rounded to the nearest inch for display; the saved coordinates retain their precision. The right properties panel manages levels, wall height, slab thickness and room areas. Areas represent marked polygons; overlapping room polygons are not automatically reconciled or partitioned.

**Drawings Layout** provides A3/A4 landscape/portrait sheets, title blocks, client/address/designer/notes, drawing scales, inserted views/text/pictures, sheet duplication, item positioning and undo/redo. Insert plain, furnished, styled, zone or chart views. Fit mode is explicitly not to scale. Measured scales require calibration. Export SVG or use Print / Save PDF, with browser margins/scale settings checked against the intended paper size.

## Workspace commands and materials

The shared toolbar reuses Save, Undo, Redo, Clear and export actions once. File opens saved project JSON. Toolkit links the floor-plan and compass tools. Furniture Plan opens the categorized local design library. Images / Videos imports images/PDFs, exports 2D drawings, and offers 3D snapshots and short video recordings. Video recording requires WebGL, canvas capture and MediaRecorder; it records up to 60 seconds and downloads the browser-supported WebM/MP4 format. Gallery stores up to six snapshots in browser storage; use Save Project for portable backups. Drawings & Schedules includes a CSV object schedule with calibrated footprint dimensions.

The 3D material panel searches the available finishes. Select a swatch, then click a floor, room, wall or furniture surface to apply it; shared Undo/Redo reverses material changes. Finishes are procedural color/pattern representations. The navigator shows the current floor geometry and camera target; click it to reposition the camera. Preview opens the current rendered image. AI generation, cloud/public asset libraries, social sharing and account subscriptions shown in the supplied commercial-product screenshots are not connected services in this local application.

## Consultant presentation update

The **Download** page now exports the checked sections directly through **Download report**. Choose PDF for an A4 document or HTML for a self-contained web report. The PDF preserves diagram and language appearance using rasterized sections, with page numbering; selectable text remains available through Premium Report → Print / Save PDF. Plan sections require an uploaded or drawn floor. An empty selection disables download. Export errors appear next to the button, and temporary export content is removed afterward. All PDF export code ships in `vendor/report-pdf.js`; it works without node_modules or a CDN. Run `npm run build:report` after changing its dependencies.

The 3D viewer now uses original rounded procedural models for beds (headboard, mattress, pillows and covers), cushioned sofas, dining tables and chairs, coffee tables, storage, lamps, toilets, sinks and puja units. Furniture keeps the saved footprint and orientation. Wood/fabric textures, softer lighting, Daylight/Warm interior/Studio presets, room-label visibility and full screen improve presentation. Models are approximations; they are not Coohom's proprietary catalog or a photorealistic rendering service. The requested Coohom and Occult King homepages returned network 403 errors in this environment, so this update follows the supplied screenshots and the consultation workflow rather than claiming a live-site inspection or integration.
