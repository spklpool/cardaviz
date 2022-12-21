class SparklerStick {

    constructor(paper, x, y, height) {
        this.paper = paper;
        this.x = x;
        this.y = y;
        this.back_stick_path = new paper.Path();
        this.back_stick_path.add(new paper.Point(x, y));
        this.back_stick_path.add(new paper.Point(x, y + height));
        this.back_stick_path.strokeColor = '#303030';
        this.back_stick_path.strokeWidth = 1;
        this.stick_path = new paper.Path();
        this.stick_path.strokeColor = '#303030';
        this.stick_path.add(new paper.Point(x, y));
        this.stick_path.add(new paper.Point(x, y + 250));
        this.stick_path.strokeWidth = 4;
    }

    burn(burn_height) {
        this.stick_path.removeSegments();
        this.stick_path.add(new this.paper.Point(this.x, burn_height));
        this.stick_path.add(new this.paper.Point(this.x, this.y + 250));
        this.stick_path.strokeWidth = 3;
    }
}

class SparklerLine {

    constructor(paper, x, y, progress, length, angle, lifetime) {
        this.paper = paper;
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
            stops: [['white', 0.7], ['#fc6d6d', 1 - (Math.random() * 0.3)], ['white', 1 - (Math.random() * 0.3)]],
            radial: true
            },
            origin: new Point(start_x, start_y),
            destination: new Point(end_x, end_y)
        };
        linePath.add(new this.paper.Point(start_x, start_y));
        linePath.add(new this.paper.Point(end_x, end_y));
        linePath.strokeWidth = Math.floor(Math.random() * 3) + 1;
        return linePath;
    }

    is_alive() {
        return this.progress < this.lifetime;
    }

    move(progress, fizzle) {
        this.progress += progress;
        var start_x = (this.paper.view.size.width / 2) + this.progress * Math.cos(this.angle);
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
    sparkler_lines = [];

    constructor(canvas, paper, data, document) {
        this.canvas = canvas;
        this.paper = paper;
        this.data = data;
        this.document = document;
        this.fizzle_x = (this.paper.view.size.width / 2);
        this.fizzle_y = (this.paper.view.size.height / 2) - 200;
        var rect = new this.paper.Path.Rectangle({
            point: [0, 0],
            size: [this.paper.view.size.width, this.paper.view.size.height],
        });
        rect.sendToBack();
        rect.fillColor = 'black';
        this.stick = new SparklerStick(this.paper, this.paper.view.size.width / 2, (this.paper.view.size.height / 2) - 200, 400);
    }

    is_not_done_fizzling() {
        return this.fizzle_y < ((this.paper.view.size.height / 2) + 50);
    }

    spawn_a_new_bunch_of_lines() {
        for (var i = 0; i < (Math.floor(Math.random() * 5)); i++) {
            if (this.sparkler_lines.length < 200) {
                var line = new SparklerLine(this.paper, this.fizzle_x, this.fizzle_y, 0, 20, Math.floor(Math.random() * 360), 50 + (Math.floor(Math.random() * 250)));
                this.sparkler_lines.push(line);
            }
        }
    }

    fizzle() {
        if (Math.random() > 0.5) {
            this.fizzle_y += 1;
        }
    }

    move_lines(value) {
        for (var i = 0; i < this.sparkler_lines.length; i++) {
            this.sparkler_lines[i].move(value, this.fizzle_y);
        }
    }

    recycle_dead_lines() {
        for (var i = 0; i < this.sparkler_lines.length; i++) {
            if (!this.sparkler_lines[i].is_alive()) {
                if (this.is_not_done_fizzling()) {
                    this.sparkler_lines[i] = new SparklerLine(this.paper, this.fizzle_x, this.fizzle_y, 0, 20, Math.floor(Math.random() * 360), 50 + (Math.floor(Math.random() * 250)));
                }
            }
        }
    }

    sparkle(value) {
        if (this.is_not_done_fizzling()) {
            this.fizzle();
            this.spawn_a_new_bunch_of_lines();
        }
        this.recycle_dead_lines();
        this.move_lines(value);
        this.stick.burn(this.fizzle_y);
        this.progress += value;

    }
}

if (typeof module !== 'undefined') {
    module.exports = { Sparkler }
}
