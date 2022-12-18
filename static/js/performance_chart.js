import {StakePoolPerformanceChart} from './StakePoolPerformanceChart.js';

var chart = null;
var global_data = null;
var data_fetch_completed = false;
var first_drawing_complete = false;

console.log('fetching data from ' + data_url);
fetch(data_url)
.then(function (response) {
    return response.json();
})
.then(function (data) {
    console.log('data fetch completed');
    global_data = data;
    data_fetch_completed = true;
})
.catch(function (err) {
    console.log('error: ' + err);
});

window.onload = function() {
    setTimeout(draw_if_data_finished_loading, 100);
}

document.addEventListener('scroll', function(event) {
    console.log('scroll, scroll, scroll...');
    if (first_drawing_complete) {
        chart.drawLegend(document.documentElement.scrollLeft, (paper.view.size.height / 2) + 30, global_data['highest_lifetime_luck'], global_data['lowest_lifetime_luck'], global_data['current_lifetime_luck'], global_data["ticker"]);
    }
});

window.addEventListener("resize", (event) => {
    console.log('resize, resize, resize...');
    if (first_drawing_complete) {
        chart.resetLegend();
        draw_if_data_finished_loading();
    }
}, true);

document.addEventListener('readystatechange', (event) => {
    if (document.readyState === "complete") {
        scroll_if_first_drawing_complete();
    }
});


function scroll_if_first_drawing_complete() {
    if (first_drawing_complete) {
        console.log("scrolling to current epoch");
    } else {
        setTimeout(scroll_if_first_drawing_complete, 100);
    }
}

function draw_if_data_finished_loading() {
    if (data_fetch_completed) {
        paper.install(window);
        var canvas = document.getElementById('myCanvas');
        paper.setup(canvas);
        chart = new StakePoolPerformanceChart(canvas, paper, global_data, document);
        chart.draw(true);
        first_drawing_complete = true;
    } else {
        setTimeout(draw_if_data_finished_loading, 100);
    }
}
