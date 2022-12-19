class SparklerLine {
    paper = null;
    view_size = null;
    x = 0;
    y = 0;
    progress = 0;
    length = 0;
    angle = 0;
    lifetime = 0;
    path = null;

    constructor(paper, x, y, progress, length, angle, lifetime) {
        this.paper = paper;
        this.view_size = this.paper.view.size;
        this.x = x;
        this.y = y;
        this.progress = progress;
        this.length = length;
        this.angle = angle;
        this.lifetime = lifetime;
        var start_x = x + this.progress * Math.cos(this.angle);
        var start_y = y + this.progress * Math.sin(this.angle);
        var end_x = start_x + this.length * Math.cos(this.angle);
        var end_y = start_y + this.length * Math.sin(this.angle);
        this.path = this.draw_sparkle_segment(start_x, start_y, end_x, end_y);
    }

    draw_sparkle_segment(start_x, start_y, end_x, end_y) {
        var linePath = new this.paper.Path();
        linePath.strokeColor = { gradient: {
            stops: [['white', 0.2], ['red', 0.25], ['yellow', 0.3], ['red', 0.35], ['white', 0.4]],
            radial: true
            },
            origin: new Point(start_x, start_y),
            destination: new Point(end_x, end_y)
        };
        linePath.add(new this.paper.Point(start_x, start_y));
        linePath.add(new this.paper.Point(end_x, end_y));
        linePath.strokeWidth = 3;
        return linePath;
    }

    is_alive() {
        return this.progress < this.lifetime;
    }

    move(value, fizzle) {
        this.progress += value;
        var start_x = (this.view_size.width / 2) + this.progress * Math.cos(this.angle);
        var start_y = fizzle + this.progress * Math.sin(this.angle);
        var end_x = start_x + this.length * Math.cos(this.angle);
        var end_y = start_y + this.length * Math.sin(this.angle);
        this.path.position = new Point(start_x, start_y, end_x, end_y);
        if ((this.lifetime - this.progress) > 0) {
            this.path.opacity = 1 - (this.progress / (this.lifetime - this.progress));
        }
    }
}

class Sparkler {
    canvas = null;
    paper = null;
    data = null;
    document = null;
    fizzle_x = 0;
    fizzle_y = 0;
    progress = 0;
    sparkler_lines = [];
    stick_path = null;
    circle_path = null;

    constructor(canvas, paper, data, document) {
        this.canvas = canvas;
        this.paper = paper;
        this.data = data;
        this.document = document;
        if (!this.canvas) {
            this.setupPaper();
        }
        this.fizzle_x = (this.paper.view.size.width / 2);
        this.fizzle_y = (this.paper.view.size.height / 2) - 200;
    }

    is_not_done_fizzling() {
        return this.fizzle_y < ((this.paper.view.size.height / 2) + 50);
    }

    sparkle(value) {
        if (this.is_not_done_fizzling()) {
            if (Math.random() > 0.5) {
                this.fizzle_y += 1;
            }
            for (var i = 0; i < (Math.floor(Math.random() * 5)); i++) {
                if (this.sparkler_lines.length < 200) {
                    var line = new SparklerLine(this.paper, this.fizzle_x, this.fizzle_y, 0, 20, Math.floor(Math.random() * 360), 50 + (Math.floor(Math.random() * 250)));
                    this.sparkler_lines.push(line);
                }
            }
        }
        for (var i = 0; i < this.sparkler_lines.length; i++) {
            if (!this.sparkler_lines[i].is_alive()) {
                if (this.is_not_done_fizzling()) {
                    this.sparkler_lines[i] = new SparklerLine(this.paper, this.fizzle_x, this.fizzle_y, 0, 20, Math.floor(Math.random() * 360), 50 + (Math.floor(Math.random() * 250)));
                }
            }
            this.sparkler_lines[i].move(value, this.fizzle_y);
        }
        this.progress += value;
        this.stick_path.removeSegments();
        this.stick_path.add(new this.paper.Point(this.paper.view.size.width / 2, this.fizzle_y));
        this.stick_path.add(new this.paper.Point(this.paper.view.size.width / 2, (this.paper.view.size.height / 2) + 50));
        this.stick_path.strokeWidth = 3;
        this.circle_path.position = new Point(this.paper.view.size.width / 2, this.fizzle_y);
        this.circle_path.bringToFront();
    }

    setupPaper() {
        var size = new this.paper.Size(600, 600)
        this.paper.setup(size);
    }

    draw() {
        var view_size = this.paper.view.size;
        var rect = new this.paper.Path.Rectangle({
            point: [0, 0],
            size: [view_size.width, view_size.height],
        });
        rect.sendToBack();
        rect.fillColor = 'black';
        this.back_stick_path = new this.paper.Path();
        this.back_stick_path.add(new this.paper.Point(this.paper.view.size.width / 2, (this.paper.view.size.height / 2) - 200));
        this.back_stick_path.add(new this.paper.Point(this.paper.view.size.width / 2, (this.paper.view.size.height / 2) + 200));
        this.back_stick_path.strokeColor = '#303030';
        this.back_stick_path.strokeWidth = 1;
        this.stick_path = new this.paper.Path();
        this.stick_path.strokeColor = '#303030';
        this.stick_path.add(new this.paper.Point(this.fizzle_x, this.fizzle_y));
        this.stick_path.add(new this.paper.Point(this.fizzle_x, this.fizzle_y + 250));
        this.stick_path.strokeWidth = 3;
        this.circle_path = new Path.Circle(new Point(this.fizzle_x, this.fizzle_y), 3);
        this.circle_path.fillColor = 'white';
    }
}

if (typeof module !== 'undefined') {
    module.exports = { Sparkler }
}
