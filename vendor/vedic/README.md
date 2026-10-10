# Vedic calculation conventions

The three JavaScript files are independent implementations. `engine.js` contains pure arithmetic, `adapter.js` supplies the current native chart and astronomy, and `ui.js` builds the consultation and print reports. The same files are embedded in `index.html`; the private server executes those embedded versions, returning presentation snapshots only.

## Inputs and scope

Every report uses the native chart's actual sidereal longitudes, Ascendant, birth moment, coordinates and selected ayanamsha. Whole-sign houses are used in Parashari divisional and Manglik reports; the KP cusp report retains the original KP cusps. Seven classical planets contribute to strengths and Ashtakavarga. Rahu and Ketu appear in charts, with no invented node Shadbala or Ashtakavarga. Incomplete astronomical context is reported as unavailable.

## Parashari divisions and strengths

Sixteen divisions are implemented: D1/2/3/4/7/9/10/12/16/20/24/27/30/40/45/60. D2 uses Sun/Moon Hora, D3 traditional trines, D30 the unequal five classical portions, and D60 counts forward from the natal sign. Higher divisions are sensitive to birth-time accuracy. Alternative Hora, Drekkana and D60 schools are not mixed into these defaults.

Vimshopaka uses the classical six/seven/ten/sixteen division weight sets, each summing to 20. Own/great friend/friend/neutral/enemy/great enemy score 20/18/15/10/7/5; compound relationships use native Rashi temporary friendship. Vaisheshikamsa counts own or exalted divisions, with the qualifying division numbers printed.

Shadbala prints Sthana, Dig, Kala, Cheshta, Naisargika and Drik in virupas, total, rupas, conventional required strength and ratio. Sthana includes angular exaltation strength, Saptavargaja dignity, Ojayugma, Kendra and Drekkana. Moolatrikona degree ranges are applied in D1. Dig uses the original native cardinal cusp longitudes. Kala includes solar-hour-angle Nathonnatha, lunar Paksha, actual day/night thirds, traditional 360-day year/30-day month lords, sunrise weekday, equal clock-hour Hora and declination Ayana. The day/night boundaries come from actual solar events. Astronomical declinations use the equator of date.

Mean motions for classical Cheshta use the Surya Siddhanta Mahayuga revolution table (civil days 1,577,917,828), the Kali epoch and Ujjain meridian. Outer planets use mean planet/mean Sun; Mercury/Venus use mean Sun/mean planet; circular midpoint and shortest angle remove wrap errors. Luminaries have zero separate Cheshta: their motion factors occur in Kala's Ayana/Paksha; those factors divided by two are used in their Ishta/Kashta calculation. Drik uses continuous graded graha aspects (quarter/half/three-quarter/full), with full special peaks for Mars 4/8, Jupiter 5/9 and Saturn 3/10. It is independent of the Western orb matrix. Natural benefics are Jupiter/Venus, waxing Moon and Mercury without co-sign malefics. Bhava Bala combines the house lord's total strength, sign-type Dig and signed aspect strength. Graha Yuddha is limited to Mars through Saturn within one degree; ecliptic latitude chooses the northern winner and classical disc-diameter differences distribute strength. A latitude tie is unavailable for review.

These defaults identify one traditional convention; different dignity ranges, mean-motion epochs, graded-aspect treatments and Bhava systems can produce different strength tables. They have not been claimed as bit-for-bit identical to another astrology package.

## Ashtakavarga and chakra

The classical favorable-house tables have seven Bhinna totals 48/49/39/54/56/52/39 and a Sarva total of **337**. Lagna contributes to each Bhinna, without adding an eighth Bhinna to Sarva. Prastara retains all eight contributors. Trikona and Ekadhipatya reductions precede Rashi/Graha/Shodhya Pinda. Rashi multipliers are 7/10/8/4/10/5/7/8/9/5/11/12 (Virgo=5 convention); planetary multipliers are 5/5/8/5/10/7/5.

Sarvatobhadra displays the traditional 9×9 nakshatra/sign/letter/tithi-weekday grid with native planetary positions. Abhijit is explicitly 276°40′–280°53′20″. This report is a chakra of placements; it does not claim an automatic Vedha or event verdict.

## Dasha, Saturn and annual reports

Full MD/Bhukti and current Bhukti/Antara, Antara/Sukshma and Sukshma/Prana use the existing Vimshottari hierarchy and native local offset. Child periods are clipped to the birth/parent interval while subdivision anchors remain unchanged. End times are exclusive.

Sade Sati searches actual Saturn longitude in the 12th, natal and 2nd signs from the natal Moon. Retrograde exits and re-entries are preserved. It searches from birth to 120 sidereal years, within the existing 1900–2100 astronomy range; clipped endpoints are marked. Saturn sign searches use weekly brackets, detect and refine retrograde stations, and refine sign entries/exits to one second. A regression comparison against the original half-day brackets covers forward and retrograde sign crossings; other transit searches retain their existing brackets. These are astronomical phase intervals, not claims of particular life outcomes.

Varshaphal returns the sidereal Sun to its exact natal longitude, at the native location. It supplies the annual kundali, progressed Muntha, annual/natal Ascendant lords and day/night lord. Mudda Vimshottari starts with the traditional birth-nakshatra/completed-age remainder and scales the nine planet-year proportions to the actual return-to-return interval. It does not supply unimplemented Tajika yogas or a fabricated annual prediction. Annual year must follow the birth year.

## Rule references and validation

Traditional numerical tables and rule definitions were cross-checked against the Parashari sections described in *Brihat Parashara Hora Shastra*, B. V. Raman's *Graha and Bhava Balas*, P. V. R. Narasimha Rao's *Vedic Astrology: An Integrated Approach*, and publicly documented Surya Siddhanta mean-motion constants. Published software tables were consulted as factual cross-checks; no external Python implementation is bundled or required. These references belong in developer documentation, not customer prediction/print rows.

Tests check division boundaries, classical Bhinna/Sarva totals, rotation invariance, reductions, independent strength geometry, the astronomical solar-return residual, Saturn sign membership, contiguous Mudda endpoints, grouped report selection, physical A4 pages, Marathi presentation, transient hover and private-server report exports. They do not establish guaranteed real-world event dates.
