var background = (function () {
    var tmp = {};
    chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
        for (var id in tmp) {
            if (tmp[id] && (typeof tmp[id] === "function")) {
                if (request.path === "background-to-page") {
                    if (request.method === id) tmp[id](request.data);
                }
            }
        }
    });
    /*  */
    return {
        "receive": function (id, callback) {
            tmp[id] = callback
        },
        "send": function (id, data) {
            chrome.runtime.sendMessage({"path": "page-to-background", "method": id, "data": data})
        }
    }
})();

var config = {
    "update": function (e) {
        if (e.state === "enabled") {
            var script = {};
            /*  */
            if (e.devices) {
                script.a = document.getElementById("webrtc-control-a");
                /*  */
                if (!script.a) {
                    script.a = document.createElement("script");
                    script.a.type = "text/javascript";
                    script.a.setAttribute("id", "webrtc-control-a");
                    script.a.onload = function () {
                        script.a.remove()
                    };
                    script.a.src = chrome.runtime.getURL("data/content_script/page_context/media_devices.js");
                    /*  */
                    document.documentElement.appendChild(script.a);
                }
            }
            /*  */
            if (e.inject) {
                script.b = document.getElementById("webrtc-control-b");
                /*  */
                if (!script.b) {
                    script.b = document.createElement("script");
                    script.b.type = "text/javascript";
                    script.b.setAttribute("id", "webrtc-control-b");
                    script.b.onload = function () {
                        script.b.remove()
                    };
                    script.b.src = chrome.runtime.getURL("data/content_script/page_context/support_detection.js");
                    /*  */
                    document.documentElement.appendChild(script.b);
                }
            }
        }
    }
};

background.send("load");
background.receive("storage", config.update);
