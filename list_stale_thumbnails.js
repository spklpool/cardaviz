const { paper } = require('paper-jsdom-canvas');
const fs = require('fs');
const { StakePoolPerformanceChart } = require('./static/js/StakePoolPerformanceChart.js')
const sharp = require('sharp')
const path = require('path');
const child_process = require('child_process');

async function process_stale_pools() {
  var pool_json_folder_path = '/var/www/html/data/';
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
        console.log('stale: ' + pool);
      } 
  }
}

process_stale_pools();

