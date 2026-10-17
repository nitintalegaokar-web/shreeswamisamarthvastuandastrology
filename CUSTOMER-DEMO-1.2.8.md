# KP MASTER customer demo · 1.2.8

Distribute only the customer demo installer/APK to customers. Keep the owner activation tool on your own computer.

- 15 kundali calculations and 10 matchmaking calculations, counted separately.
- The initial chart calculated when the app opens uses one kundali credit, so restarting cannot generate unlimited free charts.
- Every new Calculate / View action counts, including the same birth details or pair again. Internal refreshes for one action use the same credit.
- Editing a form or printing an already calculated result does not consume another credit.
- Usage is saved in native application data, outside chart files and chart backups. Registration does not reset it.
- After the relevant allowance is exhausted, that calculation requires registration and purchase. Any remaining allowance for the other feature stays available.

## Unlocking full use

1. Customer selects **Register / Purchase** and sends the displayed System ID to you.
2. In the updated owner activation tool, enter the customer name and System ID. Choose **1 · Registration key**, generate it and send the complete KP-R1 key.
3. With the same name and System ID, choose **2 · Purchase key**, set permanent access or an expiry date, generate it and send the complete KP-A1 key.
4. Customer enters registration first, then purchase. Registration alone does not unlock full use.

Use the purchase record for subsequent Activate / Deactivate status keys. Existing saved paid licences continue to work; expired or deactivated licences do not fall back to demo. Owner calculator copies are unlimited.

## Validation

Native Windows counter tests and Android JVM tests cover both limits, repeated calculations, persistence, invalid signatures, device binding and two-key activation. The customer UI adapter is tested with a simulated DOM. Approved calculation engines remain unchanged; the packaged customer HTML adds only a matchmaking access guard and the demo adapter. Windows and physical Android UI checks were not completed because the browser permission request was interrupted.

The demo uses offline device storage. Clearing Android app data, removing all native application data or modifying the application is outside its persistence guarantees; an online licensing service would be needed to enforce quotas across those resets.

## Included interface corrections

Automatic Horary results default to the present MD / AD / PD instead of the birth/query instant. A beside-table shows the three period lords, their houses, exact native period ranges and event-house checks; manual MD / AD / PD selectors and Current DBA are available. On narrow screens it stacks below the sheet. Event choices begin with their names, preserving internal IDs for keyboard selection and rule mapping.

Ruling Planet timing opens with the saved astrologer default place and DMS coordinates. Its place lookup uses DMS. Numeric location fields in other workspaces use visible DMS inputs over the existing decimal engine values.
