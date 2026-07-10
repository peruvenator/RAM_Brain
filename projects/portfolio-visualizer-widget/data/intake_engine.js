/* ============================================================================
   Flexible custom-data intake engine.
   Injected verbatim by build_widget.py (raw JS, NOT inside the f-string), so
   this file uses normal single braces / backslashes — do not double-escape.

   File ingestion (parseDelimited, parseNumber, xlsx reader) is ported from the
   portfolio-x-ray-widget builder. The time-series layer (month parsing,
   price/return detection, column mapping) is specific to this widget.
   ============================================================================ */

/* ---- delimited text (CSV / TSV / pasted spreadsheet) -> rows[][] ---- */
function rsvParseDelimited(text) {
  text = String(text || '').replace(/^﻿/, '');
  var lines = text.split(/\r\n|\n|\r/);
  var counts = { '\t': 0, ',': 0, ';': 0 };
  lines.forEach(function (ln) {
    Object.keys(counts).forEach(function (d) {
      if (ln.indexOf(d) !== -1) counts[d] += 1;
    });
  });
  var delim = '\t';
  if (counts[','] > counts['\t'] && counts[','] >= counts[';']) delim = ',';
  else if (counts[';'] > counts['\t'] && counts[';'] > counts[',']) delim = ';';
  var rows = [];
  lines.forEach(function (ln) {
    if (!ln.trim()) return;
    var cells = [], cur = '', inQ = false;
    for (var i = 0; i < ln.length; i++) {
      var ch = ln[i];
      if (inQ) {
        if (ch === '"') {
          if (ln[i + 1] === '"') { cur += '"'; i++; }
          else inQ = false;
        } else cur += ch;
      } else if (ch === '"') inQ = true;
      else if (ch === delim) { cells.push(cur); cur = ''; }
      else cur += ch;
    }
    cells.push(cur);
    rows.push(cells.map(function (c) { return c.trim(); }));
  });
  return rows;
}

/* ---- lenient number parse: handles $, commas, %, (123) negatives ---- */
function rsvParseNumber(s) {
  var t = String(s === undefined || s === null ? '' : s)
    .replace(/[$,\s%]/g, '').replace(/^\((.*)\)$/, '-$1');
  if (!t || t === '-') return null;
  var v = parseFloat(t);
  return isNaN(v) ? null : v;
}

/* ---- native .xlsx reading (zip directory + DecompressionStream) ---- */
function rsvInflateEntry(bytes, method) {
  if (method === 0) return Promise.resolve(bytes);
  if (typeof DecompressionStream === 'undefined') {
    return Promise.reject(new Error('This browser cannot read .xlsx directly — save as CSV or paste the data instead.'));
  }
  var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
  return new Response(stream).arrayBuffer().then(function (ab) { return new Uint8Array(ab); });
}
function rsvParseZipEntries(buf) {
  var dv = new DataView(buf);
  var i = buf.byteLength - 22;
  while (i >= 0 && dv.getUint32(i, true) !== 0x06054b50) i--;
  if (i < 0) throw new Error('Not a valid .xlsx file.');
  var count = dv.getUint16(i + 10, true);
  var p = dv.getUint32(i + 16, true);
  var u8 = new Uint8Array(buf);
  var entries = [];
  for (var k = 0; k < count; k++) {
    if (dv.getUint32(p, true) !== 0x02014b50) break;
    var nameLen = dv.getUint16(p + 28, true);
    var extraLen = dv.getUint16(p + 30, true);
    var commentLen = dv.getUint16(p + 32, true);
    var name = '';
    for (var c = 0; c < nameLen; c++) name += String.fromCharCode(u8[p + 46 + c]);
    entries.push({
      name: name,
      method: dv.getUint16(p + 10, true),
      compSize: dv.getUint32(p + 20, true),
      localOff: dv.getUint32(p + 42, true)
    });
    p += 46 + nameLen + extraLen + commentLen;
  }
  return entries;
}
function rsvZipEntryData(buf, e) {
  var dv = new DataView(buf);
  var nameLen = dv.getUint16(e.localOff + 26, true);
  var extraLen = dv.getUint16(e.localOff + 28, true);
  return new Uint8Array(buf, e.localOff + 30 + nameLen + extraLen, e.compSize);
}
function rsvXlsxToRows(buf) {
  var entries = rsvParseZipEntries(buf);
  var sheets = entries.filter(function (e) { return /^xl\/worksheets\/sheet\d+\.xml$/.test(e.name); })
    .sort(function (a, b) {
      return parseInt(a.name.replace(/\D/g, ''), 10) - parseInt(b.name.replace(/\D/g, ''), 10);
    });
  if (!sheets.length) throw new Error('No worksheet found inside the .xlsx file.');
  var ss = entries.filter(function (e) { return e.name === 'xl/sharedStrings.xml'; })[0];
  var jobs = [rsvInflateEntry(rsvZipEntryData(buf, sheets[0]), sheets[0].method)];
  if (ss) jobs.push(rsvInflateEntry(rsvZipEntryData(buf, ss), ss.method));
  return Promise.all(jobs).then(function (parts) {
    var dec = new TextDecoder();
    var shared = [];
    if (parts[1]) {
      var ssDoc = new DOMParser().parseFromString(dec.decode(parts[1]), 'application/xml');
      Array.prototype.slice.call(ssDoc.getElementsByTagName('si')).forEach(function (si) {
        var txt = '';
        Array.prototype.slice.call(si.getElementsByTagName('t')).forEach(function (t) { txt += t.textContent; });
        shared.push(txt);
      });
    }
    var doc = new DOMParser().parseFromString(dec.decode(parts[0]), 'application/xml');
    var rows = [];
    Array.prototype.slice.call(doc.getElementsByTagName('row')).forEach(function (rowEl) {
      var cells = [];
      Array.prototype.slice.call(rowEl.getElementsByTagName('c')).forEach(function (cEl) {
        var ref = cEl.getAttribute('r') || '';
        var colIdx = 0;
        for (var i2 = 0; i2 < ref.length; i2++) {
          var ch = ref.charCodeAt(i2);
          if (ch >= 65 && ch <= 90) colIdx = colIdx * 26 + (ch - 64);
          else break;
        }
        colIdx = Math.max(0, colIdx - 1);
        var t = cEl.getAttribute('t');
        var val = '';
        if (t === 'inlineStr') {
          var ts = cEl.getElementsByTagName('t');
          for (var q = 0; q < ts.length; q++) val += ts[q].textContent;
        } else {
          var v = cEl.getElementsByTagName('v')[0];
          val = v ? v.textContent : '';
          if (t === 's') val = shared[parseInt(val, 10)] || '';
        }
        while (cells.length < colIdx) cells.push('');
        cells[colIdx] = String(val).trim();
      });
      rows.push(cells);
    });
    return rows;
  });
}

/* ---- flexible month parser: any common format -> "YYYY-MM" (or null) ---- */
var RSV_MONTH_NAMES = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
  jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
function rsvYm(y, mo) {
  if (!y || !mo || mo < 1 || mo > 12) return null;
  return y + '-' + (mo < 10 ? '0' + mo : '' + mo);
}
function rsvParseMonth(raw) {
  var s = String(raw == null ? '' : raw).trim();
  if (!s) return null;
  var m, y, mo, yy;
  // ISO: YYYY-MM or YYYY-MM-DD (also / or . separators)
  m = s.match(/^(\d{4})[-\/.](\d{1,2})(?:[-\/.]\d{1,2})?$/);
  if (m) return rsvYm(+m[1], +m[2]);
  // US: M/D/YYYY, M/D/YY, MM-DD-YYYY
  m = s.match(/^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{2,4})$/);
  if (m) {
    var a = +m[1], b = +m[2];
    yy = m[3];
    y = yy.length === 2 ? (+yy < 50 ? 2000 + +yy : 1900 + +yy) : +yy;
    mo = (a > 12 && b <= 12) ? b : a;   // default US MM/DD; swap only if impossible
    return rsvYm(y, mo);
  }
  // Month-name forms: "Jan 2020", "January 2020", "Jan-20", "2020 Jan", "Jan 31, 2020"
  var low = s.toLowerCase();
  var nameM = low.match(/[a-z]{3,}/);
  if (nameM && RSV_MONTH_NAMES[nameM[0].substring(0, 3)]) {
    mo = RSV_MONTH_NAMES[nameM[0].substring(0, 3)];
    var yearM = low.match(/\d{4}/);
    var yy2 = low.match(/[-\s'](\d{2})(?:\D|$)/);
    if (yearM) y = +yearM[0];
    else if (yy2) y = (+yy2[1] < 50 ? 2000 + +yy2[1] : 1900 + +yy2[1]);
    else return null;
    return rsvYm(y, mo);
  }
  // Excel serial date (bare integer in a plausible day range: ~1954-2119)
  if (/^\d{5}$/.test(s)) {
    var n = parseInt(s, 10);
    if (n >= 20000 && n <= 80000) {
      var dd = new Date(Date.UTC(1899, 11, 30) + n * 86400000);
      return rsvYm(dd.getUTCFullYear(), dd.getUTCMonth() + 1);
    }
  }
  return null;
}

/* ---- classify a numeric column: 'price' | 'ret_dec' | 'ret_pct' ---- */
function rsvDetectKind(nums) {
  var v = nums.filter(function (x) { return x !== null && x !== undefined && !isNaN(x); });
  if (v.length < 2) return 'ret_dec';
  var hasNonPos = v.some(function (x) { return x <= 0; });
  var abs = v.map(function (x) { return Math.abs(x); }).sort(function (a, b) { return a - b; });
  var medAbs = abs[Math.floor(abs.length / 2)];
  if (!hasNonPos) {
    // all positive: price levels drift (consecutive ratios near 1); returns jump around
    var near = 0, tot = 0;
    for (var i = 1; i < v.length; i++) {
      if (v[i - 1] === 0) continue;
      var r = v[i] / v[i - 1];
      tot++;
      if (r >= 0.5 && r <= 2) near++;
    }
    if (tot > 0 && near / tot > 0.7 && medAbs >= 0.5) return 'price';
  }
  return medAbs < 1 ? 'ret_dec' : 'ret_pct';
}

/* ---- messy rows -> { months[], series[{name,values,kind}], warnings[] } ---- */
function rsvExtractTimeSeries(rows) {
  var warnings = [];
  rows = (rows || []).filter(function (r) {
    return r && r.some(function (c) { return String(c == null ? '' : c).trim() !== ''; });
  });
  if (rows.length < 2) return { error: 'No data found. Expected a date column and at least one value column.' };
  var nCols = 0;
  rows.forEach(function (r) { nCols = Math.max(nCols, r.length); });

  // Date column = the column whose cells parse as months most often
  var dateCol = 0, best = -1;
  for (var c = 0; c < nCols; c++) {
    var hits = 0;
    for (var r = 0; r < rows.length; r++) if (rsvParseMonth(rows[r][c]) !== null) hits++;
    if (hits > best) { best = hits; dateCol = c; }
  }
  if (best < 2) return { error: 'Could not find a date column. Include monthly dates like 2020-01-31, Jan 2020, or 1/31/2020.' };

  // Header present if row 0's date cell does not parse as a date
  var hasHeader = rsvParseMonth(rows[0][dateCol]) === null;
  var headerRow = hasHeader ? rows[0] : null;
  var dataRows = hasHeader ? rows.slice(1) : rows;

  // Value columns = every non-date column with at least two numbers
  var valCols = [];
  for (var c3 = 0; c3 < nCols; c3++) {
    if (c3 === dateCol) continue;
    var numCount = 0;
    for (var r2 = 0; r2 < dataRows.length; r2++) if (rsvParseNumber(dataRows[r2][c3]) !== null) numCount++;
    if (numCount >= 2) valCols.push(c3);
  }
  if (!valCols.length) return { error: 'No numeric value columns found next to the date column.' };

  // Collect month -> values, skipping rows whose date does not parse
  var months = [], matrix = valCols.map(function () { return []; });
  for (var r3 = 0; r3 < dataRows.length; r3++) {
    var ym = rsvParseMonth(dataRows[r3][dateCol]);
    if (!ym) continue;
    months.push(ym);
    for (var vc = 0; vc < valCols.length; vc++) matrix[vc].push(rsvParseNumber(dataRows[r3][valCols[vc]]));
  }
  if (months.length < 2) return { error: 'Fewer than 2 dated rows recognized.' };

  // Sort ascending by month, drop duplicate months (keep first)
  var idx = months.map(function (m, i) { return i; });
  idx.sort(function (a, b) { return months[a] < months[b] ? -1 : months[a] > months[b] ? 1 : 0; });
  var sMonths = [], sMatrix = valCols.map(function () { return []; }), seen = {}, dupes = 0;
  idx.forEach(function (i) {
    if (seen[months[i]]) { dupes++; return; }
    seen[months[i]] = 1;
    sMonths.push(months[i]);
    for (var q = 0; q < valCols.length; q++) sMatrix[q].push(matrix[q][i]);
  });
  if (dupes) warnings.push(dupes + ' duplicate month row(s) ignored.');

  var series = valCols.map(function (col, k) {
    var nm = headerRow && headerRow[col] && String(headerRow[col]).trim()
      ? String(headerRow[col]).trim() : ('Custom ' + (k + 1));
    return { name: nm, values: sMatrix[k], kind: rsvDetectKind(sMatrix[k]) };
  });
  return {
    months: sMonths,
    series: series,
    dateColName: headerRow && headerRow[dateCol] ? String(headerRow[dateCol]).trim() || 'Date' : 'Date',
    warnings: warnings
  };
}
