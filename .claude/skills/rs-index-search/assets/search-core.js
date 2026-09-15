  // RS-SEARCH-CORE-START
  // Pure search functions (no DOM). Shared by every Return Stacked index
  // widget; the canonical copy lives in
  // .claude/skills/rs-index-search/assets/search-core.js and is spliced
  // in by scripts/sync_search_core.py (never edit it inside a widget).
  // The regression runner (scripts/test_search.js) extracts this block
  // from the built file and replays it, so keep both markers. The whole
  // widget script must stay free of the ampersand and angle-bracket
  // characters (Divi Code Module / optimizer rule), hence the Math.min
  // helpers instead of comparison operators and nested ifs instead of
  // logical and.
  function __NS__LE(a, b) { return Math.min(a, b) === a; }
  function __NS__LT(a, b) { if (a === b) return false; return Math.min(a, b) === a; }

  // Porter stemmer (M. F. Porter, 1980). taxation, taxes and tax reduce
  // to taxat / tax / tax; the two-way prefix rule in __NS__TermHit then
  // joins them. Replaces the old strip-a-trailing-s stemmer, which is
  // why "taxation" used to find nothing.
  var __NS__Step2 = { ational: 'ate', tional: 'tion', enci: 'ence', anci: 'ance', izer: 'ize', bli: 'ble', alli: 'al', entli: 'ent', eli: 'e', ousli: 'ous', ization: 'ize', ation: 'ate', ator: 'ate', alism: 'al', iveness: 'ive', fulness: 'ful', ousness: 'ous', aliti: 'al', iviti: 'ive', biliti: 'ble', logi: 'log' };
  var __NS__Step3 = { icate: 'ic', ative: '', alize: 'al', iciti: 'ic', ical: 'ic', ful: '', ness: '' };
  var __NS__C = '[^aeiou]';
  var __NS__V = '[aeiouy]';
  var __NS__Cs = __NS__C + '[^aeiouy]*';
  var __NS__Vs = __NS__V + '[aeiou]*';
  var __NS__Mgr0 = new RegExp('^(' + __NS__Cs + ')?' + __NS__Vs + __NS__Cs);
  var __NS__Meq1 = new RegExp('^(' + __NS__Cs + ')?' + __NS__Vs + __NS__Cs + '(' + __NS__Vs + ')?$');
  var __NS__Mgr1 = new RegExp('^(' + __NS__Cs + ')?' + __NS__Vs + __NS__Cs + __NS__Vs + __NS__Cs);
  var __NS__HasV = new RegExp('^(' + __NS__Cs + ')?' + __NS__V);
  var __NS__Cvc = new RegExp('^' + __NS__C + __NS__V + '[^aeiouwxy]$');
  var __NS__Double = new RegExp('([^aeiouylsz])\\1$');

  function __NS__Stem(word) {
    var w = word;
    var fp, stem;
    if (__NS__LT(w.length, 3)) return w;
    var firstch = w.charAt(0);
    if (firstch === 'y') w = 'Y' + w.slice(1);

    // Step 1a: plurals
    fp = /^(.+?)(ss|i)es$/.exec(w);
    if (fp) w = fp[1] + fp[2];
    else {
      fp = /^(.+?)([^s])s$/.exec(w);
      if (fp) w = fp[1] + fp[2];
    }
    // Step 1b: -eed, -ed, -ing
    fp = /^(.+?)eed$/.exec(w);
    if (fp) {
      if (__NS__Mgr0.test(fp[1])) w = w.slice(0, -1);
    } else {
      fp = /^(.+?)(ed|ing)$/.exec(w);
      if (fp) {
        stem = fp[1];
        if (__NS__HasV.test(stem)) {
          w = stem;
          if (/(at|bl|iz)$/.test(w)) w = w + 'e';
          else if (__NS__Double.test(w)) w = w.slice(0, -1);
          else if (__NS__Cvc.test(w)) w = w + 'e';
        }
      }
    }
    // Step 1c: y to i
    fp = /^(.+?)y$/.exec(w);
    if (fp) { if (__NS__HasV.test(fp[1])) w = fp[1] + 'i'; }
    // Step 2
    fp = /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/.exec(w);
    if (fp) { if (__NS__Mgr0.test(fp[1])) w = fp[1] + __NS__Step2[fp[2]]; }
    // Step 3
    fp = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/.exec(w);
    if (fp) { if (__NS__Mgr0.test(fp[1])) w = fp[1] + __NS__Step3[fp[2]]; }
    // Step 4
    fp = /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/.exec(w);
    if (fp) {
      if (__NS__Mgr1.test(fp[1])) w = fp[1];
    } else {
      fp = /^(.+?)(s|t)(ion)$/.exec(w);
      if (fp) { if (__NS__Mgr1.test(fp[1] + fp[2])) w = fp[1] + fp[2]; }
    }
    // Step 5
    fp = /^(.+?)e$/.exec(w);
    if (fp) {
      stem = fp[1];
      if (__NS__Mgr1.test(stem)) w = stem;
      else if (__NS__Meq1.test(stem)) { if (!__NS__Cvc.test(stem)) w = stem; }
    }
    if (/ll$/.test(w)) { if (__NS__Mgr1.test(w)) w = w.slice(0, -1); }

    if (firstch === 'y') w = 'y' + w.slice(1);
    return w;
  }

  function __NS__Tokens(text) {
    var out = [];
    (text || '').toLowerCase().split(/[^a-z0-9]+/).forEach(function (w) {
      if (w) out.push(__NS__Stem(w));
    });
    return out;
  }

  // Synonym concept groups (search-synonyms.json, rendered in by
  // sync_search_core.py). A group fires for an element when any of its
  // phrases occurs in the element's stems (each phrase word in sequence;
  // the last word may be a prefix of the text stem, so "tax" fires on
  // "taxation"). Every word of every phrase in a fired group is then
  // appended to the element's stems, so "cta" finds an item that only
  // says "managed futures". Computed once per element (see the stem
  // cache on the DOM side).
  var __NS__SynPhrases = __SYNONYM_GROUPS__;
  var __NS__SynStems = null;
  function __NS__SynPrep() {
    if (__NS__SynStems === null) {
      __NS__SynStems = __NS__SynPhrases.map(function (group) {
        return group.map(function (phrase) { return __NS__Tokens(phrase); });
      });
    }
    return __NS__SynStems;
  }
  function __NS__PhraseAt(textStems, phrase, i) {
    var last = phrase.length - 1;
    for (var j = 0; j !== last; j++) {
      if (textStems[i + j] !== phrase[j]) return false;
    }
    var t = textStems[i + last];
    if (t === undefined) return false;
    return t.indexOf(phrase[last]) === 0;
  }
  function __NS__PhraseIn(textStems, phrase) {
    if (phrase.length === 0) return false;
    for (var i = 0; i !== textStems.length; i++) {
      if (__NS__PhraseAt(textStems, phrase, i)) return true;
    }
    return false;
  }
  function __NS__Expand(textStems) {
    var groups = __NS__SynPrep();
    var have = Object.create(null);
    var out = textStems.slice();
    textStems.forEach(function (s) { have[s] = true; });
    groups.forEach(function (group) {
      var fires = group.some(function (phrase) { return __NS__PhraseIn(textStems, phrase); });
      if (!fires) return;
      group.forEach(function (phrase) {
        phrase.forEach(function (s) {
          if (__NS__LT(s.length, 3)) return;
          if (!have[s]) { have[s] = true; out.push(s); }
        });
      });
    });
    return out;
  }
  // Stems for an element's searchable text: tokens plus synonym expansion.
  function __NS__TextStems(text) {
    return __NS__Expand(__NS__Tokens(text));
  }

  // True when a and b are identical or one edit apart (a substitution,
  // an insertion, a deletion, or two adjacent letters swapped).
  function __NS__OneEdit(a, b) {
    if (a === b) return true;
    var la = a.length;
    var lb = b.length;
    var i;
    if (la === lb) {
      var diff = [];
      for (i = 0; i !== la; i++) { if (a.charAt(i) !== b.charAt(i)) diff.push(i); }
      if (diff.length === 1) return true;
      if (diff.length === 2) {
        if (diff[1] === diff[0] + 1) {
          if (a.charAt(diff[0]) === b.charAt(diff[1])) { if (a.charAt(diff[1]) === b.charAt(diff[0])) return true; }
        }
      }
      return false;
    }
    var longer = a;
    var shorter = b;
    if (__NS__LT(la, lb)) { longer = b; shorter = a; }
    if (longer.length !== shorter.length + 1) return false;
    i = 0;
    while (i !== shorter.length) {
      if (longer.charAt(i) !== shorter.charAt(i)) break;
      i++;
    }
    return longer.slice(i + 1) === shorter.slice(i);
  }

  // Does text stem t satisfy query stem q?
  //   1. q is a prefix of t            (tax finds taxat, stack finds stacking)
  //   2. t is a prefix of q: t 4+ chars (stacking finds stack), or t is
  //      3 chars and more than half of q (taxat finds tax, but theori
  //      does not find the)
  //   3. q is 5+ chars and one edit away from t or from t's head (levrag finds leverag)
  function __NS__TermHit(t, q) {
    if (t.indexOf(q) === 0) return true;
    if (q.indexOf(t) === 0) {
      if (__NS__LE(4, t.length)) return true;
      if (t.length === 3) { if (__NS__LT(q.length, 6)) return true; }
    }
    if (__NS__LE(5, q.length)) {
      if (__NS__OneEdit(q, t)) return true;
      if (__NS__LT(q.length, t.length)) { if (__NS__OneEdit(q, t.slice(0, q.length))) return true; }
    }
    return false;
  }

  function __NS__Query(raw) {
    return __NS__Tokens((raw || '').trim().toLowerCase());
  }

  // mode 'all': every query stem must hit a text stem.
  // mode 'any': at least one must (the fallback when 'all' finds nothing).
  function __NS__MatchText(textStems, queryStems, mode) {
    if (queryStems.length === 0) return true;
    var hits = 0;
    for (var i = 0; i !== queryStems.length; i++) {
      var found = false;
      for (var j = 0; j !== textStems.length; j++) {
        if (__NS__TermHit(textStems[j], queryStems[i])) { found = true; break; }
      }
      if (found) hits++;
      else if (mode !== 'any') return false;
    }
    return hits !== 0;
  }
  // RS-SEARCH-CORE-END
