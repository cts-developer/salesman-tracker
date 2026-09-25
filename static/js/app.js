// Salesman Tracker — core front-end behaviour

document.addEventListener('DOMContentLoaded', function () {
  // Sidebar toggle (mobile)
  var burger = document.getElementById('stBurger');
  var sidebar = document.getElementById('stSidebar');
  var overlay = document.getElementById('stOverlay');

  function closeSidebar() {
    sidebar && sidebar.classList.remove('show');
    overlay && overlay.classList.remove('show');
  }

  if (burger && sidebar && overlay) {
    burger.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      overlay.classList.toggle('show');
    });
    overlay.addEventListener('click', closeSidebar);
  }

  // Auto-dismiss alerts
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(function (el) {
    setTimeout(function () {
      el.classList.remove('show');
      el.classList.add('fade');
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });
});

// Capture GPS location into hidden lat/lng inputs and show status text.
function stCaptureLocation(latFieldId, lngFieldId, statusId) {
  var statusEl = document.getElementById(statusId);
  if (!navigator.geolocation) {
    if (statusEl) statusEl.innerHTML = '<span class="text-danger">Geolocation is not supported by this browser.</span>';
    return;
  }
  if (statusEl) statusEl.innerHTML = '<span class="text-muted-st">Fetching your location&hellip;</span>';

  navigator.geolocation.getCurrentPosition(
    function (position) {
      var lat = position.coords.latitude.toFixed(6);
      var lng = position.coords.longitude.toFixed(6);
      document.getElementById(latFieldId).value = lat;
      document.getElementById(lngFieldId).value = lng;
      if (statusEl) {
        statusEl.innerHTML = '<span class="st-badge active"><span class="st-dot"></span>Location captured (' + lat + ', ' + lng + ')</span>';
      }
    },
    function (error) {
      if (statusEl) statusEl.innerHTML = '<span class="text-danger">Could not fetch location: ' + error.message + '</span>';
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}
