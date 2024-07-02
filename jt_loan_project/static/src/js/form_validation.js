// Only allow number keys + number pad
$('input[name="phone"]').keypress(
    function(event) {
        if (event.keyCode == 46 || event.keyCode == 8) {
            //do nothing
        } else {
            if (event.keyCode < 48 || event.keyCode > 57) {
                event.preventDefault();
            }
        }
    }
);

//editable or not in manage account page.
$(function() {
    $("form .visible_input").attr("disabled", true);
    $(".submit_btn").attr("disabled", true);

    $(".edit_details").click(function() {
        $(".edit_details").attr("disabled", true);
        $(".visible_input").attr("disabled", false);
        $(".submit_btn").attr("disabled", false);
    });

    $(".submit_btn").click(function() {
        $(".edit_details").attr("disabled", true);
    });
});

$("#box_create_acc").on('click', function () {
    $('#hidden_box_acc').modal('show');
});
$(".o_popup_btn_close").on('click', function () {
   $('#hidden_box_acc').removeClass("d-block");
});

$(function () {
    $("#rt_toggle_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#password").attr("type", type);
    });
});

$(function () {
    $("#rt_cnfr_toggle_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#confirm_password").attr("type", type);
    });
});

$(function () {
    $("#login_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#password").attr("type", type);
    });
});