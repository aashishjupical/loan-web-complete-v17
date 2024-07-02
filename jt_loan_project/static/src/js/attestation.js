odoo.define('jt_loan_project.attestation',[], function () {
"use strict";

    $(document).on("click", "ul.calendar_sty > li", function () {
      $('ul.calendar_sty > li.slot_li_tag').removeClass("active");
      $(this).addClass("active");
      var get_active_slot = $(".slot_li_tag.active #slot_span_tag").html();
      $('#slot_data_get').val(get_active_slot)
      $('#book_now_att').removeClass('disabled');
      $('#book_now_att').addClass('attestation-btn-color');

      $('#book_now_att').removeAttr("type").attr("type", "submit");
    });

   $("#playvideo").click(function (ev) {
        $("#video1")[0].src += "?controls=0&amp;autoplay=1";
        ev.preventDefault();
        setTimeout(function(){ $('#watch-ac').removeClass('disabled');
        $('#watch-ac').removeAttr("type").attr("type", "submit");
         }, 273000);
        
    });
  $("#cover").click(function (ev) {
        $("#video1")[0].src += "?controls=0&amp;autoplay=1";
        ev.preventDefault();
        ev.preventDefault();
        setTimeout(function(){ $('#watch-ac').removeClass('disabled');
        $('#watch-ac').removeAttr("type").attr("type", "submit");
         }, 273000);

  });
});