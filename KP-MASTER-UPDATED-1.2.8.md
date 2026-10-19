# KP MASTER 1.2.8 · Updated Windows and web builds

Windows x64 installers:

- [Customer](KP-Master-Customer-Setup-1.2.8-x64.exe): existing demo/registration/purchase flow, plus owner-signed package features.
- [Owner](KP-Master-Owner-Setup-1.2.8-x64.exe): unlocked calculator.
- [Owner Activation](KP-Master-Owner-Activation-Setup-1.2.8-x64.exe): choose a package name and purchased features when issuing a customer key.

Web archives:

- [Customer Web](KP-MASTER-Customer-Web-1.2.8.zip): signed registration/purchase keys tied to the browser profile and site address. Browser source remains inspectable; this is not native distribution protection.
- [Owner Web](KP-MASTER-Owner-Web-1.2.8.zip): unlocked, self-contained HTML.

The updated builds include full truncated planet names on hover (also inside enlarged dialogs), RP settings and complete primary/supporting event houses, improved A4 evidence flow and repeating page borders, Vedic-only symbol references and the offline [12-page tutorial PDF](docs/KP-MASTER-User-Tutorial-1.2.8.pdf) in Help. They also apply the confirmed gemstone house exceptions and English/Marathi colour legends, and remove the redundant report photo-library button.

**Android APK upgrades are not built.** The original private Android signing directory is missing. Restore `release.p12` and `store-password.txt` privately to build an update with the existing certificate. No replacement signing identity was generated, and older APKs are not presented as current builds.

29 unit-test files passed, Android licence/control tests passed 20 assertions, browser interaction/print tests passed, and the Windows installers' packaged sources were checked against the reviewed build sources. Installation on Windows and testing on a physical Android phone were not performed in this environment. See the release JSON and SHA256SUMS for individual artifact checksums.
