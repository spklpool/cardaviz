class StakePoolPerformanceChart {
    canvas = null;
    paper = null;
    data = null;
    watermark_enabled = true;
    drawing_epoch_numbers = true;
    drawing_ticker = false;
    document = null;
    background_color = '#101010'
    separator_line_color = '#282828';
    current_epoch_color = '#282828';
    actual_block_color = '#D3D3D3';
    expected_block_color = 'blue';
    blockRounding = 3;
    block_to_epoch_width_margin = 4;
    epochWidth = 30;
    blockWidth = 0;
    block_height = 0;
    epoch_text_offset = 15;
    epoch_text_vertical_offset = 30;
    epoch_offset = 0;

    constructor(canvas, paper, data, document, thumbnail_mode) {
        this.canvas = canvas;
        this.paper = paper;
        this.data = data;
        this.document = document;
        if (thumbnail_mode) {
            this.watermark_enabled = false;
            this.drawing_epoch_numbers = false;
            this.drawing_ticker = true;
            this.epochWidth = this.paper.view.size.width / this.data['epochs'].length
            this.stroke_width = 1;
        } else {
            this.epochWidth = 30;
            this.watermark_enabled = false;
            this.stroke_width = 5;
        }

        this.canvas_required_width = data["epochs"].length * this.epochWidth;
        if (!this.canvas) {
            this.setupPaper();
        }
        this.block_height = (this.paper.view.size.height / 2) / (this.data.max_epoch_blocks + 1);
        this.blockWidth = this.epochWidth - this.block_to_epoch_width_margin;
    }

    setupPaper() {
        var size = new this.paper.Size(this.canvas_required_width, 1200)
        this.paper.setup(size);
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

    draw_translucent_rectangle(width, height, strokeColor, fillColor, opacity, blockRounding) {
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
        path.strokeWidth = 1
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
        if (this.watermark_enabled) {
            var watermark_current_x = this.paper.view.size.width;
            var watermark_current_y = this.paper.view.size.height;
            while (watermark_current_x > 0) {
                var watermark_text = this.draw_text(watermark_current_x, watermark_current_y, 'cardaviz.app', 310, 48, '#181818');
                watermark_current_x -= watermark_text.bounds.width * 0.6;
                watermark_current_y -= watermark_text.bounds.height * 0.8;
                if (watermark_current_y <= 0) {
                    watermark_current_y = this.paper.view.size.height;
                }
            }
        }
    }

    start_cumulative_path() {
        var cumulativeDiffPath = new this.paper.Path();
        cumulativeDiffPath.strokeColor = 'yellow';
        cumulativeDiffPath.strokeWidth = this.stroke_width;
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

    draw(resize_enabled) {
        if (this.document && this.canvas && resize_enabled) {
            if (this.canvas_required_width > this.document.documentElement.clientWidth) {
                this.document.body.style.width = this.canvas_required_width + 'px';
                this.document.documentElement.scrollLeft = this.canvas_required_width - this.document.documentElement.clientWidth;
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
        if (this.drawing_ticker) {
            var gap = view_size.height / 2;
            var ticker_text = this.draw_text(0, 0, this.data['ticker'], 0, 18, 'white');
            ticker_text.position = new Point((gap * 4) + (ticker_text.bounds.width / 2), 25);
            var epochs_text = this.draw_text(0, 0, this.data['epochs'].length + ' epochs', 0, 18, 'white');
            epochs_text.position = new Point((gap * 4) + (epochs_text.bounds.width / 2), 50);
            var luck_text = this.draw_text(0, 0, '💪 ' + this.data['current_lifetime_luck'].toFixed(2) + '%', 0, 18, 'white');
            luck_text.position = new Point((gap * 4) + (luck_text.bounds.width / 2), 75);
            var luck_text2 = this.draw_text(0, 0, 'diff ' + this.data['cumulative_diff'].toFixed(2), 0, 18, 'white');
            luck_text2.position = new Point((gap * 4) + (luck_text2.bounds.width / 2), 100);
            var luck_text3 = this.draw_text(0, 0, 'stake ' + (this.data['epochs'][this.data['epochs'].length - 1]['pool_stake'] / 1000000000).toFixed(2) + 'k', 0, 18, 'white');
            luck_text3.position = new Point((gap * 4) + (luck_text3.bounds.width / 2), 125);
        }
    }
}

if (typeof module !== 'undefined') {
    module.exports = { StakePoolPerformanceChart }
}
