class ColorDispenser {
    static initial_colors = Array(
                    {"normal": "#aa7777", "highlighted": "#dd0000"},
                    {"normal": "#77aa77", "highlighted": "#00dd00"},
                    {"normal": "#7777aa", "highlighted": "#0000dd"},
                    {"normal": "#aaaa77", "highlighted": "#dddd00"},
                    {"normal": "#aa77aa", "highlighted": "#dd00dd"},
                    {"normal": "#77aaaa", "highlighted": "#00dddd"}
                );
    static remaining_colors = [];

    static getNextColor() {
        if (this.remaining_colors.length == 0) {
            this.remaining_colors = [...this.initial_colors];
        }
        return this.remaining_colors.shift();
    }
}

class PaperSankeyDiagramConstants {
    static band_width = 300;
    static spacer_length = 15;
    static end_of_band_width = 10;
}

class CardanoTreasuryBandData {
    constructor(address, color) {
        this.address = address;
        this.color = color;
    }
}

class CardanoTreasuryBandDetailData {
    constructor(gov_action_proposal_id, color) {
        this.gov_action_proposal_id = gov_action_proposal_id;
        this.color = color;
    }
}

class PaperSankeyDiagramBand {
    child_bands = [];
    child_bands_data = [];
    constructor(id, top_left_x, top_left_y, top_right_x, top_right_y, left_thickness, right_thickness, color, label, amount) {
        this.id = id;
        this.top_left_x = top_left_x;
        this.top_left_y = top_left_y;
        this.top_right_x = top_right_x;
        this.top_right_y = top_right_y;
        this.left_thickness = left_thickness;
        this.right_thickness = right_thickness;
        this.color = color;
        this.label = label;
        this.amount = amount;
        this.band_path = this.draw(top_left_x, top_left_y, top_right_x, top_right_y, left_thickness, right_thickness, this.color);
        this.band_path.onMouseEnter = () => this.on_mouse_enter();
        this.band_path.onMouseLeave = () => this.on_mouse_leave();
        this.band_path.onClick = () => this.on_band_click();
    }

    draw(top_left_x, top_left_y, top_right_x, top_right_y, left_thickness, right_thickness, color) {
        var band_group = new paper.Group();
        band_group.addChild(this.draw_cubic_bezier_band(top_left_x, top_left_y, top_right_x, top_right_y, left_thickness, right_thickness, color));
        band_group.addChild(this.draw_end_of_band_solid_rectangle(top_right_x, top_right_y, right_thickness, color));
        return band_group;
    }

    draw_left_justified_text(x, y, text, rotation, fontSize, color) {
        var ret = new paper.PointText({
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
        ret.translate(new Point(ret.strokeBounds.width/2, ret.bounds.height/2));
        return ret;
    }

    draw_cubic_bezier_band(top_left_x, top_left_y, top_right_x, top_right_y, left_thickness, right_thickness, color) {
        var band_path = new paper.Path();
        var fromPoint = new paper.Point(top_left_x, top_left_y);
        band_path.add(fromPoint);
        this.addTopCubicCurveToBandPath(band_path, top_left_x, top_left_y, top_right_x, top_right_y);
        band_path.add(top_right_x, top_right_y + right_thickness);
        this.addBottomCubicCurveToBandPath(band_path, top_left_x, top_left_y + left_thickness, top_right_x, top_right_y + right_thickness);
        band_path.closed = true;
        band_path.fillColor = color['normal'];
        band_path.strokeColor = band_path.fillColor;
        return band_path;
    }

    addTopCubicCurveToBandPath(band_path, from_x, from_y, to_x, to_y) {
        var toPoint = new paper.Point(to_x, to_y);
        var handle1 = new paper.Point(from_x + (PaperSankeyDiagramConstants.band_width / 2), from_y);
        var handle2 = new paper.Point(to_x - (PaperSankeyDiagramConstants.band_width / 2), to_y);
        band_path.cubicCurveTo(handle1, handle2, toPoint);
    }

    addBottomCubicCurveToBandPath(band_path, to_x, to_y, from_x, from_y) {
        var toPoint = new paper.Point(to_x, to_y);
        var handle1 = new paper.Point(from_x - (PaperSankeyDiagramConstants.band_width / 2), from_y);
        var handle2 = new paper.Point(to_x + (PaperSankeyDiagramConstants.band_width / 2), to_y);
        band_path.cubicCurveTo(handle1, handle2, toPoint);
    }

    draw_end_of_band_solid_rectangle(top_right_x, top_right_y, thickness, color) {
        var band_tip_path = new paper.Path();
        band_tip_path.add(top_right_x, top_right_y);
        band_tip_path.add(top_right_x, top_right_y + thickness);
        band_tip_path.add(top_right_x + PaperSankeyDiagramConstants.end_of_band_width, top_right_y + thickness);
        band_tip_path.add(top_right_x + PaperSankeyDiagramConstants.end_of_band_width, top_right_y);
        band_tip_path.closed = true;
        band_tip_path.fillColor = color['highlighted'];
        band_tip_path.strokeColor = band_tip_path.fillColor;
        return band_tip_path;
    }

    add_mouse_listener(callback) {
        this.mouse_listener_callback = callback;
    }

    on_mouse_enter() {
        this.mouse_listener_callback.on_band_mouse_enter(this.id);
    }

    on_mouse_leave() {
        this.mouse_listener_callback.on_band_mouse_leave(this.id);
    }

    on_band_click() {
        this.mouse_listener_callback.on_band_mouse_click(this.id);
    }
}

class CardanoTreasuryDetailsPaperSankeyDiagramBandMouseEventListener {
    child_bands = [];
    child_bands_data = [];

    constructor(canvas, child_bands, child_bands_data) {
        this.canvas = canvas;
        this.bands = child_bands;
        this.bands_data = child_bands_data;
    }

    on_band_mouse_enter(id) {
        this.bands[id].band_path.children[0].fillColor = this.bands[id].color['highlighted'];
        this.bands[id].band_path.children[0].strokeColor = this.bands[id].band_path.children[0].fillColor;
        this.canvas.style.cursor = "pointer";
    }

    on_band_mouse_leave(id) {
        this.bands[id].band_path.children[0].fillColor = this.bands[id].color['normal'];
        this.bands[id].band_path.children[0].strokeColor = this.bands[id].band_path.children[0].fillColor;
        this.canvas.style.cursor = "default";
    }

    on_band_mouse_click(id) {
        console.log('details click id: ' + id + ' gov_action_proposal_id: ' + this.bands_data[id].gov_action_proposal_id);
        this.fetch_band_details(this.bands_data[id].gov_action_proposal_id);
    }

    treasury_withdrawal_details_json = null;
    fetch_band_details(id) {
        var url = '/gov_action_votes/' + id;
        console.log('fetching vote details json for ' + id + ' from ' + url);
        fetch(url)
        .then(function (response) {
            return response.json();
        })
        .then(data => this.process_data_for_band(id, data));
    }

    process_data_for_band(id, data) {
        console.log('process_data_for_band: ' + id);
        console.log(data);
    }
}

class CardanoTreasuryPaperSankeyDiagramBandMouseEventListener {
    child_bands = [];
    child_bands_data = [];

    constructor(diagram) {
        this.diagram = diagram;
    }

    on_band_mouse_enter(id) {
        this.diagram.bands[id].band_path.children[0].fillColor = this.diagram.bands[id].color['highlighted'];
        this.diagram.bands[id].band_path.strokeColor = this.diagram.bands[id].band_path.children[0].fillColor;
        this.diagram.canvas.style.cursor = "pointer";
    }

    on_band_mouse_leave(id) {
        this.diagram.bands[id].band_path.children[0].fillColor = this.diagram.bands[id].color['normal'];
        this.diagram.bands[id].band_path.strokeColor = this.diagram.bands[id].band_path.children[0].fillColor;
        this.diagram.canvas.style.cursor = "default";
    }

    on_band_mouse_click(id) {
        this.child_bands.forEach((item) => {
            item.band_path.remove();
        });
        this.child_bands = [];
        this.child_bands_data = [];
        this.fetch_band_details(this.diagram.bands[id], this.diagram.band_data[id], this.diagram.canvas);
    }

    treasury_withdrawal_details_json = null;
    fetch_band_details(band, band_data, canvas) {
        var treasury_withdrawals_url = '/treasury_withdrawal_details/' + band_data.address;
        console.log('fetching treasury withdrawal details json for ' + band_data.address + ' from ' + treasury_withdrawals_url);
        fetch(treasury_withdrawals_url)
        .then(function (response) {
            return response.json();
        })
        .then(data => this.process_data_for_band(data, band, canvas));
    }

    process_data_for_band(data, band, canvas) {
        this.treasury_withdrawal_details_json = data;
        var total_details_amount = 0;
        var new_band_current_y_left = band.top_right_y;
        var new_band_current_y_right = PaperSankeyDiagramConstants.spacer_length;
        var new_band_current_y_origin_right = PaperSankeyDiagramConstants.spacer_length;
        for (var i = 0; i < this.treasury_withdrawal_details_json.length; i++) {
            total_details_amount += this.treasury_withdrawal_details_json[i]['amount'];
        }
        this.detail_band_mouse_event_listener = new CardanoTreasuryDetailsPaperSankeyDiagramBandMouseEventListener(canvas, this.child_bands, this.child_bands_data);
        var total_right_height_with_spaces = this.diagram.window_height - (this.treasury_withdrawal_details_json.length * PaperSankeyDiagramConstants.spacer_length) - (2 * PaperSankeyDiagramConstants.spacer_length);
        for (var i = 0; i < this.treasury_withdrawal_details_json.length; i++) {
            var new_band_left_height = (band.right_thickness/total_details_amount) * this.treasury_withdrawal_details_json[i]['amount'];
            var new_band_right_height = (total_right_height_with_spaces/total_details_amount) * this.treasury_withdrawal_details_json[i]['amount'];
            var band_color = ColorDispenser.getNextColor();
            var current_band = new PaperSankeyDiagramBand(i, band.top_right_x + PaperSankeyDiagramConstants.end_of_band_width, new_band_current_y_left, band.top_right_x + (band.top_right_x - band.top_left_x), new_band_current_y_right, new_band_left_height, new_band_right_height, band_color, this.treasury_withdrawal_details_json[i]['label'], this.treasury_withdrawal_details_json[i]['amount']);
            this.child_bands.push(current_band);
            var data = new CardanoTreasuryBandDetailData();
            data.gov_action_proposal_id = this.treasury_withdrawal_details_json[i]['label']
            this.child_bands_data.push(data);
            current_band.add_mouse_listener(this.detail_band_mouse_event_listener);
            data.color = band_color;
            new_band_current_y_left += new_band_left_height;
            new_band_current_y_right += new_band_right_height + PaperSankeyDiagramConstants.spacer_length;
            new_band_current_y_origin_right += new_band_right_height;
        }
    }
}

class HighlightingPaperSankeyDiagramBandMouseEventListener {
    child_bands = [];
    child_bands_data = [];

    constructor(diagram) {
        this.diagram = diagram;
    }

    on_band_mouse_enter(id) {
        this.diagram.bands[id].band_path.children[0].fillColor = this.diagram.bands[id].color['highlighted'];
        this.diagram.bands[id].band_path.strokeColor = this.diagram.bands[id].band_path.children[0].fillColor;
    }

    on_band_mouse_leave(id) {
        this.diagram.bands[id].band_path.children[0].fillColor = this.diagram.bands[id].color['normal'];
        this.diagram.bands[id].band_path.strokeColor = this.diagram.bands[id].band_path.children[0].fillColor;
    }

    on_band_mouse_click(id) {
    }
}

class ChildrenHighlightingPaperSankeyDiagramBandMouseEventListener {
    constructor(children) {
        this.children = children;
    }

    on_band_mouse_enter(id) {
        this.children[id].band_path.children[0].fillColor = this.children[id].color['highlighted'];
        this.children[id].band_path.strokeColor = this.children[id].band_path.children[0].fillColor;
    }

    on_band_mouse_leave(id) {
        this.children[id].band_path.children[0].fillColor = this.children[id].color['normal'];
        this.children[id].band_path.strokeColor = this.children[id].band_path.children[0].fillColor;
    }

    on_band_mouse_click(id) {
        console.log(this.children[id].label);
    }
}

class PaperSankeyDiagram {
    minumum_bands = 4;
    maximum_bands = 9;
    bands_by_depth = [];
    leafs_by_depth = [];
    total_bands_by_depth = [];
    bands = [];
    band_data = [];
    total_amount = 0;
    total_amount_leaves = 0;
    leaves_count = 0;
    current_y = 0;
    normalized_data = null;
    left_band_origin = 0;
    scaling_factor = 1;
    total_spacers_height = 0;
    drawing_height_without_spacers = 0;
    max_depth = 0;

    constructor(canvas, data, left_offset, top_offset, diagram_width, window_height) {
        this.data = data;
        this.canvas = canvas;
        this.left_offset = left_offset;
        this.top_offset = top_offset;
        this.diagram_width = diagram_width;
        this.window_height = window_height;
        this.left_band_origin = this.left_offset - PaperSankeyDiagramConstants.end_of_band_width;
        this.current_y = this.top_offset;
        this.normalized_data = this.replace_small_amounts_with_other(data);
        this.total_drawing_height = window_height - (top_offset * 2);
        this.band_mouse_event_listener = new HighlightingPaperSankeyDiagramBandMouseEventListener(this);
    }

    draw() {
        this.drawLeftRectangle(this.top_offset);
        this.preDrawingCalculations();
        this.draw_left_justified_text(30, 50, 'total withdrawals: ' + this.total_amount, 0, 16, 'red');
        this.drawBands();
    }

    drawBands() {
        for (var i = 0; i < this.normalized_data.length; i++) {
            var iteration_length = (this.total_drawing_height/this.total_amount) * this.normalized_data[i]['amount'];
            var band_color = ColorDispenser.getNextColor();
            var current_band = new PaperSankeyDiagramBand(i, this.left_offset, this.current_y_origin, this.left_offset + this.diagram_width, this.current_y, iteration_length, iteration_length, band_color, this.normalized_data[i]['label'], this.normalized_data[i]['amount']);
            current_band.add_mouse_listener(this.band_mouse_event_listener);
            var current_band_data = new CardanoTreasuryBandData(this.normalized_data[i]['label'], band_color);
            this.band_data.push(current_band_data);
            this.bands.push(current_band);
            this.current_y += iteration_length + PaperSankeyDiagramConstants.spacer_length;
            this.current_y_origin += iteration_length;
        }
    }

    addTotalAmountOfData(data) {
        var ret = 0;
        for (var i = 0; i < data.length; i++) {
            ret += data[i]['amount'];
        }
        return ret;
    }

    preDrawingCalculations() {
        this.total_amount = this.addTotalAmountOfData(this.normalized_data);
        this.calculateRecursively(1, this.normalized_data);
        this.total_spacers_height = (this.leaves_count + 2) * PaperSankeyDiagramConstants.spacer_length;
        this.drawing_height_without_spacers = this.total_drawing_height - this.total_spacers_height;
        this.scaling_factor = this.drawing_height_without_spacers / this.total_amount_leaves;
        this.start_y = this.total_spacers_height / 2;
        this.start_y_origin = this.start_y;
    }

    calculateRecursively(depth, data) {
        if (depth > this.max_depth) this.max_depth = depth;
        if (this.bands_by_depth[depth - 1]) {
            this.bands_by_depth[depth - 1] += data.length;
        } else {
            this.bands_by_depth[depth - 1] = data.length;
        }
        if (!this.leafs_by_depth[depth - 1]) {
            this.leafs_by_depth[depth - 1] = 0;
        }
        for (var i = 0; i < data.length; i++) {
            if (data[i]['children']) {
                this.calculateRecursively(depth + 1, data[i]['children']);
            } else {
                this.total_amount_leaves += data[i].amount;
                this.leaves_count ++;
                this.leafs_by_depth[depth - 1] ++;
            }
        }
        var cummulative_leafs = 0;
        for (var i=1; i<depth; i++) {
            cummulative_leafs += this.leafs_by_depth[i-1];
        }
        this.total_bands_by_depth[depth - 1] = this.bands_by_depth[depth - 1] + cummulative_leafs;
    }

    drawLeftRectangle(top_offset) {
        this.current_y_origin = top_offset;
        var total_amount_path_p1 = new Point(this.left_band_origin, this.current_y_origin);
        var total_amount_path_p2 = new Point(this.left_band_origin + PaperSankeyDiagramConstants.end_of_band_width, this.current_y_origin);
        var total_amount_path_p3 = new Point(this.left_band_origin + PaperSankeyDiagramConstants.end_of_band_width, this.current_y_origin + this.total_drawing_height);
        var total_amount_path_p4 = new Point(this.left_band_origin, this.current_y_origin + this.total_drawing_height);
        var total_amount_path = new paper.Path(total_amount_path_p1, total_amount_path_p2, total_amount_path_p3, total_amount_path_p4);
        total_amount_path.closed = true;
        total_amount_path.strokeColor = 'grey';
        total_amount_path.fillColor = 'grey';
        total_amount_path.strokeWidth = 1;
    }

    replace_small_amounts_with_other(data) {
        if (data.length < this.minumum_bands) return data;
        var ret = [];
        var other_amount = 0;
        for (var i = 0; i < data.length; i++) {
            if (i < this.maximum_bands){
                ret.push(data[i]);
            } else {
                other_amount += data[i]['amount'];
            }
        }
        if (other_amount > 0) {
            ret.push({amount: other_amount, label: 'other'});
        }
        return ret;
    }

    draw_left_justified_text(x, y, text, rotation, fontSize, color) {
        var ret = new paper.PointText({
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
        ret.translate(new Point(ret.strokeBounds.width/2, ret.bounds.height/2-4));
        return ret;
    }
}

class CardanoTreasuryPaperSankeyDiagram extends PaperSankeyDiagram {

    //
    //  sample data
    //  [{"amount": 20, "label": "label1"}, {"amount": 80, "label": "label2"}]
    //
    constructor(canvas, data, left_offset, top_offset, diagram_width, window_height) {
        super(canvas, data, left_offset, top_offset, diagram_width, window_height);
        this.band_mouse_event_listener = new CardanoTreasuryPaperSankeyDiagramBandMouseEventListener(this);
        this.draw();
    }

    draw() {
        this.drawLeftRectangle(this.top_offset);
        this.preDrawingCalculations();
        this.drawTreasuryIcon(new Point(70, (this.top_offset * 2) + (this.total_drawing_height/2)));
        this.draw_left_justified_text(30, 50, 'total withdrawals: ' + this.total_amount, 0, 16, 'red');
        this.drawBands();
    }

    drawTreasuryIcon(location) {
        var p1 = new Point(20, 200);
        var p2 = new Point(10, 200);
        var p3 = new Point(10, 210);
        var p4 = new Point(0, 210);
        var p5 = new Point(0, 220);
        var p6 = new Point(140, 220);
        var p7 = new Point(140, 210);
        var p8 = new Point(130, 210);
        var p9 = new Point(130, 200);
        var p10 = new Point(120, 200);
        var p11 = new Point(120, 200);
        var p12 = new Point(120, 125);
        var p13 = new Point(140, 125);
        var p14 = new Point(70, 80);
        var p15 = new Point(0, 125);
        var p16 = new Point(20, 125);
    
        var path1 = new paper.Path(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16);
        path1.closed = true;
        path1.strokeWidth = 1;
    
        var p26 = new Point(35, 125);
        var p27 = new Point(35, 200);
        var p28 = new Point(62.5, 200);
        var p29 = new Point(62.5, 125);
     
        var path2 = new paper.Path(p26, p27, p28, p29);
        path2.strokeWidth = 1;
        path2.closed = true;
    
        var p32 = new Point(77.5, 125);
        var p33 = new Point(77.5, 200);
        var p34 = new Point(105, 200);
        var p35 = new Point(105, 125);
        var path3 = new paper.Path(p32, p33, p34, p35);
    
        path3.strokeWidth = 1;
        path3.closed = true;
        
        var compoundPath = new CompoundPath();
        compoundPath.addChild(path1);
    
        var combinedPath = compoundPath.subtract(path2, { insert: false }).subtract(path3, { insert: false });
        combinedPath.strokeColor = 'grey';
        combinedPath.fillColor = 'grey';
        
    
        path1.remove();
        path2.remove();
        path3.remove();

        combinedPath.translate(new Point(location.x, location.y - (combinedPath.bounds.height/2)));
        combinedPath.addTo(project.activeLayer);
    
        return combinedPath;
    }
}

class CardanoGenesisPaperSankeyDiagram extends PaperSankeyDiagram {
    child_bands = [];
    child_bands_data = [];

    //
    //  sample data
    //  [{"amount": 20, "label": "label1"}, {"amount": 80, "label": "label2"}]
    //
    constructor(canvas, data, left_offset, top_offset, diagram_width, window_height) {
        super(canvas, data, left_offset, top_offset, diagram_width, window_height);
        this.normalized_data = data;
        this.draw();
    }

    draw() {
        this.preDrawingCalculations();
        var initial_depth_spacer_height = this.total_spacers_height / (data.length + 1);
        this.drawBandsRecursively(1, this.left_offset, this.start_y_origin + (initial_depth_spacer_height / 2), this.normalized_data, this.child_bands, this.child_bands_data);
        this.drawLabelsRecursively(this.child_bands);
    }

    drawLabelsRecursively(bands) {
        for (var i=0; i<bands.length; i++) {
            this.draw_left_justified_text(bands[i].top_left_x + PaperSankeyDiagramConstants.spacer_length, bands[i].top_right_y + (bands[i].right_thickness / 2), bands[i].label + ': ' + bands[i].amount, 0, 16, 'white');
            this.drawLabelsRecursively(bands[i].child_bands);
        }
    }

    drawBandsRecursively(depth, start_x, start_y, data, bands, band_data) {
        console.log('depth: ' + depth + ' bands: ' + this.total_bands_by_depth[depth - 1]);
        var child_band_listener = new ChildrenHighlightingPaperSankeyDiagramBandMouseEventListener(bands);
        var current_y_left = start_y;
        var this_depth_spacer_height = this.total_spacers_height / (this.total_bands_by_depth[depth - 1] + 1);
        var current_y_right = current_y_left - (((this.total_bands_by_depth[depth - 1] - 1) * this_depth_spacer_height) / 2);
        for (var i = 0; i < data.length; i++) {
            var iteration_length = data[i]['amount'] * this.scaling_factor;
            var band_color = ColorDispenser.getNextColor();
            var this_band_width = PaperSankeyDiagramConstants.band_width;
            if (!data[i].children) this_band_width = PaperSankeyDiagramConstants.band_width * (this.max_depth - depth + 1);
            console.log(data[i]['label']);
            console.log('max_depth: ' + this.max_depth);
            console.log('depth: ' + depth);
            console.log('this_band_width: ' + this_band_width);
            var current_band = new PaperSankeyDiagramBand(i, start_x, current_y_left, start_x + this_band_width, current_y_right, iteration_length, iteration_length, band_color, data[i]['label'], data[i]['amount']);
            current_band.add_mouse_listener(child_band_listener);
            var current_band_data = new CardanoTreasuryBandData(data[i]['label'], band_color);
            band_data.push(current_band_data);
            bands.push(current_band);
            if (data[i].children) {
                this.drawBandsRecursively(depth + 1, start_x + PaperSankeyDiagramConstants.band_width + PaperSankeyDiagramConstants.end_of_band_width, current_y_right, data[i].children, current_band.child_bands, current_band.child_bands_data);
            }
            current_y_left += iteration_length;
            current_y_right += iteration_length + this_depth_spacer_height;
        }
    }
}

if (typeof module !== 'undefined') {
    module.exports = { PaperSankeyDiagram, PaperSankeyDiagramBand }
}
