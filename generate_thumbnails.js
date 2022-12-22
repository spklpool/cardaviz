const { paper } = require('paper-jsdom-canvas');
const fs = require('fs');
const { StakePoolPerformanceChart } = require('./static/js/StakePoolPerformanceChart.js')
const sharp = require('sharp')
const path = require('path');
const child_process = require('child_process');

async function convertSVGToPng(source_svg, destination_png) {
  await sharp(source_svg).png().toFile(destination_png)
}

function saveCanvasToSVGFile(destination_file) {
    var svg = paper.project.exportSVG({asString:true});
    fs.writeFileSync(destination_file, svg);
}

function process_pool(file_path) {
    var destination_directory = '/var/www/html/images/';
    var data = fs.readFileSync(file_path, 'utf8');
    var pool = path.parse(file_path).name;
    console.log('drawing ' + pool);
    var chart = new StakePoolPerformanceChart(null, paper, JSON.parse(data), null);
    chart.setupPaper();
    chart.draw(false);
    saveCanvasToSVGFile(destination_directory + pool + '.svg');
    convertSVGToPng(destination_directory + pool + '.svg', destination_directory + pool + '.png');
    console.log('done saving files for ' + pool);
    paper.project.clear();

    try {
      if (global.gc) {global.gc();}
    } catch (e) {
      console.log("gc not available.  try running with --expose-gc `");
    }
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function process_pools() {
  var pool_json_folder_path = '/var/www/html/data/';
  var processes_running = 0;
  while(true) {
    if (processes_running > 0) {
      console.log('processes running - sleeping for 10 seconds');
      await sleep(10000);
    } else {
      console.log('no processes running - starting to process all files in ' + pool_json_folder_path);
      var skipped_for_running = 0;
      const dir = fs.opendirSync(pool_json_folder_path)
      let dirent
      while ((dirent = dir.readSync()) !== null) {
        var pool_thumbnail_needs_updating = false;
        var pool = path.parse(dirent.name).name;
        var jsonstats = fs.statSync('/var/www/html/data/' + pool + '.json');
        var jsonmtime = jsonstats.mtime;
        var jsondate = Date.parse(jsonmtime);
        if (!fs.existsSync('/var/www/html/images/' + pool + '.png')) {
          pool_thumbnail_needs_updating = true;
        } else {
          var pngstats = fs.statSync('/var/www/html/images/' + pool + '.png');
          var pngmtime = pngstats.mtime;
          var pngdate = Date.parse(pngmtime);
          if ((jsondate - pngdate) > 0) {
            pool_thumbnail_needs_updating = true;
          }
        }
        if (pool_thumbnail_needs_updating) {
          if (processes_running > 10) {
            console.log('sleeping for 20 seconds to give processes time to complete');
            await sleep(20000);
          }
          console.log('json: ' + jsonmtime);
          console.log('png: ' + pngmtime);
          console.log('stale: ' + pool);
          processes_running += 1;
          var process_command = 'node ' + process.cwd() + '/generate_thumbnails.js ' + pool;
          console.log('running in separate process: ' + process_command);
          spawned_process = child_process.spawn('node', [process.cwd() + '/generate_thumbnails.js', pool]);
          spawned_process.stdout.on('data', function (data) {
            console.log('stdout: ' + data.toString());
          });
          spawned_process.stderr.on('data', function (data) {
            console.log('stderr: ' + data.toString());
          });
          spawned_process.on('exit', function (code) {
            console.log('child process exited with code ' + code.toString());
            processes_running -= 1;
          });
        }
      }
    }
  }
}

if (process.argv.length > 2) {
  process_pool('/var/www/html/data/' + process.argv[2] + '.json');
} else {
    process_pools();
}

