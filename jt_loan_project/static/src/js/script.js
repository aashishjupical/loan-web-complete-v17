// odoo.define('jt_loan_project.script', function (require) {
odoo.define('jt_loan_project.script',[], function () {
    'use strict'
    $('#upload-file').change(function () {
        var filename = $(this).val();
        $('#file-upload-name').html(filename);
        if (filename != "") {
            setTimeout(function () {
                $('.upload-wrapper').addClass("uploaded");
            }, 600);
            setTimeout(function () {
                $('.upload-wrapper').removeClass("uploaded");
                $('.upload-wrapper').addClass("success");
            }, 1600);
        }
    });
    

    // upload and show id start
    var btnUpload = $("#upload_file"),
        btnOuter = $(".button_outer");
    btnUpload.on("change", function (e) {
        var ext = btnUpload.val().split('.').pop().toLowerCase();
        if ($.inArray(ext, ['gif', 'png', 'jpg', 'jpeg']) == -1) {
            $(".error_msg").text("Not an Image...");
        } else {
            $(".error_msg").text("");
            btnOuter.addClass("file_uploading");
            setTimeout(function () {
                btnOuter.addClass("file_uploaded");
            }, 3000);
            var uploadedFile = URL.createObjectURL(e.target.files[0]);
            setTimeout(function () {
                $("#uploaded_view").append('<img src="' + uploadedFile + '" />').addClass("show");
            }, 3500);
        }
    });
    $(".file_remove").on("click", function (e) {
        $("#uploaded_view").removeClass("show");
        $("#uploaded_view").find("img").remove();
        btnOuter.removeClass("file_uploading");
        btnOuter.removeClass("file_uploaded");
    });
    
    // '/per_emergency_info' this page selection code

    $('#selection_option').change(function () {
        // $('#per_emg_btn').prop("disabled", true);
        var selectVal = $(this).val();
        
        if (selectVal == "Select Relationship") {
           $('#per_emg_btn').prop("disabled", true);
        } else {
           $('#per_emg_btn').prop("disabled", false);
        }
    });

});