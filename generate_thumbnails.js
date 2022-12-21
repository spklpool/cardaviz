const { paper } = require('paper-jsdom-canvas');
const fs = require('fs');
const { StakePoolPerformanceChart } = require('./static/js/StakePoolPerformanceChart.js')
const sharp = require('sharp')
const path = require('path');
const exec_sync = require('child_process').execSync;

async function convertSVGToPng(pool) {
  await sharp('/var/www/html/test/' + pool + '.svg').png().toFile('/var/www/html/test/' + pool + '.png')
}

function saveCanvasToSVGFile(pool) {
    var svg = paper.project.exportSVG({asString:true});
    fs.writeFileSync('/var/www/html/test/' + pool + '.svg', svg);
}

function process_pool(file_path) {
    var data = fs.readFileSync(file_path, 'utf8');
    var pool = path.parse(file_path).name;
    console.log('drawing ' + pool);
    var chart = new StakePoolPerformanceChart(null, paper, JSON.parse(data), null);
    chart.setupPaper();
    chart.draw(false);
    saveCanvasToSVGFile(pool);
    convertSVGToPng(pool);
    paper.project.clear();

    try {
      if (global.gc) {global.gc();}
    } catch (e) {
      console.log("gc not available.  try running with --expose-gc `");
    }
}

if (process.argv.length > 2) {
  process_pool('/var/www/html/data/' + process.argv[2] + '.json');
} else {
  var pool_json_folder_path = '/var/www/html/data/';
  const dir = fs.opendirSync(pool_json_folder_path)
  let dirent
  while ((dirent = dir.readSync()) !== null) {
    var pool = path.parse(dirent.name).name;
    var jsonstats = fs.statSync('/var/www/html/data/' + pool + '.json');
    var jsonmtime = jsonstats.mtime;
    var jsondate = Date.parse(jsonmtime);
    if (!fs.existsSync('/var/www/html/test/' + pool + '.png')) {
      process_pool(pool_json_folder_path + dirent.name);
    }
    var pngstats = fs.statSync('/var/www/html/test/' + pool + '.png');
    var pngmtime = pngstats.mtime;
    var pngdate = Date.parse(pngmtime);
    if ((jsondate - pngdate) > 0) {
      console.log('json: ' + jsonmtime);
      console.log('png: ' + pngmtime);
      console.log('stale: ' + pool);
      exec_sync('node generate_thumbnails.js ' + pool);
    }
  }
  dir.closeSync();
}

