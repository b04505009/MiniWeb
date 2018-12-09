/*
 * script.js
 * Copyright (C) 2018  <@DESKTOP-TA60DPH>
 *
 * Distributed under terms of the MIT license.
 */
$(document).ready(function() {
    $('form input').change(function() {
        var type = this.files[0].name.split(".")
        type = type[type.length - 1]
        if (type == 'pcap') {
            $('form p').text(this.files.length + " file(s) selected");
        } else {
            alert('please select a pcap file');
            $("#upload").val('');
            $('form p').text('Drag your files here or click in this area.')
        }

    });
});

function check_progress() {

    var bar = document.getElementById("pb");
    var modal = $('#myModal');
    dot = 0;
    console.log(thread_id);

    function worker() {
        $.get('status/' + thread_id, function(status) {
            console.log(status)
            console.log(dot)
            dot = dot % 4
            if (status == "nothing") {
                bar.style.width = '0%';
                modal.find('.modal-body #status_context').text("Uploading." + ".".repeat(dot));
                setTimeout(worker, 500)
            }
            if (status == "file valid") {
                bar.style.width = '0%';
                modal.find('.modal-body #status_context').text("FlowMeter running." + ".".repeat(dot));
                setTimeout(worker, 500)
            }
            if (status == "flmt") {
                bar.style.width = '50%';
                modal.find('.modal-body #status_context').text("FlowMeter finished!  Waiting for Joy running." + ".".repeat(dot));
                setTimeout(worker, 500)
            }
            if (status == "joy") {
                bar.style.width = '100%';
                setTimeout(worker, 1000)
            }
            dot = dot + 1;
        })

    }
    worker()
}

$("form#uploadform").submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);
    console.log(thread_id)
    console.log(formData)
    check_progress(thread_id);

    var ajaxRequest = $.ajax({

            type: "POST",
            url: "/checkvalid/" + thread_id,
            contentType: false,
            processData: false,
            data: formData,

            success: function(result) {
                if (result == "file valid") {
                    window.location = "/result/" + thread_id;
                } else if (result == "file not valid") {
                    alert("your file is not valid");
                    $('#myModal').modal('hide');
                    $(".modal-backdrop").remove();
                    $('form p').text('Drag your files here or click in this area.');
                } else {
                    alert("error");
                    $("#upload").val('');
                    $('form p').text('Drag your files here or click in this area.');
                }
            },
        })
        .fail(function() {
            alert("upload failed");
        });

});

function openModelResult(evt, modelName) {
    // Declare all variables
    var i, tabcontent, tablinks;
    // Get all elements with class="tabcontent" and show joy
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(modelName).style.display = "block";
    evt.currentTarget.className += " active";
}