// Run the simple visualizer's compute() verbatim against the embedded DATA
// and emit the same stats the widget displays.
const fs = require('fs');
const DATA = JSON.parse(fs.readFileSync('simple_visualizer_data.json', 'utf-8'));

// State copied from the disclosure in the screenshot:
//   60% Stocks / 40% Bonds / 30% Stack (33.34% MF, 33.33% MA, 33.33% Gold)
//   MF 0 bp fee / 50 bp financing; MA 0 bp fee / 50 bp financing; Gold 40 bp / 50 bp.
const state = {
  stockPct: 60, bondPct: 40,
  trendPct: 33.34, fyPct: 0, goldPct: 33.33, marbPct: 33.33,
  stackSize: 30,
  trendFee: 0, fyFee: 0, goldFee: 40, marbFee: 0,
  trendFinancing: 50, fyFinancing: 50, goldFinancing: 50, marbFinancing: 50,
};

function compute() {
  const { stockPct, bondPct, trendPct, fyPct, goldPct, marbPct, stackSize } = state;
  const sw = stockPct / 100, bw = bondPct / 100;
  const tw = trendPct / 100, fw = fyPct / 100, gw = goldPct / 100, mw = marbPct / 100;
  const ss = stackSize / 100;

  const fixedValues = [100];
  const stackedValues = [100];
  const labels = [DATA[0].date];

  for (let i = 1; i < DATA.length; i++) {
    const prev = DATA[i - 1], cur = DATA[i];
    const rStock = cur.stocks / prev.stocks - 1;
    const rBond = cur.bonds / prev.bonds - 1;
    const rTrend = cur.trend / prev.trend - 1;
    const rFy = cur.futuresYield / prev.futuresYield - 1;
    const rGold = cur.gold / prev.gold - 1;
    const rMarb = cur.mergerArb / prev.mergerArb - 1;
    const rTbill = cur.tbills / prev.tbills - 1;

    const rFixed = sw * rStock + bw * rBond;
    const trendNet = rTrend - state.trendFee / 10000 / 12;
    const fyNet = rFy - state.fyFee / 10000 / 12 - (rTbill + state.fyFinancing / 10000 / 12);
    const goldNet = rGold - state.goldFee / 10000 / 12 - (rTbill + state.goldFinancing / 10000 / 12);
    const marbNet = rMarb - state.marbFee / 10000 / 12 - (rTbill + state.marbFinancing / 10000 / 12);
    const trendFinanced = trendNet - (rTbill + state.trendFinancing / 10000 / 12);
    const rStacked = rFixed + ss * (tw * trendFinanced + fw * fyNet + gw * goldNet + mw * marbNet);

    fixedValues.push(fixedValues[i - 1] * (1 + rFixed));
    stackedValues.push(stackedValues[i - 1] * (1 + rStacked));
    labels.push(cur.date);
  }
  return { fixedValues, stackedValues, labels };
}

function computeStats(values) {
  const n = values.length - 1;
  const monthlyReturns = [];
  for (let i = 1; i < values.length; i++) {
    monthlyReturns.push(values[i] / values[i - 1] - 1);
  }
  const endVal = values[values.length - 1];
  const annReturn = Math.pow(endVal / values[0], 12 / n) - 1;
  const mean = monthlyReturns.reduce((a, b) => a + b, 0) / n;
  const variance = monthlyReturns.reduce((a, r) => a + (r - mean) ** 2, 0) / (n - 1);
  const annVol = Math.sqrt(variance) * Math.sqrt(12);
  let peak = values[0], maxDD = 0;
  for (let i = 1; i < values.length; i++) {
    if (values[i] > peak) peak = values[i];
    const dd = (peak - values[i]) / peak;
    if (dd > maxDD) maxDD = dd;
  }
  const tbillEnd = DATA[DATA.length - 1].tbills;
  const tbillStart = DATA[0].tbills;
  const annTbill = Math.pow(tbillEnd / tbillStart, 12 / n) - 1;
  const sharpe = (annReturn - annTbill) / annVol;
  return { annReturn, annVol, maxDD, sharpe, monthlyReturns, annTbill };
}

function computeTrackingError(fixedReturns, stackedReturns) {
  const diffs = [];
  for (let i = 0; i < fixedReturns.length; i++) {
    diffs.push(stackedReturns[i] - fixedReturns[i]);
  }
  const mean = diffs.reduce((a, b) => a + b, 0) / diffs.length;
  const variance = diffs.reduce((a, d) => a + (d - mean) ** 2, 0) / (diffs.length - 1);
  return Math.sqrt(variance) * Math.sqrt(12);
}

const { fixedValues, stackedValues } = compute();
const fixedStats = computeStats(fixedValues);
const stackedStats = computeStats(stackedValues);
const te = computeTrackingError(fixedStats.monthlyReturns, stackedStats.monthlyReturns);

console.log("Final Stock/Bond level :", fixedValues[fixedValues.length - 1].toFixed(4));
console.log("Final Stacked   level :", stackedValues[stackedValues.length - 1].toFixed(4));
console.log("Annualized RFR (geom) :", (fixedStats.annTbill * 100).toFixed(4) + "%");
console.log();
console.log("Metric                Stock/Bond     Stacked     Difference");
console.log("Annualized Return    ", (fixedStats.annReturn * 100).toFixed(2) + "%   ",
            (stackedStats.annReturn * 100).toFixed(2) + "%   ",
            ((stackedStats.annReturn - fixedStats.annReturn) * 100).toFixed(2) + "%");
console.log("Annualized Vol       ", (fixedStats.annVol * 100).toFixed(2) + "%   ",
            (stackedStats.annVol * 100).toFixed(2) + "%   ",
            ((stackedStats.annVol - fixedStats.annVol) * 100).toFixed(2) + "%");
console.log("Maximum Drawdown     ", (fixedStats.maxDD * 100).toFixed(2) + "%   ",
            (stackedStats.maxDD * 100).toFixed(2) + "%   ",
            ((stackedStats.maxDD - fixedStats.maxDD) * 100).toFixed(2) + "%");
console.log("Sharpe Ratio         ", fixedStats.sharpe.toFixed(2) + "       ",
            stackedStats.sharpe.toFixed(2) + "       ",
            (stackedStats.sharpe - fixedStats.sharpe).toFixed(2));
console.log("Tracking Error                          ", (te * 100).toFixed(2) + "%");
