'use strict';
const catalog=require('./features.json'),ids=Object.freeze(catalog.map(f=>f.id));
function normalizeFeatures(value){if(!Array.isArray(value)||value.some(id=>typeof id!=='string'||!ids.includes(id)))throw Error('Choose valid customer features.');return ids.filter(id=>value.includes(id));}
function entitlements(claims){return Object.freeze(claims?.features===undefined?[...ids]:normalizeFeatures(claims.features));}
function edition(value){const text=String(value||'Custom').trim();if(!text||text.length>80||/[\x00-\x1f]/.test(text))throw Error('Enter a package name of 1–80 characters.');return text;}
module.exports={catalog,ids,normalizeFeatures,entitlements,edition};
