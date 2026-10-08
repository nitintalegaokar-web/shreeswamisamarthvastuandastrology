# Offline interface language packs

The English interface is the default. Navigation and common controls cover India's 22 scheduled languages; Marathi, Hindi, Tamil, Gujarati, Kannada and Telugu also have expanded settings and chart labels. The dictionaries are embedded in `index.html` so the standalone calculator does not contact a translation service or send chart information anywhere.

`interface-packs.json` records the language codes and display dictionaries. When updating a pack, update the embedded `kp-interface-languages` data in `index.html` as well. Missing translations retain the original English text. Detailed explanations are not fully translated in every language; imported rule text, personal notes and place names keep their original wording. Technical identifiers, input values, degrees and calculation data are not translated.

Translations should be reviewed by fluent speakers before claiming complete localization. The settings language choice is persisted with the other astrologer preferences. Existing bilingual English/Marathi preferences remain supported.
