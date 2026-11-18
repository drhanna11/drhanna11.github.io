(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector("#site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
    });
  }

  var links = document.querySelectorAll("a.js-listing-email[data-user][data-domain]");
  if (links.length) {
    var subject = "Get listed: [business name]";
    var body = [
      "Business name:",
      "Phone:",
      "Website:",
      "Cities served:",
      "Appliances repaired:",
      "Independently owned (yes/no):",
      "",
      "Anything else we should verify:",
      ""
    ].join("\n");
    var href =
      "mailto:" +
      links[0].getAttribute("data-user") +
      "@" +
      links[0].getAttribute("data-domain") +
      "?subject=" +
      encodeURIComponent(subject) +
      "&body=" +
      encodeURIComponent(body);
    links.forEach(function (a) {
      var addr = a.getAttribute("data-user") + "@" + a.getAttribute("data-domain");
      a.setAttribute("href", href);
      if (!a.classList.contains("btn")) {
        a.textContent = addr;
      }
    });
  }
})();
