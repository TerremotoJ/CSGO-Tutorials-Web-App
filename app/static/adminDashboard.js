var flashMessages = [];
$(document).ready(function () {
  // Variable to store the currently selected data type
  var currentDataType = "users";

  $(".modal").on("hidden.bs.modal", function () {
    flashMessages = [];
  });

  // Function to retrieve users or videos data using AJAX
  function fetchData() {
    
    var url = currentDataType === "users" ? "/get_users_data" : "/get_videos_data";

    $.ajax({
      url: url,
      type: "GET",
      dataType: "json",
      success: function (data) {
        updateContent(data);
      },
      error: function (error) {
        console.error("Error fetching data:", error);
      },
    });
  }

  // Update content dynamically based on received data (users/videos)
  function updateContent(data) {

    var tableBody = $("#userTableBody");
    var tableHeaders = $("#tableHeaders");
    tableBody.empty();
    tableHeaders.empty();

    var headers = [];

    data[currentDataType].forEach(function (item) {
      var row = $("<tr>").data("user-id", item.id);
      if (currentDataType === "users") {
        headers = ["ID", "Username", "Email", "Role", "Actions"];
        row.append($("<td>").addClass("align-middle").text(item.id));
        row.append($("<td>").addClass("align-middle").text(item.username));
        row.append($("<td>").addClass("align-middle").text(item.email));
        row.append($("<td>").addClass("align-middle").text(item.role));
      } else if (currentDataType === "videos") {
        headers = [
          "ID",
          "Title",
          "URL",
          "Thumbnail",
          "Game Map",
          "Grenade",
          "Actions",
        ];
        row.append($("<td>").addClass("align-middle").text(item.id));
        row.append($("<td>").addClass("align-middle").text(item.title));
        row.append(
          $("<td>")
            .addClass("align-middle")
            .append($("<a>").attr("href", item.url).text(item.url))
        );
        row.append(
          $("<td>")
            .addClass("align-middle")
            .html(
              `<img src="${escapeHtml(item.thumbnail_url)}" alt="Thumbnail" style="max-width: 100px; max-height: 100px; " class="thumbnail-image" data-bs-toggle="modal" data-bs-target="#imageModal" data-enlarged-src="${escapeHtml(item.thumbnail_url)}">`
            )
        );
        row.append($("<td>").addClass("align-middle").text(item.game_map));
        row.append($("<td>").addClass("align-middle").text(item.grenade));
      }
      var actionsColumn = $("<td>");
      var editDiv = $("<div>").addClass("d-flex justify-content-center");
      if (currentDataType == "users") {
        editDiv.append(
          $("<a>")
            .attr("name", "Edit")
            .addClass("btn btn-info w-75")
            .attr("data-bs-toggle", "modal")
            .attr("data-bs-target", "#userModal")
            .attr("data-user-id", item.id)
            .css("width", "100%")
            .text("Edit")
        );

        var deleteDiv = $("<div>").addClass("d-flex justify-content-center");
        deleteDiv.append(
          $("<a>")
            .attr("name", "Delete")
            .addClass("btn btn-danger w-75")
            .attr("href", item.deleteUrl)
            .css("width", "100%")
            .text("Delete")
        );

      } else {
        editDiv.append(
          $("<a>")
            .attr("name", "Edit")
            .addClass("btn btn-info w-75")
            .attr("data-bs-toggle", "modal")
            .attr("data-bs-target", "#editVideoModal")
            .attr("data-video-id", item.id)
            .css("width", "100%")
            .text("Edit")
        );

        var deleteDiv = $("<div>").addClass("d-flex justify-content-center");
        deleteDiv.append(
          $("<a>")
            .attr("name", "Delete")
            .addClass("btn btn-danger w-75 deleteVideoButton")
            .attr("data-bs-toggle", "modal")
            .attr("data-bs-target", "#deleteVideoModal")
            .attr("data-video-id", item.id)
            //.attr("href", item.deleteUrl)
            .css("width", "100%")
            .text("Delete")
        );

      }


      actionsColumn.append(editDiv);
      actionsColumn.append(deleteDiv);

      row.append(actionsColumn);

      tableBody.append(row);
    });

    // Show or hide the "Add Video" button based on the selected data type
    if (currentDataType === "videos") {
      $("#tableBreak").show();
      $("#addVideoBtn").show();
    } else {
      $("#tableBreak").hide();
      $("#addVideoBtn").hide();
    }

    var headerRow = $("<tr>");
    headers.forEach(function (header) {
      headerRow.append($("<th>").text(header));
    });
    tableHeaders.append(headerRow);
  }

  // Get user data on page load
  fetchData();

  $("#videosRadio").click(function () {
    currentDataType = "videos";
    fetchData();
  });

  $("#usersRadio").click(function () {
    currentDataType = "users";
    fetchData();
  });

  // The Delete button that opened the modal carries the id of the video on its row
  document.getElementById("deleteVideoModal").addEventListener("show.bs.modal", function (event) {
    var videoId = $(event.relatedTarget).data("video-id");
    $("#deleteVideoForm").attr("action", `/delete/video/${videoId}`);
  });

  $("#confirmDeleteBtn").on("click", function () {
    $("#deleteVideoForm").submit();
  });

  $(document).on("submit", "form.needs-validation", function (event) {
    // Disable default button click behavior
    event.preventDefault();

    var formData = $(this).serialize();

    var userModal = $("#userModal");
    var userID;
    // Send form data using AJAX
    $.ajax({
      url: $(this).attr("action"),
      type: "POST",
      dataType: "json",
      data: formData,
      success: function (response) {

        flashMessages = response.flash_messages || [];
        // Update user data after successful form submission.
        userID = response.userId;

        loadUserData(userID);
      },
      error: function (error) {
        // Handle the error response (if needed)
        console.error("Error submitting form:", error);
      },
    });
  });


  $(document).on("click", "#submitEditVideo", function (event) {
    // Disable default button click behavior
    event.preventDefault();

    var formData = $(this).closest("form").serialize();

    $.ajax({
      url: $(this).closest("form").attr("action"),
      type: "POST",
      dataType: "json",
      data: formData,
      success: function (response) {

        flashMessages = response.flash_messages || [];

        if (currentDataType === "users") {
          userID = response.userId;
          loadUserData(userID);
        } else if (currentDataType === "videos") {
          videoID = response.videoId;
          loadVideoDataEdit(videoID);
        }
      },
      error: function (error) {
        // Keep the admin's edits in the form and show the reasons above it
        var messages = (error.responseJSON && error.responseJSON.flash_messages) || ["The video could not be saved."];
        var modalBody = $("#editVideoModal").find(".modal-body");
        modalBody.find(".alert").remove();
        messages.slice().reverse().forEach(function (message) {
          modalBody.prepend($("<div>").addClass("alert alert-warning").text(message));
        });
      },
    });
  });

  // Add Video
  // Triggered when clicking the "Add Video" button
  $(document).on("click", "#addVideoBtn", function () {
    flashMessages = [];
    $("#addVideoErrors").empty();
    $("#addVideoForm")[0].reset();
    $("#addVideoModal").modal("show");
  });


  $(document).on("click", "#submitAddVideo", function (event) {
    // Disable default button click behavior
    event.preventDefault();

    var form = $("#addVideoForm");

    $.ajax({
      url: form.attr("action"),
      type: "POST",
      dataType: "json",
      data: form.serialize(),
      success: function (response) {

        flashMessages = response.flash_messages || [];

        // The modal is closed after form completion
        $("#addVideoModal").modal("hide");

        // Fetch updated video data.
        fetchData();
      },
      error: function (error) {
        var messages = (error.responseJSON && error.responseJSON.flash_messages) || ["The video could not be added."];
        var errorsDiv = $("#addVideoErrors").empty();
        messages.forEach(function (message) {
          errorsDiv.append($("<div>").addClass("alert alert-warning").text(message));
        });
      },
    });
  });

  $(document).on("click", '[name="Edit"]', function () {
    var userId = $(this).closest("tr").data("user-id");
    var videoId = $(this).data("video-id");
    if (currentDataType === "users") {
      loadUserData(userId);
    } else if (currentDataType === "videos") {

      loadVideoDataEdit(videoId);
    }
  });

  // Add a click event listener for dynamically added images
  $(document).on("click", ".thumbnail-image", function () {
    var enlargedSrc = $(this).data("enlarged-src");
    $("#enlargedImage").attr("src", enlargedSrc);
  });

  var editVideoModal = document.getElementById('editVideoModal')
  editVideoModal.addEventListener('hidden.bs.modal', function (event) {
    fetchData();
  })


  var userModal = document.getElementById('userModal')
  userModal.addEventListener('hidden.bs.modal', function (event) {
    fetchData();
  })

  var deleteVideoModal = document.getElementById('deleteVideoModal')
  deleteVideoModal.addEventListener('hidden.bs.modal', function (event) {
    fetchData();
  })

  
});

function loadVideoDataEdit(videoId) {
  const csrfToken = $("meta[name=csrf-token]").attr("content");

  $.ajax({
    url: "/get_video_data/" + videoId,
    type: "GET",
    dataType: "json",
    success: function (videoData) {

      $("#editVideoModalLabel").text("Manage video - " + videoData.title);
      // Update the modal body with video details
      var modalBody = $("#editVideoModal").find(".modal-body");
      modalBody.empty();

      if (flashMessages.length > 0) {
        for (var i = 0; i < flashMessages.length; i++) {
          modalBody.append(`
                                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                                    <strong>${escapeHtml(flashMessages[i])}</strong> 
                                    <button type="button" class="close" data-bs-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                    </button>
                                </div>
                            `);
        }
      }

      modalBody.append(`
              <form method="POST" action="/edit/video/${videoId}" class="needs-validation" novalidate>
                  <input type="hidden" name="csrf_token" value="${csrfToken}"/>
          
                  <div class="mb-2">
                      <label for="title" class="form-label"><h4>Title:</h4></label>
                      <input type="text" class="form-control" id="title" name="title" value="${escapeHtml(videoData.title)}" required>
                      <div class="invalid-feedback">
                          Please enter a title.
                      </div>
                  </div>
          
                  <div class="mb-2">
                      <label for="url" class="form-label"><h4>URL:</h4></label>
                      <input type="text" class="form-control" id="url" name="url" value="${escapeHtml(videoData.url)}" required>
                      <div class="invalid-feedback">
                          Please enter a URL.
                      </div>
                  </div>
          
                  <div class="mb-2">
                      <label for="description" class="form-label"><h4>Description:</h4></label>
                      <textarea class="form-control" id="description" name="description" rows="4" cols="50">${escapeHtml(videoData.description)}</textarea>
                  </div>
          
                  <div class="mb-2">
                      <label for="notes" class="form-label"><h4>Notes:</h4></label>
                      <textarea class="form-control" id="notes" name="notes" rows="4" cols="50">${escapeHtml(videoData.notes)}</textarea>
                  </div>
          
                  <div class="mb-2 reverse-form-check">
                  <label class="reverse-form-check-label" for="is_public"><h4>Is Public:</h4></label>

                      <input type="checkbox" class="reverse-form-check-input" id="is_public" name="is_public" ${videoData.is_public ? "checked" : ""
        }>
                  </div>
          
          
                  </button>
                  <button type="button" id= "submitEditVideo" class="btn btn-primary">
                    Save changes
                  </button>
              </form>
          `);
    },
    error: function (error) {
      console.error("Error fetching video data:", error);
    },
  });
}

function loadUserData(userId) {
  const csrfToken = $("meta[name=csrf-token]").attr("content");

  $.ajax({
    url: "/get_user_data/" + userId,
    type: "GET",
    dataType: "json",
    success: function (userData) {

      var roles = userData.roles;
      var selectedRoleId = userData.selectedRoleId;
      $("#userModalLabel").text("Manage User - " + userData.username);

      var modalBody = $("#userModal").find(".modal-body");
      modalBody.empty();

      if (flashMessages.length > 0) {
        for (var i = 0; i < flashMessages.length; i++) {
          modalBody.append(`
                        <div class="alert alert-warning alert-dismissible fade show" role="alert">
                            <strong>${escapeHtml(flashMessages[i])}</strong> 
                            <button type="button" class="close" data-bs-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                    `);
        }
      }

      var roleOptions = roles.map(function (role) {
        // Check if the role ID matches the selectedRoleId
        var isSelected = selectedRoleId === role.id ? "selected" : "";
        return `<option value="${escapeHtml(role.id)}" ${isSelected}>${escapeHtml(role.name)}</option>`;
      });

      modalBody.append(`
            <form method="POST" action="/edit/user/${userId}" class="needs-validation" novalidate>
                <input type="hidden" name="csrf_token" value="${csrfToken}"/>
                
                <div class="mb-2">
                    <label for="username" class="form-label"><h4>Username:</h4></label>
                    <input type="text" class="form-control" id="username" name="username" value="${escapeHtml(userData.username)}" required>
                    <div class="invalid-feedback">
                        Please enter a username.
                    </div>
                </div>
               
                <div class="mb-2">
                    <label for="role" class="form-label"><h4>Select Role:</h4></label>
                    <select class="form-select" name="role" id="role">
                    ${roleOptions.join("")}
                    </select>
                </div>
        
                <div class="mb-2">
                    <label for="notes" class="form-label"><h4>Notes:</h4></label>
                    <textarea class="form-control" id="notes" name="notes" rows="4" cols="50">${escapeHtml(userData.notes)}</textarea>
                </div>
        
                <div class="d-flex align-items-center justify-content-center">
                    <button type="submit" class="btn btn-primary">Update User</button>
                </div>
            </form>

            
        `);
    },
    error: function (error) {
      console.error("Error fetching user data:", error);
    },
  });
}
