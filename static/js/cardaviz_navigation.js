function draw_home(canvas) {
    var p1 = new Point(20, 200);
    var p2 = new Point(53.333, 200);
    var p3 = new Point(53.333, 140);
    var p4 = new Point(86.666, 140);
    var p5 = new Point(86.666, 200);
    var p6 = new Point(120, 200);
    var p7 = new Point(120, 123);
    var p8 = new Point(125, 125);
    var p9 = new Point(140, 125);
    var p10 = new Point(70, 80);
    var p11 = new Point(0, 125);
    var p12 = new Point(15, 125);
    var p13 = new Point(20, 123);

    var path = new paper.Path(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13);
    path.closed = true;
    path.smooth({ type: 'catmull-rom', factor: 0.6 });
    path.fillColor = 'white';
    path.scale(0.3);
    path.onMouseEnter = function (event) {
        path.fillColor = '#A9A9A9';
        canvas.style.cursor = "pointer";
    }
    path.onMouseLeave = function (event) {
        path.fillColor = 'white';
        canvas.style.cursor = "pointer";
    }
    path.onClick = function (event) {
        window.location.href = 'https://cardaviz.app/';
    }
    return path
}

function draw_back_arrow(canvas) {
    var p1 = new Point(0, 100);
    var p2 = new Point(40, 50);
    var p3 = new Point(40, 80);
    var p4 = new Point(100, 80);
    var p5 = new Point(100, 120);
    var p6 = new Point(40, 120);
    var p7 = new Point(40, 150);

    var path = new paper.Path(p1, p2, p3, p4, p5, p6, p7);
    path.closed = true;
    path.smooth({ type: 'catmull-rom', factor: 0.6 });
    path.fillColor = 'white'
    path.scale(0.3);
    path.onMouseEnter = function (event) {
        path.fillColor = '#A9A9A9';
        canvas.style.cursor = "pointer";
    }
    path.onMouseLeave = function (event) {
        path.fillColor = 'white';
        canvas.style.cursor = "default";
    }
    path.onClick = function (event) {
        history.back();
    }
    return path
}

if (typeof module !== 'undefined') {
    module.exports = { draw_back_arrow, draw_home }
}