// Search-core regression runner for the Return Stacked index widgets.
//
//   node test_search.js <search-tests.json>
//
// Reads the widget's built file named in the config, extracts the pure
// search core (between the RS-SEARCH-CORE markers), rebuilds each item's
// searchable text the way the widget does (visible text + data-* search
// attributes), and checks hit counts for the queries listed in the config.
// A few stemmer / typo guard rails run for every widget.
//
// Config keys:
//   file          built file, relative to the config (the embed for a built
//                 widget, the single HTML file for a hand-maintained one)
//   slice         optional [fromMarker, toMarker]: only items between the
//                 first occurrences of these strings count (dedupes a widget
//                 that repeats posts across tile views)
//   itemTags      tag names that carry data-tags (default ["li", "a"])
//   itemClass     optional class an item must carry
//   dedupeAttr    attribute that identifies an item (default: href, then
//                 data-url); items sharing it count once
//   searchAttrs   data-* names joined into the text (default keywords tags
//                 topics concepts search)
//   tileContext   optional {nameClass, descClass, skipClass}: items that are
//                 not skipClass also get the nearest preceding tile name and
//                 description (Literature widget behaviour)
//   titleRe       optional regex (string) whose group 1 is the item title
//   minItems      fail if fewer items were parsed
//   checks        list of {q, mode?, atLeast?, exactly?, sameAs?, all?,
//                 excludesTitle?, includesTitle?, as?}; `as` names a count
//                 that later checks can reference with sameAs.
'use strict';
var fs = require('fs');
var path = require('path');

var cfgPath = process.argv[2];
if (!cfgPath) { console.error('usage: node test_search.js <search-tests.json>'); process.exit(2); }
var cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
var file = path.resolve(path.dirname(cfgPath), cfg.file);
var html = fs.readFileSync(file, 'utf8');

// 1. Pull the search core out of the file and evaluate it.
var startMark = '// RS-SEARCH-CORE-START';
var endMark = '// RS-SEARCH-CORE-END';
var s = html.indexOf(startMark);
var e = html.indexOf(endMark);
if (s === -1 || e === -1) { console.error('FAIL: RS-SEARCH-CORE markers not found in ' + file); process.exit(1); }
var coreSrc = html.slice(s + startMark.length, e);
if (/[&<>]/.test(coreSrc)) { console.error('FAIL: search core contains &, < or >'); process.exit(1); }
var nsMatch = /function\s+([A-Za-z0-9]+?)LE\s*\(/.exec(coreSrc);
if (!nsMatch) { console.error('FAIL: could not detect the namespace prefix'); process.exit(1); }
var ns = nsMatch[1];
var core = new Function(coreSrc + '\nreturn { stem: ' + ns + 'Stem, tokens: ' + ns + 'Tokens, textStems: ' + ns + 'TextStems, termHit: ' + ns + 'TermHit, query: ' + ns + 'Query, matchText: ' + ns + 'MatchText, groups: ' + ns + 'SynPhrases };')();

// 2. Rebuild the searchable text of every item.
function unesc(t) {
  return t.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ').replace(/&middot;/g, ' ').replace(/&reg;/g, '').replace(/&[a-z]+;/g, ' ');
}
function stripTags(t) { return unesc(t.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim(); }

var region = html;
var regionOffset = 0;
if (cfg.slice) {
  var a = html.indexOf(cfg.slice[0]);
  var b = html.indexOf(cfg.slice[1], a + 1);
  if (a === -1 || b === -1) { console.error('FAIL: slice markers not found'); process.exit(1); }
  region = html.slice(a, b);
  regionOffset = a;
}
var itemTags = cfg.itemTags || ['li', 'a'];
var searchAttrs = cfg.searchAttrs || ['keywords', 'tags', 'topics', 'concepts', 'search'];
var openRe = new RegExp('<(' + itemTags.join('|') + ')\\b([^>]*\\bdata-tags="[^>]*)>', 'g');
var attrRe = /\b(data-[a-z-]+|href|class)="([^"]*)"/g;
var titleRe = cfg.titleRe ? new RegExp(cfg.titleRe) : null;

// Tile context: nearest preceding tile name / description.
var tiles = [];
if (cfg.tileContext) {
  var nameRe = new RegExp('class="' + cfg.tileContext.nameClass + '"[^>]*>([\\s\\S]*?)<\\/', 'g');
  var descRe = new RegExp('class="' + cfg.tileContext.descClass + '"[^>]*>([\\s\\S]*?)<\\/', 'g');
  var tm;
  while ((tm = nameRe.exec(html)) !== null) tiles.push({ at: tm.index, name: stripTags(tm[1]), desc: '' });
  while ((tm = descRe.exec(html)) !== null) {
    for (var ti = tiles.length - 1; ti !== -1; ti--) { if (tiles[ti].at < tm.index) { tiles[ti].desc = stripTags(tm[1]); break; } }
  }
}
function tileTextBefore(pos) {
  var best = null;
  tiles.forEach(function (t) { if (t.at < pos) best = t; });
  return best ? best.name + ' ' + best.desc : '';
}

var items = {};
var titles = {};
var order = [];
var m;
while ((m = openRe.exec(region)) !== null) {
  var tag = m[1];
  var attrs = {};
  var am;
  while ((am = attrRe.exec(m[2])) !== null) attrs[am[1]] = unesc(am[2]);
  var cls = ' ' + (attrs['class'] || '') + ' ';
  if (cfg.itemClass && cls.indexOf(' ' + cfg.itemClass + ' ') === -1) continue;
  var closeAt = region.indexOf('</' + tag + '>', m.index);
  if (closeAt === -1) continue;
  var inner = region.slice(m.index + m[0].length, closeAt);
  var parts = [stripTags(inner)];
  searchAttrs.forEach(function (k) { parts.push(attrs['data-' + k] || ''); });
  if (cfg.tileContext) {
    if (cls.indexOf(' ' + cfg.tileContext.skipClass + ' ') === -1) parts.push(tileTextBefore(regionOffset + m.index));
  }
  var key = cfg.dedupeAttr ? attrs[cfg.dedupeAttr] : (attrs['href'] || attrs['data-url']);
  if (!key) key = 'item-' + order.length;
  if (!items[key]) {
    order.push(key);
    items[key] = parts.join(' ');
    var t = titleRe ? titleRe.exec(inner) : null;
    titles[key] = t ? stripTags(t[1]) : stripTags(inner).slice(0, 80);
  } else {
    items[key] += ' ' + parts.join(' ');
  }
}
if (order.length < (cfg.minItems || 1)) { console.error('FAIL: only parsed ' + order.length + ' items from ' + file); process.exit(1); }

var stemsOf = {};
order.forEach(function (k) { stemsOf[k] = core.textStems(items[k]); });

function matching(q, mode) {
  var qs = core.query(q);
  return order.filter(function (k) { return core.matchText(stemsOf[k], qs, mode || 'all'); });
}
function count(q, mode) { return matching(q, mode).length; }

// 3. Assertions.
var failures = 0;
function check(label, ok, detail) {
  console.log((ok ? 'ok   ' : 'FAIL ') + label + (detail !== undefined ? '  (' + detail + ')' : ''));
  if (!ok) failures++;
}

console.log(path.basename(file) + ': ' + order.length + ' items, namespace ' + ns + ', ' + core.groups.length + ' synonym groups');

// Guard rails that hold for every widget.
check('stem(taxation) and stem(tax) hit each other', core.termHit(core.stem('taxation'), core.stem('tax')) && core.termHit(core.stem('tax'), core.stem('taxation')));
check('stem(diversify) hits stem(diversification)', core.termHit(core.stem('diversification'), core.stem('diversify')));
check('stem(stacking) hits stem(stack)', core.termHit(core.stem('stack'), core.stem('stacking')));
check('short text token does not hit long query by reverse prefix', !core.termHit(core.stem('in'), core.stem('inflation')));
check('levrage hits leverage (one edit)', core.termHit(core.stem('leverage'), core.stem('levrage')));
check('protfolio hits portfolio (transposition)', core.termHit(core.stem('portfolio'), core.stem('protfolio')));
check('theory does not hit the (3-char token, reverse prefix)', !core.termHit(core.stem('the'), core.stem('theory')));
check('short words get no typo tolerance: gild vs gold', !core.termHit(core.stem('gold'), core.stem('gild')));
check('synonym expansion: "managed futures" text gains cta', core.textStems('managed futures overlay').indexOf(core.stem('cta')) !== -1);
check('synonym expansion: unrelated text gains nothing', core.textStems('purple elephant').length === 2);
check('empty query matches every item', count('') === order.length, count(''));

var named = {};
(cfg.checks || []).forEach(function (c) {
  var mode = c.mode || 'all';
  var label = '"' + c.q + '"' + (mode === 'any' ? ' [any]' : '');
  var n = count(c.q, mode);
  if (c.as) named[c.as] = n;
  if (c.atLeast !== undefined) check(label + ' matches at least ' + c.atLeast, Math.max(n, c.atLeast) === n, n);
  if (c.exactly !== undefined) check(label + ' matches exactly ' + c.exactly, n === c.exactly, n);
  if (c.sameAs !== undefined) check(label + ' agrees with "' + c.sameAs + '"', n === named[c.sameAs], n + ' vs ' + named[c.sameAs]);
  if (c.all) check(label + ' matches every item', n === order.length, n);
  if (c.excludesTitle !== undefined) {
    var hit = matching(c.q, mode).some(function (k) { return titles[k].indexOf(c.excludesTitle) === 0; });
    check(label + ' does not surface "' + c.excludesTitle + '"', !hit);
  }
  if (c.includesTitle !== undefined) {
    var has = matching(c.q, mode).some(function (k) { return titles[k].indexOf(c.includesTitle) === 0; });
    check(label + ' surfaces "' + c.includesTitle + '"', has);
  }
  if (c.list) console.log('     ' + matching(c.q, mode).map(function (k) { return titles[k]; }).join(' | '));
});

console.log(failures === 0 ? '\nALL PASS (' + order.length + ' items)' : '\n' + failures + ' FAILURE(S)');
process.exit(failures === 0 ? 0 : 1);
