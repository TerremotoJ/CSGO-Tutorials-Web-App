$(document).ready(function () {
  $("#username").on("input", function (event) {
    //  $('#checkAvailabilityBtn').on('click', function (event) {
    event.preventDefault();
    var username = $("#username").val();

    // Loading spinner
    $("#usernameAvailability").html(
      '<div class="spinner-border text-secondary" role="status"> <span class="visually-hidden">Loading...</span> </div>'
    );

    $.ajax({
      type: "POST",
      url: "/check_username_availability",
      data: {
        username: username,
        csrf_token: $('input[name="csrf_token"]').val(), // CSRF token
      },
      success: function (response) {
        // Hide spinner
        $("#usernameAvailability").empty();

        if (response.available) {
          $("#usernameAvailability").html(
            '<div class="spinner-grow text-success" role="status"><span class="visually-hidden">Loading...</span></div>'
          );
        } else {
          // Red spinner if not available
          $("#usernameAvailability").html(
            '<div class="spinner-grow text-danger" role="status"><span class="visually-hidden">Loading...</span></div>'
          );
        }
      },
    });
  });
});
