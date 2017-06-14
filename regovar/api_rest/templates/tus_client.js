

// TUS Client for File upload

var pirusFileUpload = null;
var pirusFileInput = document.querySelector("#modal_new_file_tus_localinput");
var pirusFileAlertBox = document.querySelector("#tus_support_alert");
var pirusFileChunkInput = document.querySelector("#modal_new_file_tus_chunksize");
var pirusFileEndpointInput = document.querySelector("#modal_new_file_tus_endpoint");


if (!tus.isSupported) 
{
    pirusFileAlertBox.className = pirusFileAlertBox.className.replace("hidden", "");
}


pirusFileInput.addEventListener("change", function(e) 
{
    var file = e.target.files[0];
    console.log("selected file", file);
    var endpoint = pirusFileEndpointInput.value;
    var chunkSize = parseInt(pirusFileChunkInput.value, 10);


    if (isNaN(chunkSize)) 
    {
        chunkSize = Infinity;
    }
    var options = {
        endpoint: endpoint,
        resume: true,
        chunkSize: chunkSize,
        metadata: { filename: file.name },
        onError: function(error) 
        {
            pirusFileInput.value = "";
            buildPopup("Failed because: " + error, "alert", "tusFileProgress");
        },
        onProgress: function(bytesUploaded, bytesTotal) 
        {
            var percentage = (bytesUploaded / bytesTotal * 100).toFixed(2);
            console.log(bytesUploaded, bytesTotal, percentage + "%");
            buildProgressBar(percentage, "RUN", "modal_new_file_progress");
        },
        onSuccess: function() 
        {
            pirusFileInput.value = "";
            $("#modal_new_file_progress").html("");

        }
    }

    pirusFileUpload = new tus.Upload(file, options);
    pirusFileUpload.start();

    // fileId = pirusFileUpload.url.substr(pirusFileUpload.url.lastIndexOf('/') + 1);
    // add_new_activity_to_demo_browser("file", fileId);
    // Todo : while the upload of the file start/continue, display a form to edit file information (comments, tags, filename, ...)
})















// TUS Client for Pipeline upload

var pirusPipeUpload = null;
var pirusPipeInput = document.querySelector("#modal_new_pipeline_tus_localinput");
var pirusPipeChunkInput = document.querySelector("#modal_new_pipeline_tus_chunksize");
var pirusPipeEndpointInput = document.querySelector("#modal_new_pipeline_tus_endpoint");


pirusPipeInput.addEventListener("change", function(e) 
{
    var file = e.target.files[0];
    console.log("selected file", file);
    var endpoint = pirusPipeEndpointInput.value;
    var chunkSize = parseInt(pirusPipeChunkInput.value, 10);
    if (isNaN(chunkSize)) 
    {
        chunkSize = Infinity;
    }
    var options = {
        endpoint: endpoint,
        resume: true,
        chunkSize: chunkSize,
        metadata: { filename: file.name },
        onError: function(error) 
        {
            pirusPipeInput.value = "";
            buildPopup("Failed because: " + error, "alert", "tusPipeProgress");
        },
        onProgress: function(bytesUploaded, bytesTotal) 
        {
            var percentage = (bytesUploaded / bytesTotal * 100).toFixed(2);
            console.log(bytesUploaded, bytesTotal, percentage + "%");
            buildProgressBar(percentage, "RUN", "tusPipeProgress");
        },
        onSuccess: function() 
        {
            pirusPipeInput.value = "";
            buildPopup("Download finish !  " + pirusPipeUpload.file.name + " Will be soon installed.", "success", "tusPipeProgress");
        }
    }

    pirusPipeUpload = new tus.Upload(file, options)
    pirusPipeUpload.start()

    pipeId = pirusPipeUpload.url.substr(pirusPipeUpload.url.lastIndexOf('/') + 1);
    add_new_activity_to_demo_browser("pipeline", pipeId);
    // Todo : while the upload of the file start/continue, display a form to edit file information (comments, tags, filename, ...)
})
