const { paper } = require('paper-jsdom-canvas');
const fs = require('fs');
const { StakePoolPerformanceChart } = require('./static/js/StakePoolPerformanceChart.js')

function saveCanvasToSVGFile() {
    var svg = paper.project.exportSVG({asString:true});
    fs.writeFileSync('/var/www/html/test/test.svg', svg);
}

function draw_solid_rectangle(x, y, width, height, color, blockRounding) {
    var rect = new paper.Rectangle([x, y], [width, height]);
    var path = new paper.Path.Rectangle(rect, blockRounding);
    path.fillColor = color;
    return path;
}


var data_url = 'http://cardaviz.spklpool.com/data/' + process.argv[2] + '.json';
var chart = null;
var global_data = null;
var data_fetch_completed = false;
var first_drawing_complete = false;

console.log('fetching data from ' + data_url);
fetch(data_url).then(function (response) {
	return response.json();
}).then(function (data) {
	console.log('data fetch completed');
	global_data = data;
	data_fetch_completed = true;
}).catch(function (err) {
	console.log('error: ' + err);
});

setTimeout(draw_if_data_finished_loading, 100);

function draw_if_data_finished_loading() {
	if (data_fetch_completed) {
		console.log('drawing');
		chart = new StakePoolPerformanceChart(null, paper, global_data, null);
		chart.setupPaper();
		chart.draw(false);
		first_drawing_complete = true;
		console.log('drawing complete');
                saveCanvasToSVGFile();
	} else {
		setTimeout(draw_if_data_finished_loading, 100);
	}
}

