# KP MASTER Owner edition

This is the full unlocked calculator for the owner. It has its own application
identity, installation folder and desktop shortcut, separate from the locked
customer edition and the key/activation tool. No production activation keys
are needed or packaged here.

From `desktop/`, run `npm run build:owner-edition:setup` to prepare the current
standalone software and build the owner installer. Use the pinned dependency
versions and caches documented in the parent README. From this folder, `npm ci`
uses its pinned lockfile and `npm start` launches this edition for development.

`npm run build:setup` from the parent folder builds the locked customer edition
and requires the real owner-exported public key. `npm run build:owner:setup`
builds the separate tool for private-key creation and signed license issuing.
Do not distribute this unlocked owner installer or the browser project to customers
who should receive the locked edition.
