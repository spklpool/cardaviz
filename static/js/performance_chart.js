
var middleY = 300;
var canvasRequiredWidth = 0;
var legend_y = middleY + 30;
var legend_width = 420;
var legend_height = 260;
var blockRounding = 3;
var block_to_epoch_width_margin = 4;
var epochWidth = 30;
var blockWidth = epochWidth - block_to_epoch_width_margin;
var global_data = null;
var calculated_current_lifetime_luck = 0;
var first_drawing = true;
var scrolling_changed = false;
var data_fetch_completed = false;
var global_data = null;
var first_drawing_complete = false;
var textHeight = 35;
var textWidth = 15;
var epoch_text_offset = 15;
var epoch_text_vertical_offset = 30;

// legend objects
var legend_path = null;
var ticker_text = null;
var legend_expected_block_text = null;
var legend_expected_rect = null;
var legend_expected_path = null;
var legend_actual_block_text = null;
var legend_performance_text = null;
var legend_cumulative_text = null;
var legend_highest_luck_text = null;
var legend_lowest_lifetime_luck_text = null;
var legend_current_lifetime_luck_text = null;
var legend_green_text = null;
var legend_red_text = null;
var legend_cumulative_path = null;
var legend_actual_path = null;
var legend_green_path = null;
var legend_red_path = null;

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

paper.install(window);

window.onload = function() {
    var canvas = document.getElementById('myCanvas');
    paper.setup(canvas);
    draw_black_background
    setTimeout(draw_if_data_finished_loading, 100);
}

document.addEventListener("scroll", (event) => {
    console.log('scroll, scroll, scroll...');
    scrolling_changed = true;
    if (first_drawing_complete) {
        drawLegend(document.documentElement.scrollLeft, legend_y);
    }
});

document.addEventListener('readystatechange', (event) => {
    if (document.readyState === "complete") {
        scroll_if_first_drawing_complete();
    }
});

function scroll_if_first_drawing_complete() {
    if (first_drawing_complete) {
        console.log("scrolling to current epoch");
        document.documentElement.scrollLeft = canvasRequiredWidth - document.documentElement.clientWidth + 100;
    } else {
        setTimeout(scroll_if_first_drawing_complete, 100);
    }
}

function draw_if_data_finished_loading() {
    if (data_fetch_completed) {
        drawPoolPerformanceChart(global_data);
        first_drawing_complete = true;
    } else {
        setTimeout(draw_if_data_finished_loading, 100);
    }
}

function draw_black_background() {
    var rect = new paper.Path.Rectangle({
        point: [0, 0],
        size: [paper.view.size.width, paper.view.size.height],
        strokeColor: 'black',
        selected: true
    });
    rect.sendToBack();
    rect.fillColor = 'black';
}

function draw_epoch_separator_lines(number_of_epochs) {
    for (epoch = 0; epoch < number_of_epochs; epoch ++) {

        // epoch separation lines
        var epochSeparatorPath = new paper.Path();
        epochSeparatorPath.strokeColor = '#282828';
        epochSeparatorPath.add(new paper.Point(epochWidth * epoch, 0));
        epochSeparatorPath.add(new paper.Point(epochWidth * epoch, middleY * 2));

        // add an extra line at the end to make it pretty
        if (epoch == (number_of_epochs - 1)) {
            var lastEpochSeparatorPath = new paper.Path();
            lastEpochSeparatorPath.strokeColor = '#282828';
            lastEpochSeparatorPath.add(new paper.Point(epochWidth * (epoch + 1), 0));
            lastEpochSeparatorPath.add(new paper.Point(epochWidth * (epoch + 1), middleY * 2));

            // grey rectangle for last epoc to indicate it is still under way
            var last_epoch_rect = new paper.Rectangle([epochWidth * epoch, 1], [epochWidth, middleY * 2]);
            var last_epoch_path = new paper.Path.Rectangle(last_epoch_rect, blockRounding);
            last_epoch_path.fillColor = '#282828';
        }
    }
}

function draw_block_separator_lines(block_height) {
    for (height = 0; height < (middleY * 2); height += block_height) {
        var block_separator_path = new paper.Path();
        block_separator_path.strokeColor = '#282828';
        block_separator_path.add(new paper.Point(0, height));
        block_separator_path.add(new paper.Point(canvasRequiredWidth, height));
    }
}

function draw_epochs(pool_data, diff_path, block_offset, block_height, cumulative_diff_scaling_factor) {
    for (var epoch = 0; epoch < pool_data["epochs"].length; epoch++) {
        var epochBlockCount = parseFloat(pool_data["epochs"][epoch].actual);
        var epochBlockExpected = parseFloat(pool_data["epochs"][epoch].expected);
        var epochBlockDiff = epochBlockCount - epochBlockExpected;

        var epochX = epoch * epochWidth;
        var epochText = new paper.PointText({
            point: [epochX + epoch_text_offset, (middleY * 2) + epoch_text_vertical_offset],
            content: pool_data["epochs"][epoch].epoch,
            style: {
                fontFamily: 'Courier New',
                fontWeight: 'bold',
                fontSize: 16,
                fillColor: 'white',
                justification: 'center'
            }
        }).rotate(310);

        for (var epochBlock = 0; epochBlock < epochBlockCount; epochBlock++) {
            var rect = new paper.Rectangle([epochX + block_offset, middleY - ((epochBlock + 1) * block_height)], [blockWidth, block_height]);
            var path = new paper.Path.Rectangle(rect, blockRounding);
            path.fillColor = '#D3D3D3';
        }

        var expected_rect = new paper.Rectangle([epochX + block_offset, middleY - (epochBlockExpected * block_height)], [blockWidth, epochBlockExpected * block_height]);
        var expected_path = new paper.Path.Rectangle(expected_rect, blockRounding);
        expected_path.strokeColor = 'blue';
        expected_path.strokeWidth = 2;

        if (epoch < pool_data["epochs"].length - 1) {
            var diffPath = new paper.Path();
            if (epochBlockDiff > 0) {
                diffPath.strokeColor = 'green';
            } else {
                diffPath.strokeColor = 'red';
            }
            diffPath.strokeWidth = 5;
            diffPath.add(new paper.Point(epochX, middleY - (epochBlockDiff * block_height)));
            diffPath.add(new paper.Point(epochX + epochWidth, middleY - (epochBlockDiff * block_height)));

            diff_path.add(new paper.Point((epochWidth * epoch) + 14, middleY - (cumulative_diff_scaling_factor * (pool_data['epochs'][epoch]['epoch_cumulative_diff'] * block_height))));
            diff_path.add(new paper.Point((epochWidth * epoch) + 16, middleY - (cumulative_diff_scaling_factor * (pool_data['epochs'][epoch]['epoch_cumulative_diff'] * block_height))));

            diff_path.smooth({ type: 'catmull-rom', factor: 1.0 });
            diff_path.bringToFront();
        }
    }
}

function start_cumulative_path() {
    var cumulativeDiffPath = new paper.Path();
    cumulativeDiffPath.strokeColor = 'yellow';
    cumulativeDiffPath.strokeWidth = 5;
    return cumulativeDiffPath;
}

function drawPoolPerformanceChart(data) {
    var max_cumulative_diff_adjustment_buffer = 0.1;
    var blockHeight = middleY / (data.max_epoch_blocks + 1);
    draw_black_background();
    draw_epoch_separator_lines(data["epochs"].length);
    canvasRequiredWidth = data["epochs"].length * epochWidth;
    draw_block_separator_lines(blockHeight);
    draw_epochs(data, start_cumulative_path(), block_to_epoch_width_margin / 2, blockHeight, middleY / ((data.max_cumulative_diff + max_cumulative_diff_adjustment_buffer) * blockHeight));
    drawRightAxisLuckBar(data.max_epoch_blocks, middleY, blockHeight, data.max_cumulative_diff, data.cumulative_expected_blocks, canvasRequiredWidth);
    drawLegend(document.documentElement.scrollLeft, legend_y, data['highest_lifetime_luck'], data['lowest_lifetime_luck'], data['current_lifetime_luck'], data["ticker"])
}

function drawRightAxisLuckBar(max_epoch_blocks, middleY, block_height, max_cumulative_diff, total_expected_blocks, canvasRequiredWidth) {
    var desired_number_of_axis_text = 6;
    var axis_text_count = 2;
    if (max_epoch_blocks > desired_number_of_axis_text) {
        axis_text_count = Math.ceil(max_epoch_blocks / desired_number_of_axis_text);
    }
    var skip_text_count = 0;
    for (height = 0; height <= (middleY * 2); height += block_height) {
        skip_text_count ++;
        if (height > 0 && skip_text_count == axis_text_count) {
            skip_text_count = 0;
            var right_axis_path = new paper.Path();
            right_axis_path.strokeColor = 'yellow';
            right_axis_path.add(new paper.Point(canvasRequiredWidth, height));
            right_axis_path.add(new paper.Point(canvasRequiredWidth + 20, height));
            right_axis_path.strokeWidth = 5;

            if (height == middleY) {
                axis_content = "100%";
            } else if (height > middleY) {
                current_axis_diff = ((height - middleY) / block_height)/(middleY / block_height) * (max_cumulative_diff / total_expected_blocks)
                axis_content = ((1 - current_axis_diff) * 100).toFixed(2) + "%";
            } else {
                current_axis_diff = ((middleY - height) / block_height)/(middleY / block_height) * (max_cumulative_diff / total_expected_blocks)
                axis_content = ((1 + current_axis_diff) * 100).toFixed(2) + "%";
            }
            var axis_text = new paper.PointText({
            point: [canvasRequiredWidth + 25, height + 3],
            content: axis_content,
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'yellow',
                justification: 'left'
            }
            })
        }
    }
}

function drawLegend(legend_x, legend_y, highest_lifetime_luck, lowest_lifetime_luck, current_lifetime_luck, ticker) {
    if (legend_path == null) {
        var legend_rect = new paper.Rectangle([legend_x, legend_y], [legend_width, legend_height]);
        legend_path = new paper.Path.Rectangle(legend_rect, blockRounding);
        legend_path.strokeColor = '#D3D3D3';
        legend_path.fillColor = 'black';
        legend_path.opacity = 0.9;
    }
    legend_path.position = new Point(legend_x + 220, legend_y + legend_height / 2);

    if (ticker_text == null) {
        ticker_text = new paper.PointText({
            point: [legend_x + 20, legend_y + 30],
            content: "ticker: " + ticker,
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: '#D3D3D3',
                justification: 'left'
            }
        })
    }
    ticker_text.position = new Point(legend_x + 95, legend_y + 25);

    if (legend_expected_block_text == null) {
        legend_expected_block_text = new paper.PointText({
            point: [legend_x + 50, legend_y + 60],
            content: ': expected blocks',
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'blue',
                justification: 'left'
            }
        })
    }
    legend_expected_block_text.position = new Point(legend_x + 152.3, legend_y + 55);

    if (legend_expected_path == null) {
        var legend_expected_rect = new paper.Rectangle([legend_x + 15, legend_y + 49], [blockWidth, 13]);
        legend_expected_path = new paper.Path.Rectangle(legend_expected_rect, blockRounding);
        legend_expected_path.strokeColor = 'blue';
        legend_expected_path.strokeWidth = 2;
    }
    legend_expected_path.position = new Point(legend_x + 40.5, legend_y + 55.5);


    if (legend_actual_block_text == null) {
        legend_actual_block_text = new paper.PointText({
            point: [legend_x + 50, legend_y + 90],
            content: ': actual blocks ',
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: '#D3D3D3',
                justification: 'left'
            }
        })
    }
    legend_actual_block_text.position = new Point(legend_x + 147, legend_y + 85);

    if (legend_actual_path == null) {
        var legend_actual_rect = new paper.Rectangle([legend_x + 30, legend_y + 79], [blockWidth, 13]);
        legend_actual_path = new paper.Path.Rectangle(legend_actual_rect, blockRounding);
        legend_actual_path.fillColor = '#D3D3D3';
        legend_actual_path.strokeWidth = 2;
    }
    legend_actual_path.position = new Point(legend_x + 40.5, legend_y + 85);

    if (legend_green_path == null) {
        legend_green_path = new paper.Path();
        legend_green_path.strokeColor = 'green';
        legend_green_path.strokeWidth = 5;
        legend_green_path.add(legend_x + 30, legend_y + 110);
        legend_green_path.add(legend_x + 59, legend_y + 110);
    }
    legend_green_path.position = new Point(legend_x + 40, legend_y + 110);

    if (legend_red_path == null) {
        legend_red_path = new paper.Path();
        legend_red_path.strokeColor = 'red';
        legend_red_path.strokeWidth = 5;
        legend_red_path.add(legend_x + 30, legend_y + 120);
        legend_red_path.add(legend_x + 59, legend_y + 120);
    }
    legend_red_path.position = new Point(legend_x + 40, legend_y + 120);


    if (legend_cumulative_path == null) {
        legend_cumulative_path = new paper.Path();
        legend_cumulative_path.strokeColor = 'yellow';
        legend_cumulative_path.strokeWidth = 5;
        legend_cumulative_path.add(legend_x + 30, legend_y + 149);
        legend_cumulative_path.add(legend_x + 59, legend_y + 149);
    }
    legend_cumulative_path.position = new Point(legend_x + 40, legend_y + 149);

    if (legend_performance_text == null) {
        legend_performance_text = new paper.PointText({
            point: [legend_x + 50, legend_y + 120],
            content: ": epoch performance",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: '#D3D3D3',
                justification: 'left'
            }
        })
    }
    legend_performance_text.position = new Point(legend_x + 163.2, legend_y + 115);

    if (legend_green_text == null) {
        legend_green_text = new paper.PointText({
            point: [legend_x + 270, legend_y + 120],
            content: " over",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'green',
                justification: 'left'
            }
        })
    }
    legend_green_text.position = new Point(legend_x + 290, legend_y + 115);

    if (legend_red_text == null) {
        legend_red_text = new paper.PointText({
            point: [legend_x + 320, legend_y + 120],
            content: " under",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'red',
                justification: 'left'
            }
        })
    }
    legend_red_text.position = new Point(legend_x + 350, legend_y + 115);

    if (legend_cumulative_text == null) {
        legend_cumulative_text = new paper.PointText({
            point: [legend_x + 50, legend_y + 153],
            content: ": cumulative performance",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'yellow',
                justification: 'left'
            }
        })
    }
    legend_cumulative_text.position = new Point(legend_x + 190.2, legend_y + 148);

    if (legend_highest_luck_text == null) {
        legend_highest_luck_text = new paper.PointText({
            point: [legend_x + 70, legend_y + 187],
            content: 'highest performance : ' + highest_lifetime_luck.toFixed(2) + "%",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'yellow',
                justification: 'left'
            }
        })
    }
    legend_highest_luck_text.position = new Point(legend_x + 236.6, legend_y + 181.5);

    if (legend_lowest_lifetime_luck_text == null) {
        legend_lowest_lifetime_luck_text = new paper.PointText({
            point: [legend_x + 70, legend_y + 215],
            content: 'lowest performance  : ' + lowest_lifetime_luck.toFixed(2) + "%",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'yellow',
                justification: 'left'
            }
        })
    }
    legend_lowest_lifetime_luck_text.position = new Point(legend_x + 231.6, legend_y + 209.5);

    if (legend_current_lifetime_luck_text == null) {
        legend_current_lifetime_luck_text = new paper.PointText({
            point: [legend_x + 70, legend_y + 242],
            content: 'current performance : ' + current_lifetime_luck.toFixed(2) + "%",
            style: {
                fontFamily: 'Courier New',
                fontSize: 18,
                fillColor: 'yellow',
                justification: 'left'
            }
        })
    }
    legend_current_lifetime_luck_text.position = new Point(legend_x + 237, legend_y + 236.5);
}
