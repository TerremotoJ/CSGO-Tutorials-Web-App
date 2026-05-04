// Escapes text before it is placed inside an HTML string; adminDashboard.js uses it too
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let currentMapFilter = "all"; // Map filter
let currentNadeFilter = null; // Grenade filter

document.addEventListener("DOMContentLoaded", function () {
  // Only the index page has the video list; the admin dashboard loads this file for escapeHtml
  if (!document.getElementById('cardsContainer')) {
    return;
  }

  const mapFilterButtons = document.querySelectorAll('.mapFilter');
  const nadeFilterButtons = document.querySelectorAll('.nadeFilter');
  const reverseSwitchCheckbox = document.getElementById('flexSwitchCheckReverse');

  mapFilterButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      const mapFilter = button.getAttribute('data-filter');

      // reset grenades if map changes
      currentNadeFilter = null;
      const grenadeFilter = currentNadeFilter; // Uses current grenade filter

      const bookmarkFilter = reverseSwitchCheckbox.checked ? 'true' : '';
      currentMapFilter = mapFilter; // Update maps filter
      updateButtonStates(); // Update button state
      fetchVideos(currentMapFilter, grenadeFilter, bookmarkFilter);
    });
  });

  nadeFilterButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      const grenadeFilter = button.getAttribute('data-filter');
      const mapFilter = currentMapFilter;
      const bookmarkFilter = reverseSwitchCheckbox.checked ? 'true' : '';
      currentNadeFilter = grenadeFilter;
      updateButtonStates();
      fetchVideos(mapFilter, currentNadeFilter, bookmarkFilter);
    });
  });


  // bookmarked filter
  reverseSwitchCheckbox.addEventListener('change', function () {
    const bookmarkFilter = reverseSwitchCheckbox.checked ? 'true' : '';
    updateButtonStates();
    fetchVideos(currentMapFilter, currentNadeFilter, bookmarkFilter);
  });


  fetchVideos(currentMapFilter, currentNadeFilter);

  attachAssistirButtonClickListeners();
});

// Function to add and remove button states
function updateButtonStates() {
  const mapFilterButtons = document.querySelectorAll('.mapFilter');
  const nadeFilterButtons = document.querySelectorAll('.nadeFilter');


  mapFilterButtons.forEach((button) => {
    button.classList.remove("active");
  });

  const activeMapButton = document.querySelector(
    `.mapFilter[data-filter="${currentMapFilter}"]`
  );
  if (activeMapButton) {
    activeMapButton.classList.add("active");
  }

  nadeFilterButtons.forEach((button) => {
    button.classList.remove("active");
  });

  const activeNadeButton = document.querySelector(
    `.nadeFilter[data-filter="${currentNadeFilter}"]`
  );
  if (activeNadeButton) {
    activeNadeButton.classList.add("active");
  }
}

function fetchVideos(mapFilter, grenadeFilter, bookmarkFilter) {

  const url = `/get_videos?map=${mapFilter || ''}&grenade=${grenadeFilter || ''}&bookmark=${bookmarkFilter || ''}`;

  // Fetch CSRF token
  const csrfToken = $('meta[name=csrf-token]').attr('content');

  fetch(url, {
    headers: {
      'X-CSRFToken': csrfToken,  // CSRF token in headers
    },
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const videos = data.videos;
      const userRole = data.userRole;
      renderVideos(videos, userRole);
      if (userRole == "Admin" || userRole == "User") {
        attachAssistirButtonClickListenersUsers();
      }
      attachBookmarkButtonClickListeners();
    })
    .catch(error => console.error('Error fetching videos:', error));
}

function renderVideos(videos, userRole) {
  const cardsContainer = document.getElementById('cardsContainer');
  cardsContainer.innerHTML = ''; // clear cards

  videos.forEach(video => {
    const isBookmarked = video.is_bookmarked;

    // Determine class by bookmark state
    const buttonClass = `btn btn-outline-dark bookmarkButton ms-auto${isBookmarked ? ' bookmarked' : ''}`;

    const iconSrc = isBookmarked ? "/static/images/bookmarked.svg" : "/static/images/bookmark.svg";



    // Limited roles get no URL in the list; the confirm modal asks /watch_video for it
    const modalButtonHtml = userRole === "Admin" || userRole === "User"
      ? `<button class="btn watchButton userWatchButton" type="button"  data-bs-toggle="modal" data-bs-target="#videoModal" data-video-url="${escapeHtml(video.url)}">
          Watch
        </button>`
      : `<button class="btn watchButton" type="button"  data-bs-toggle="modal" data-bs-target="#confirmWatchModal">
          Watch
        </button>`;

    const bookmarkButtonHtml = userRole === "Admin" || userRole === "User"
      ? `<button class="${buttonClass}" type="button" data-video-id="${escapeHtml(video.id)}">
            <img class="bookmark-icon" src="${iconSrc}" alt="Bookmark Icon">
          </button>`
      : '';

    const cardHtml = `<div class="col">
      <div class="card ${escapeHtml(video.game_map)} ${escapeHtml(video.grenade)}" data-video-id="${escapeHtml(video.id)}">
        <img src="${escapeHtml(video.thumbnail_url)}" alt="${escapeHtml(video.title)}" class="card-img-top thumbs"/>
        <div class="card-body p-2 d-flex flex-column align-items-center">
          <h5 class="card-title">${escapeHtml(video.title)}</h5>

          ${modalButtonHtml}

          ${bookmarkButtonHtml}
        </div>
      </div>
    </div>`;

    cardsContainer.innerHTML += cardHtml;
  });


}

// The server counts the view and returns the URL, or an error once the limit is reached
function requestVideoUrl(videoId) {
  const csrfToken = $('meta[name=csrf-token]').attr('content');

  return fetch(`/watch_video/${videoId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  })
    .then(response => response.json());
}


function getCurrentUserWatchInfo() {
  const url = '/check_watch_count';

  // CSRF token
  const csrfToken = $('meta[name=csrf-token]').attr('content');

  return fetch(url, {
    headers: {
      'X-CSRFToken': csrfToken,
    },
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      } else {
        return { watchedVideos: data.watched_videos, canWatch: data.can_watch, max_videos: data.max_videos };
      }
    });
}



function attachAssistirButtonClickListeners() {
  var exampleModal = document.getElementById('confirmWatchModal');
  var canWatch;
  var confirmButton = exampleModal.querySelector('#confirmButton');
  var videoId;
  var assistirButton;




  exampleModal.addEventListener('show.bs.modal', function (event) {
    // Modal button
    assistirButton = event.relatedTarget
    videoId = assistirButton.closest(".card").getAttribute("data-video-id");



    getCurrentUserWatchInfo()
      .then(info => {
        canWatch = info.canWatch;
        watchedVideos = info.watchedVideos
        max_videos = info.max_videos

        confirmButton.disabled = !canWatch;

        if (canWatch) {


          var message = `You have watched ${watchedVideos} of the ${max_videos} videos this account can watch in total. Do you want to continue?`;
          var ConfirmationMessage = exampleModal.querySelector('.modal-body #confirmationMessage');
          ConfirmationMessage.textContent = message;




        }
        else {

          var message = `You have watched ${watchedVideos} of the ${max_videos} videos this account can watch in total. This account cannot watch more videos.`;
          var ConfirmationMessage = exampleModal.querySelector('.modal-body #confirmationMessage');
          ConfirmationMessage.textContent = message;

        }


      })
      .catch(error => {
        console.error('Error fetching watched videos:', error);
      });


  })


  confirmButton.addEventListener('click', function () {
    if (canWatch) {
      var title = assistirButton.parentNode.querySelector(".card-title").textContent;

      requestVideoUrl(videoId)
        .then(data => {
          if (!data.url) {
            alert(data.error || 'This video cannot be watched.');
            return;
          }
          updateModalContent(title, data.url);

          var videoModal = new bootstrap.Modal(document.getElementById('videoModal'));
          videoModal.show();
        })
        .catch(error => console.error('Error requesting the video:', error));
    }


  });
}




// Click function for users and admins
function attachAssistirButtonClickListenersUsers() {
  var assistirButtons = document.querySelectorAll('.userWatchButton');
  assistirButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      // Videos URL
      var videoUrl = button.getAttribute("data-video-url");

      updateModalContent(
        button.parentNode.querySelector(".card-title").textContent,
        videoUrl
      );
    });
  });
}

function attachBookmarkButtonClickListeners() {
  $.ajax({
    url: '/check_bookmark_permission',
    type: 'GET',
    success: function (data) {
      if (data.can_bookmark) {
        // A user can bookmark
        var bookmarkButtons = document.querySelectorAll(".bookmarkButton");
        bookmarkButtons.forEach(function (button) {
          button.addEventListener("click", function () {
            handleBookmarkButtonClick(button);
          });
        });
      } else {
      }
    },
    error: function () {
      console.error('Error checking bookmark permission.');
    }
  });
}

function handleBookmarkButtonClick(button) {
  const videoId = button.getAttribute("data-video-id");
  const isBookmarked = button.classList.contains("bookmarked");

  const csrfToken = $('meta[name=csrf-token]').attr('content');

  button.classList.toggle("bookmarked");
  const iconSrc = isBookmarked ? "/static/images/bookmark.svg" : "/static/images/bookmarked.svg";
  button.querySelector("img").src = iconSrc;

  // AJAX request to update bookmark state in the database
  const url = '/update_bookmark_state';
  const data = { video_id: videoId, is_bookmarked: !isBookmarked };

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(data),
  })
    .then(response => response.json())
    .then(data => {

      // Update the bookmark button icon based on the bookmarked state
      const imageElement = button.querySelector(".bookmark-icon");
      const imageURL = data.is_bookmarked ? '/static/images/bookmarked.svg' : '/static/images/bookmark.svg';
      imageElement.src = imageURL;

      // Toggles "bookmarked" class based on response.
      button.classList.toggle("bookmarked", data.is_bookmarked);

      // update videos, so if a bookmark is removed inside the Bookmarked Videos filter, the video disappears
      // disabled because it causes a bug where watching a bookmarked video makes the page out of focus
      /*
      const mapFilter = currentMapFilter || 'all';
      const grenadeFilter = currentNadeFilter || '';
      const bookmarkFilter = document.getElementById('flexSwitchCheckReverse').checked ? 'true' : '';
      fetchVideos(mapFilter, grenadeFilter, bookmarkFilter);
      */

    })
    .catch(error => {
      // If fetch fails
      button.classList.toggle("bookmarked");
      const iconSrc = !isBookmarked ? "/static/images/bookmark.svg" : "/static/images/bookmarked.svg";
      button.querySelector("img").src = iconSrc;
      console.error('Error updating bookmark state:', error);
    });
}

// Function to update modal content
function updateModalContent(title, url) {
  var modalTitle = document.getElementById("videoModalLabel");
  var videoIframe = document.getElementById("videoIframe");

  modalTitle.textContent = title;
  videoIframe.src = url;
}


