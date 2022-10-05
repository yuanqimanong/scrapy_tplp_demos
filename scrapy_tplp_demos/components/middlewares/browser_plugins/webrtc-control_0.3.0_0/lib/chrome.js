var app = {};

app.error = function () {
    return chrome.runtime.lastError;
};

app.shortname = function () {
    return chrome.runtime.getManifest().short_name;
};

app.contextmenu = {
    "create": function (options, callback) {
        if (chrome.contextMenus) {
            chrome.contextMenus.create(options, function (e) {
                if (callback) callback(e);
            });
        }
    },
    "on": {
        "clicked": function (callback) {
            if (chrome.contextMenus) {
                chrome.contextMenus.onClicked.addListener(function (info, tab) {
                    app.storage.load(function () {
                        callback(info, tab);
                    });
                });
            }
        }
    }
};

app.options = {
    "port": null,
    "message": {},
    "receive": function (id, callback) {
        if (id) {
            app.options.message[id] = callback;
        }
    },
    "send": function (id, data) {
        if (id) {
            chrome.runtime.sendMessage({"data": data, "method": id, "path": "background-to-options"});
        }
    },
    "post": function (id, data) {
        if (id) {
            if (app.options.port) {
                app.options.port.postMessage({"data": data, "method": id, "path": "background-to-options"});
            }
        }
    }
};

app.tab = {
    "query": {
        "index": function (callback) {
            chrome.tabs.query({"active": true, "currentWindow": true}, function (tabs) {
                var tmp = chrome.runtime.lastError;
                if (tabs && tabs.length) {
                    callback(tabs[0].index);
                } else callback(undefined);
            });
        }
    },
    "open": function (url, index, active, callback) {
        var properties = {
            "url": url,
            "active": active !== undefined ? active : true
        };
        /*  */
        if (index !== undefined) {
            if (typeof index === "number") {
                properties.index = index + 1;
            }
        }
        /*  */
        chrome.tabs.create(properties, function (tab) {
            if (callback) callback(tab);
        });
    }
};

app.privacy = {
    "network": {
        "webrtc": {
            "set": function (options, callback) {
                if (chrome.privacy) {
                    if (chrome.privacy.network) {
                        if (chrome.privacy.network.webRTCIPHandlingPolicy) {
                            chrome.privacy.network.webRTCIPHandlingPolicy.set(options.alpha, function () {
                                chrome.privacy.network.webRTCIPHandlingPolicy.get({}, function (e) {
                                    if (callback) callback(e);
                                });
                            });
                        }
                        /*  */
                        if (chrome.privacy.network.webRTCMultipleRoutesEnabled) { // Deprecated since Chrome 48
                            chrome.privacy.network.webRTCMultipleRoutesEnabled.set(options.beta, function () {
                                chrome.privacy.network.webRTCMultipleRoutesEnabled.get({}, function (e) {
                                    if (callback) callback(e);
                                });
                            });
                        }
                    }
                }
            }
        }
    }
};

app.on = {
    "management": function (callback) {
        chrome.management.getSelf(callback);
    },
    "uninstalled": function (url) {
        chrome.runtime.setUninstallURL(url, function () {
        });
    },
    "installed": function (callback) {
        chrome.runtime.onInstalled.addListener(function (e) {
            app.storage.load(function () {
                callback(e);
            });
        });
    },
    "startup": function (callback) {
        chrome.runtime.onStartup.addListener(function (e) {
            app.storage.load(function () {
                callback(e);
            });
        });
    },
    "message": function (callback) {
        chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
            app.storage.load(function () {
                callback(request, sender, sendResponse);
            });
            /*  */
            return true;
        });
    }
};

app.storage = (function () {
    chrome.storage.onChanged.addListener(function () {
        chrome.storage.local.get(null, function (e) {
            app.storage.local = e;
            if (app.storage.callback) {
                if (typeof app.storage.callback === "function") {
                    app.storage.callback(true);
                }
            }
        });
    });
    /*  */
    return {
        "local": {},
        "callback": null,
        "read": function (id) {
            return app.storage.local[id];
        },
        "write": function (id, data, callback) {
            var tmp = {};
            tmp[id] = data;
            app.storage.local[id] = data;
            chrome.storage.local.set(tmp, function (e) {
                if (callback) callback(e);
            });
        },
        "load": function (callback) {
            var keys = Object.keys(app.storage.local);
            if (keys && keys.length) {
                if (callback) callback("cache");
            } else {
                chrome.storage.local.get(null, function (e) {
                    app.storage.local = e;
                    if (callback) callback("disk");
                });
            }
        }
    }
})();

app.page = {
    "port": null,
    "message": {},
    "receive": function (id, callback) {
        if (id) {
            app.page.message[id] = callback;
        }
    },
    "post": function (id, data) {
        if (id) {
            if (app.page.port) {
                app.page.port.postMessage({"data": data, "method": id, "path": "background-to-page"});
            }
        }
    },
    "send": function (id, data, tabId, frameId) {
        if (id) {
            chrome.tabs.query({}, function (tabs) {
                var tmp = chrome.runtime.lastError;
                if (tabs && tabs.length) {
                    var options = {
                        "method": id,
                        "data": data ? data : {},
                        "path": "background-to-page"
                    };
                    /*  */
                    tabs.forEach(function (tab) {
                        if (tab) {
                            options.data.tabId = tab.id;
                            options.data.top = tab.url ? tab.url : '';
                            options.data.title = tab.title ? tab.title : '';
                            /*  */
                            if (tabId && tabId !== null) {
                                if (tabId === tab.id) {
                                    if (frameId && frameId !== null) {
                                        chrome.tabs.sendMessage(tab.id, options, {"frameId": frameId});
                                    } else {
                                        chrome.tabs.sendMessage(tab.id, options);
                                    }
                                }
                            } else {
                                chrome.tabs.sendMessage(tab.id, options);
                            }
                        }
                    });
                }
            });
        }
    }
};

app.button = {
    "title": function (tabId, title, callback) {
        if (title) {
            var options = {"title": title};
            if (tabId) options["tabId"] = tabId;
            chrome.action.setTitle(options, function (e) {
                if (callback) callback(e);
            });
        }
    },
    "on": {
        "clicked": function (callback) {
            chrome.action.onClicked.addListener(function (e) {
                app.storage.load(function () {
                    callback(e);
                });
            });
        }
    },
    "icon": function (tabId, path, imageData, callback) {
        if (path && typeof path === "object") {
            var options = {"path": path};
            if (tabId) options["tabId"] = tabId;
            chrome.action.setIcon(options, function (e) {
                if (callback) callback(e);
            });
        } else if (imageData && typeof imageData === "object") {
            var options = {"imageData": imageData};
            if (tabId) options["tabId"] = tabId;
            chrome.action.setIcon(options, function (e) {
                if (callback) callback(e);
            });
        } else {
            var options = {
                "path": {
                    "16": "../data/icons/" + (path ? path + '/' : '') + "16.png",
                    "32": "../data/icons/" + (path ? path + '/' : '') + "32.png",
                    "48": "../data/icons/" + (path ? path + '/' : '') + "48.png",
                    "64": "../data/icons/" + (path ? path + '/' : '') + "64.png"
                }
            };
            /*  */
            if (tabId) options["tabId"] = tabId;
            chrome.action.setIcon(options, function (e) {
                if (callback) callback(e);
            });
        }
    }
};