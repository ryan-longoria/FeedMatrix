#include "json2.jsx"

function logMessage(level, msg) {
    var t = new Date().toISOString();
    $.writeln("[" + level + " " + t + "] " + msg);
}

function downloadFromUrl(url, localPath) {
    try {
        logMessage("INFO", "Attempting download: " + url);
        var s = new Socket();
        var urlParts = url.split("://");
        if (urlParts.length < 2) {
            throw new Error("Invalid URL format: " + url);
        }
        var hostAndPath = urlParts[1].split("/");
        var host = hostAndPath.shift();
        var path = "/" + hostAndPath.join("/");

        if (s.open(host + ":80", "BINARY")) {
            var request = "GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\n\r\n";
            s.write(request);
            var response = s.read(999999);
            s.close();
            var parts = response.split("\r\n\r\n");
            if (parts.length < 2) {
                throw new Error("Invalid HTTP response.");
            }
            var content = parts.slice(1).join("\r\n\r\n");
            var f = new File(localPath);
            if (!f.open("w")) {
                throw new Error("Failed to open local file for writing: " + localPath);
            }
            f.write(content);
            f.close();
            logMessage("INFO", "File downloaded: " + localPath);
            return true;
        } else {
            throw new Error("Unable to open socket: " + host);
        }
    } catch (e) {
        logMessage("ERROR", "Download failed: " + e.message);
        return false;
    }
}

function doJsonUpdates() {
    var presignedUrl = $.getenv("PRESIGNED_URL");
    if (!presignedUrl) {
        logMessage("WARN", "No PRESIGNED_URL found in environment. Skipping JSON updates.");
        return;
    }
    logMessage("INFO", "Got PRESIGNED_URL: " + presignedUrl);

    var localJsonPath = "C:/animeutopia/output/most_recent_post.json";
    if (!downloadFromUrl(presignedUrl, localJsonPath)) {
        logMessage("ERROR", "Failed to download JSON from " + presignedUrl);
        return;
    }

    var jsonFile = new File(localJsonPath);
    if (!jsonFile.exists) {
        logMessage("ERROR", "JSON file does not exist after download.");
        return;
    }
    jsonFile.open("r");
    var rawData = jsonFile.read();
    jsonFile.close();

    var postData;
    try {
        postData = JSON.parse(rawData);
    } catch (ex) {
        logMessage("ERROR", "JSON parse error: " + ex.message);
        return;
    }
    logMessage("INFO", "JSON loaded. Title=" + postData.title);

    if (!app.project.file) {
        logMessage("WARN", "No .aep file is open yet, skipping updates.");
        return;
    }

    var compName = "standard-news-template";
    var comp = null;
    for (var i = 1; i <= app.project.items.length; i++) {
        var it = app.project.items[i];
        if (it instanceof CompItem && it.name === compName) {
            comp = it;
            break;
        }
    }
    if (!comp) {
        logMessage("ERROR", "Comp not found: " + compName);
        return;
    }

    var titleLayer = comp.layer("Title");
    var descLayer  = comp.layer("Description");
    var bgLayer    = comp.layer("BackgroundImage");

    if (titleLayer) {
        titleLayer.property("Source Text").setValue(postData.title || "No Title");
    }
    if (descLayer) {
        descLayer.property("Source Text").setValue(postData.description || "No Description");
    }
    logMessage("INFO", "Text layers updated.");

    if (bgLayer) {
        var bgFile = new File("C:/animeutopia/output/backgroundimage_converted.jpg");
        if (bgFile.exists) {
            logMessage("INFO", "Replacing background with: " + bgFile.fsName);
            var importOpts = new ImportOptions(bgFile);
            var newFootage = app.project.importFile(importOpts);
            bgLayer.replaceSource(newFootage, false);

            var compW = comp.width, compH = comp.height;
            var lyW   = bgLayer.source.width, lyH = bgLayer.source.height;
            var scaleX = (compW / lyW) * 100;
            var scaleY = (compH / lyH) * 100;
            var scaleVal = Math.max(scaleX, scaleY);
            bgLayer.transform.scale.setValue([scaleVal, scaleVal]);
            bgLayer.transform.position.setValue([compW / 2, compH / 2]);
            logMessage("INFO", "Background replaced & scaled.");
        }
    }

    logMessage("INFO", "Dynamic JSON updates complete. The comp is updated in memory.");
}

(function main() {
    function handleProjectOpen(evt) {
        doJsonUpdates();
    }

    if (app.project.file) {
        doJsonUpdates();
    } else {
        app.eventListeners.add("afterProjectOpen", handleProjectOpen);
    }
})();
