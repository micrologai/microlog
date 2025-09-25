version = "{microlog_version}";

object = () => { }

function load_binary(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'arraybuffer';
    xhr.onload = function() {
        if (this.status == 200) {
            var uInt8Array = new Uint8Array(this.response);
            var binaryString = '';
            for (var i = 0; i < uInt8Array.length; i++) {
                binaryString += String.fromCharCode(uInt8Array[i]);
            }
            var base64 = window.btoa(binaryString);
            callback(base64);
        } else {
            console.error("Error loading " + url + " status=" + this.status)
        }
    };
    xhr.onerror = function() {
        console.error("Network error while loading " + url)
    };
    xhr.send();
}

function optimizedDrawPolygon(context, color, lineWidth, coordinatesJson) {
    const coordinates = JSON.parse(coordinatesJson)
    context.beginPath();
    context.strokeStyle = color
    context.lineWidth = lineWidth
    var n = 0
    context.moveTo(coordinates[n], coordinates[n + 1])
    for (; n < coordinates.length; n += 2) {
        x = coordinates[n]
        y = coordinates[n + 1]
        context.lineTo(x, y)
    }
    context.stroke()
}

function optimizedFillRects(context, coordinatesJson) {
    const coordinates = JSON.parse(coordinatesJson)
    context.beginPath()
    for (var n = 0; n < coordinates.length; n += 5) {
        x = coordinates[n]
        y = coordinates[n + 1]
        w = coordinates[n + 2]
        h = coordinates[n + 3]
        context.fillStyle = coordinates[n + 4]
        context.fillRect(x, y, w, h)
    }
}

function optimizedDrawTexts(context, coordinatesJson) {
    const coordinates = JSON.parse(coordinatesJson)
    context.beginPath()
    context.strokeStyle = "red"
    for (var n = 0; n < coordinates.length; n += 5) {
        x = coordinates[n]
        y = coordinates[n + 1]
        text = coordinates[n + 2]
        color = coordinates[n + 3]
        w = coordinates[n + 4]
        context.fillStyle = color
        context.fillText(text, x, y, w)
    }
}

function optimizedDrawLines(context, lineWidth, strokeStyle, coordinatesJson) {
    const coordinates = JSON.parse(coordinatesJson)
    context.lineWidth = lineWidth
    context.strokeStyle = strokeStyle
    for (var n = 0; n < coordinates.length; n += 4) {
        context.beginPath()
        context.moveTo(coordinates[n], coordinates[n + 1])
        context.lineTo(coordinates[n + 2], coordinates[n + 3])
        context.stroke()
    }
}

function circle(context, x, y, radius, fill, lineWidth, color) {
    context.beginPath()
    context.arc(x, y, radius, 0, 2 * Math.PI)
    context.fillStyle = fill
    context.fill()
    if (lineWidth) {
        context.strokeStyle = color
        context.lineWidth = lineWidth
        context.stroke()
    }

}

// Hide the pyscript splash screen
setTimeout(() => $("py-splashscreen").text(""), 10);
setTimeout(() => $("py-splashscreen").text(""), 100);
setTimeout(() => $("py-splashscreen").text(""), 1000);

function draw_graph(json) {
    const data = JSON.parse(json);
    const nodes = new vis.DataSet(data.nodes);
    const edges = new vis.DataSet(data.edges);
    const container = document.getElementById("design-configure");
    const options = {
        configure: { enabled: false, container },
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -5000,
                centralGravity: 0.1,
                springLength: 295,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0.35,
            },
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.005,
                springConstant: 0.15,
                springLength: 100,
                damping: 0.7,
                avoidOverlap: 0.9
            },
            repulsion: {
                centralGravity: 0.2,
                springLength: 200,
                springConstant: 0.11,
                nodeDistance: 100,
                damping: 0.09
            },
            hierarchicalRepulsion: {
                centralGravity: 0.0,
                springLength: 100,
                springConstant: 0.01,
                nodeDistance: 120,
                damping: 0.09
            },
            maxVelocity: 50,
            minVelocity: 0.1,
            solver: 'barnesHut',
            stabilization: {
                enabled: true,
                iterations: 9,
                fit: true
            },
            timestep: 0.5,
            adaptiveTimestep: true
        },
        layout: {
            improvedLayout: false,
            randomSeed: 191006
        },
        nodes: {
            shapeProperties: {
                interpolation: false
            }
        }
    };
    enablePhysics = (delay) => {
        setTimeout(() => {
            options.physics.enabled = true;
            network.setOptions(options)
        }, delay)
    }
    disablePhysics = (delay) => {
        setTimeout(() => {
            options.physics.enabled = false;
            network.setOptions(options)
        }, delay)
    }
    network = new vis.Network($("#design-canvas")[0], { nodes, edges, }, options);
    network.on("dragStart", (event) => {
        if (event.nodes.length) {
            id = event.nodes[0]
            node = nodes.get(id)
            node.fixed = false;
            nodes.update([node])
        }
    })
    network.on("dragStart", (event) => {
        if (event.nodes.length) {
            enablePhysics();
        }
    })
    network.on("dragEnd", (event) => {
        if (event.nodes.length) {
            node = nodes.get(event.nodes[0])
            node.fixed = true;
            nodes.update([node])
            disablePhysics();
        }
    })
    function shake() {
        options.physics.repulsion.springLength = 50 + Math.random() * 200
        options.physics.repulsion.springConstant = 0.01 + Math.random() * 0.2
        options.physics.repulsion.nodeDistance = 50 + Math.random() * 200
        options.physics.repulsion.damping = 0.01 + Math.random() * 0.2
        network.setOptions(options)
        enablePhysics();
        disablePhysics(5000);
    }
    network.on("click", (event) => {
        shake();
    })
    network.once('afterDrawing', function () {
        network.moveTo({ x: 400, y: 400, scale: 0.9 });
    });
    network.fit();
    disablePhysics(6000);
}

$.fn.isInViewport = function() {
    const offset = $(this).offset();
    if (!offset) return true
    const elementTop = $(this).offset().top;
    const elementBottom = elementTop + $(this).outerHeight();
    const viewportTop = $(window).scrollTop() + 50;
    const viewportBottom = viewportTop + $(window).height();
    return elementBottom > viewportTop && elementTop < viewportBottom;
};
