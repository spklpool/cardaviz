class StakePoolPerformanceChart {
    canvas = null;
    paper = null;
    data = null;
    document = null;
    legend_initialized = false;
    background_color = 'black'
    separator_line_color = '#282828';
    current_epoch_color = '#282828';
    actual_block_color = '#D3D3D3';
    expected_block_color = 'blue';
    legend_width = 420;
    legend_height = 260;
    blockRounding = 3;
    block_to_epoch_width_margin = 4;
    epochWidth = 30;
    blockWidth = 0;
    block_height = 0;
    epoch_text_offset = 15;
    epoch_text_vertical_offset = 30;
    right_axis_legend_width = 120;
    epoch_offset = 0;

    // legend objects
    legend_path = null;
    ticker_text = null;
    legend_expected_block_text = null;
    legend_expected_rect = null;
    legend_expected_path = null;
    legend_actual_block_text = null;
    legend_performance_text = null;
    legend_cumulative_text = null;
    legend_highest_luck_text = null;
    legend_lowest_lifetime_luck_text = null;
    legend_current_lifetime_luck_text = null;
    legend_green_text = null;
    legend_red_text = null;
    legend_cumulative_path = null;
    legend_actual_path = null;
    legend_green_path = null;
    legend_red_path = null;

    constructor(canvas, paper, data, document) {
        this.canvas = canvas;
        this.paper = paper;
        this.data = data;
        this.document = document;
        this.blockWidth = this.epochWidth - this.block_to_epoch_width_margin;
        this.canvas_required_width = data["epochs"].length * this.epochWidth;
        if (!this.canvas) {
            this.setupPaper();
        }
        this.block_height = (this.paper.view.size.height / 2) / (this.data.max_epoch_blocks + 1);
    }

    setupPaper() {
        var size = new this.paper.Size(this.canvas_required_width + this.right_axis_legend_width, 1200)
        this.paper.setup(size);
    }

    resetLegend() {
        this.legend_path = null;
        this.ticker_text = null;
        this.legend_expected_block_text = null;
        this.legend_expected_rect = null;
        this.legend_expected_path = null;
        this.legend_actual_block_text = null;
        this.legend_performance_text = null;
        this.legend_cumulative_text = null;
        this.legend_highest_luck_text = null;
        this.legend_lowest_lifetime_luck_text = null;
        this.legend_current_lifetime_luck_text = null;
        this.legend_green_text = null;
        this.legend_red_text = null;
        this.legend_cumulative_path = null;
        this.legend_actual_path = null;
        this.legend_green_path = null;
        this.legend_red_path = null;
    }

    draw_background_solid_rectangle(x, y, width, height, color) {
        var rect = new this.paper.Path.Rectangle({
            point: [x, y],
            size: [width, height],
            strokeColor: color
        });
        rect.sendToBack();
        rect.fillColor = color;
    }

    draw_translucent_rectangle(x, y, width, height, strokeColor, fillColor, opacity, blockRounding) {
        var rect = new this.paper.Rectangle([0, 0], [width, height]);
        var path = new this.paper.Path.Rectangle(rect, blockRounding);
        path.strokeColor = strokeColor;
        path.fillColor = fillColor;
        path.opacity = opacity;
        return path;
    }

    draw_solid_rectangle(x, y, width, height, color, blockRounding) {
        var rect = new this.paper.Rectangle([x, y], [width, height]);
        var path = new this.paper.Path.Rectangle(rect, blockRounding);
        path.fillColor = color;
        return path;
    }

    draw_hollow_rectangle(x, y, width, height, color, blockRounding) {
        var rect = new this.paper.Rectangle([x, y], [width, height]);
        var path = new this.paper.Path.Rectangle(rect, blockRounding);
        path.strokeColor = color;
        path.strokeWidth = 2
        return path;
    }

    draw_line(start_x, start_y, end_x, end_y, color, strokeWidth) {
        var linePath = new this.paper.Path();
        linePath.strokeColor = color;
        linePath.add(new this.paper.Point(start_x, start_y));
        linePath.add(new this.paper.Point(end_x, end_y));
        linePath.strokeWidth = strokeWidth;
        return linePath;
    }

    draw_matrix_lines(number_of_epochs, height) {
        var watermark_current_x = this.paper.view.size.width;
        var watermark_current_y = this.paper.view.size.height;
        while (watermark_current_x > 0) {
            var watermark_text = this.draw_text(watermark_current_x, watermark_current_y, 'cardaviz.app', 310, 36, '#181818');
            watermark_current_x -= watermark_text.bounds.width / 2;
            watermark_current_y -= watermark_text.bounds.height / 2;
            if (watermark_current_y <= 0) {
                watermark_current_y = this.paper.view.size.height;
            }
        }
        for (var epoch = 0; epoch < number_of_epochs; epoch ++) {
            var line_x = this.epoch_offset + (this.epochWidth * epoch);
            this.draw_line(line_x, 0, line_x, height, this.separator_line_color, 2);
            if (epoch == (number_of_epochs - 1)) {
                var extra_line_x = this.epoch_offset + (this.epochWidth * (epoch + 1));
                this.draw_line(extra_line_x, 0, extra_line_x, height, this.separator_line_color, 2);
                this.draw_solid_rectangle(line_x, 1, this.epochWidth, height, this.current_epoch_color, 0);
            }
        }
        for (var current_height = 0; current_height < height; current_height += this.block_height) {
            this.draw_line(this.epoch_offset, current_height, this.epoch_offset + this.canvas_required_width, current_height, this.separator_line_color, 2);
        }
    }

    start_cumulative_path() {
        var cumulativeDiffPath = new this.paper.Path();
        cumulativeDiffPath.strokeColor = 'yellow';
        cumulativeDiffPath.strokeWidth = 5;
        return cumulativeDiffPath;
    }

    draw_text(x, y, text, rotation, fontSize, color) {
        return new this.paper.PointText({
            point: [x, y],
            content: text,
            style: {
                fontFamily: 'Courier New',
                fontWeight: 'bold',
                fontSize: fontSize,
                fillColor: color,
                justification: 'center'
            }
        }).rotate(rotation);
    }

    draw_epochs(diff_path, block_offset, blockHeight, cumulative_diff_scaling_factor) {
        var middle_y = this.paper.view.size.height / 2;
        for (var epoch = 0; epoch < this.data["epochs"].length; epoch++) {
            var epochBlockCount = parseFloat(this.data["epochs"][epoch].actual);
            var epochBlockExpected = parseFloat(this.data["epochs"][epoch].expected);
            var epochBlockDiff = epochBlockCount - epochBlockExpected;

            var epochX = this.epoch_offset + (epoch * this.epochWidth);
            this.draw_text(epochX + this.epoch_text_offset, this.paper.view.size.height - this.epoch_text_vertical_offset, this.data["epochs"][epoch].epoch, 310, 16, 'white');

            // blocks - actual and expected
            for (var epochBlock = 0; epochBlock < epochBlockCount; epochBlock++) {
                this.draw_solid_rectangle(epochX + block_offset, middle_y - ((epochBlock + 1) * blockHeight), this.blockWidth, blockHeight, this.actual_block_color, this.blockRounding)
            }
            this.draw_hollow_rectangle(epochX + block_offset, middle_y - (epochBlockExpected * blockHeight), this.blockWidth, epochBlockExpected * blockHeight, this.expected_block_color, this.blockRounding);

            if (epoch < this.data["epochs"].length - 1) {
                // performance diff lines
                var diffPath = new this.paper.Path();
                if (epochBlockDiff > 0) {
                    diffPath.strokeColor = 'green';
                } else {
                    diffPath.strokeColor = 'red';
                }
                diffPath.strokeWidth = 5;
                diffPath.add(new this.paper.Point(epochX, middle_y - (epochBlockDiff * blockHeight)));
                diffPath.add(new this.paper.Point(epochX + this.epochWidth, middle_y - (epochBlockDiff * blockHeight)));

                // cumulative performance line
                diff_path.add(new this.paper.Point(epochX + 14, middle_y - (cumulative_diff_scaling_factor * (this.data['epochs'][epoch]['epoch_cumulative_diff'] * blockHeight))));
                diff_path.add(new this.paper.Point(epochX + 16, middle_y - (cumulative_diff_scaling_factor * (this.data['epochs'][epoch]['epoch_cumulative_diff'] * blockHeight))));

                // make cumulative line prettier
                diff_path.smooth({ type: 'catmull-rom', factor: 1.0 });
                diff_path.bringToFront();
            }
        }
    }

    // Draws the axis on the right for the cumulative performance yellow line.
    // the values are scaled so that the cumulative performance line takes up the entire height so the values on the axis are
    // scaled accordingly.  Also, depending on how many blocks a pool produces, the height of a block also scales.
    drawRightAxisLuckBar(max_epoch_blocks, total_height, blockHeight, max_cumulative_diff, total_expected_blocks, canvasRequiredWidth) {
        var desired_number_of_axis_text = 6;
        var axis_text_count = 2;
        if (max_epoch_blocks > desired_number_of_axis_text) {
            axis_text_count = Math.ceil(max_epoch_blocks / desired_number_of_axis_text);
        }
        var skip_text_count = 0;
        for (var height = 0; height <= total_height; height += blockHeight) {
            skip_text_count ++;
            if (height > 0 && skip_text_count == axis_text_count) {
                skip_text_count = 0;
                var right_axis_path = new this.paper.Path();
                right_axis_path.strokeColor = 'yellow';
                right_axis_path.add(new this.paper.Point(this.epoch_offset + canvasRequiredWidth, height));
                right_axis_path.add(new this.paper.Point(this.epoch_offset + canvasRequiredWidth + 20, height));
                right_axis_path.strokeWidth = 5;
                var axis_content = '';
                if (height == (total_height / 2)) {
                    axis_content = "100%";
                } else if (height > (total_height / 2)) {
                    var current_axis_diff = ((height - (total_height / 2)) / blockHeight)/((total_height / 2) / blockHeight) * (max_cumulative_diff / total_expected_blocks)
                    axis_content = ((1 - current_axis_diff) * 100).toFixed(2) + "%";
                } else {
                    var current_axis_diff = (((total_height / 2) - height) / blockHeight)/((total_height / 2) / blockHeight) * (max_cumulative_diff / total_expected_blocks)
                    axis_content = ((1 + current_axis_diff) * 100).toFixed(2) + "%";
                }
                this.draw_text(this.epoch_offset + canvasRequiredWidth + 75, height + 3, axis_content, 0, 18, 'yellow')
            }
        }
    }

    // draws a legend in a semi transparent box.
    // all objects are originally drawn at 0,0 and then repositioned to where they should be
    // this is to make them fall in the same position later when we reposition them again when scrolling
    drawLegend(legend_x, legend_y, highest_lifetime_luck, lowest_lifetime_luck, current_lifetime_luck, ticker) {
        console.log('drawing legend [' + legend_x + ',' + legend_y + ']');
        if (!this.legend_initialized) {
            this.legend_path = this.draw_translucent_rectangle(0, 0, this.legend_width, this.legend_height, '#D3D3D3', 'black', 0.9, 20);
            this.ticker_text = this.draw_text(0, 0, "ticker: " + ticker, 0, 18, '#D3D3D3');
            this.legend_expected_block_text = this.draw_text(0, 0, ': expected blocks', 0, 18, 'blue');
            this.legend_expected_path = this.draw_hollow_rectangle(0, 0, this.blockWidth, 13, 'blue', this.blockRounding);
            this.legend_actual_block_text = this.draw_text(0, 0, ': actual blocks ', 0, 18, '#D3D3D3');
            this.legend_actual_path = this.draw_solid_rectangle(0, 0, this.blockWidth, 13, '#D3D3D3', this.blockRounding);
            this.legend_green_path = this.draw_line(0, 0, 29, 0, 'green', 5);
            this.legend_red_path = this.draw_line(0, 0, 29, 0, 'red', 5);
            this.legend_performance_text = this.draw_text(0, 0, ': epoch performance', 0, 18, 'yellow');
            this.legend_green_text = this.draw_text(0, 0, ' over', 0, 18, 'green');
            this.legend_red_text = this.draw_text(0, 0, ' under', 0, 18, 'red');
            this.legend_cumulative_text = this.draw_text(0, 0, ': cumulative performance', 0, 18, 'yellow');
            this.legend_highest_luck_text = this.draw_text(0, 0, 'highest performance : ' + highest_lifetime_luck.toFixed(2) + '%', 0, 18, 'yellow');
            this.legend_lowest_luck_text = this.draw_text(0, 0, 'lowest performance  : ' + lowest_lifetime_luck.toFixed(2) + '%', 0, 18, 'yellow');
            this.legend_current_lifetime_luck_text = this.draw_text(0, 0, 'current performance : ' + current_lifetime_luck.toFixed(2) + '%', 0, 18, 'yellow');
            this.legend_initialized = true;
        }
        this.legend_path.position = new Point(legend_x + 220, legend_y + this.legend_height / 2);
        this.ticker_text.position = new Point(legend_x + 95, legend_y + 25);
        this.legend_expected_block_text.position = new Point(legend_x + 152.3, legend_y + 55);
        this.legend_expected_path.position = new Point(legend_x + 40.5, legend_y + 55.5);
        this.legend_actual_block_text.position = new Point(legend_x + 147, legend_y + 85);
        this.legend_actual_path.position = new Point(legend_x + 40.5, legend_y + 85);
        this.legend_green_path.position = new Point(legend_x + 40, legend_y + 110);
        this.legend_red_path.position = new Point(legend_x + 40, legend_y + 120);

        if (this.legend_cumulative_path == null) {
            this.legend_cumulative_path = new this.paper.Path();
            this.legend_cumulative_path.strokeColor = 'yellow';
            this.legend_cumulative_path.strokeWidth = 5;
            this.legend_cumulative_path.add(0, 0);
            this.legend_cumulative_path.add(29, 0);
        }
        this.legend_cumulative_path.position = new Point(legend_x + 40, legend_y + 149);
        this.legend_performance_text.position = new Point(legend_x + 163.2, legend_y + 115);
        this.legend_green_text.position = new Point(legend_x + 290, legend_y + 115);
        this.legend_red_text.position = new Point(legend_x + 350, legend_y + 115);
        this.legend_cumulative_text.position = new Point(legend_x + 60 + (this.legend_cumulative_text.bounds.width / 2), legend_y + 148);
        this.legend_highest_luck_text.position = new Point(legend_x + 84 + (this.legend_highest_luck_text.bounds.width / 2), legend_y + 181.5);
        this.legend_lowest_luck_text.position = new Point(legend_x + 84 + (this.legend_lowest_luck_text.bounds.width / 2), legend_y + 209.5);
        this.legend_current_lifetime_luck_text.position = new Point(legend_x + 84 + (this.legend_current_lifetime_luck_text.bounds.width / 2), legend_y + 236.5);
    }


    draw(drawLegend) {
        if (this.document && this.canvas) {
            console.log('setting up canvas');
            if (this.canvas_required_width > this.document.documentElement.clientWidth) {
                this.document.body.style.width = this.canvas_required_width + this.right_axis_legend_width + 'px';
                this.document.documentElement.scrollLeft = this.canvas_required_width - this.document.documentElement.clientWidth + this.right_axis_legend_width;
            } else {
                this.document.body.style.width = document.documentElement.clientWidth;
                var epochs_to_offset = (document.documentElement.clientWidth - this.canvas_required_width) / this.epochWidth
                this.epoch_offset = Math.ceil(epochs_to_offset) * this.blockWidth;
            }
            this.paper.setup(this.canvas);
        }
        var view_size = this.paper.view.size;
        this.draw_background_solid_rectangle(0, 0, view_size.width, view_size.height, this.background_color);
        this.draw_matrix_lines(this.data["epochs"].length, view_size.height);
        var max_cumulative_diff_adjustment_buffer = 0.1;
        this.draw_epochs(this.start_cumulative_path(), this.block_to_epoch_width_margin / 2, this.block_height, (view_size.height / 2) / ((this.data.max_cumulative_diff + max_cumulative_diff_adjustment_buffer) * this.block_height));
        this.drawRightAxisLuckBar(this.data.max_epoch_blocks, view_size.height, this.block_height, this.data.max_cumulative_diff, this.data.cumulative_expected_blocks, this.canvas_required_width);
        if (drawLegend) {
            this.drawLegend(this.document.documentElement.scrollLeft, (view_size.height / 2) + 30, this.data['highest_lifetime_luck'], this.data['lowest_lifetime_luck'], this.data['current_lifetime_luck'], this.data["ticker"]);
        }
    }
}

if (typeof module !== 'undefined') {
    module.exports = { StakePoolPerformanceChart }
}