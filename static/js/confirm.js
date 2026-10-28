// Ask before submitting a form marked with data-confirm (deleting things).
// Without JavaScript the form still works; this only adds a safety check.
document.addEventListener("submit", function (event) {
  var form = event.target;
  var question = form.getAttribute && form.getAttribute("data-confirm");
  if (question && !window.confirm(question)) {
    event.preventDefault();
  }
});
