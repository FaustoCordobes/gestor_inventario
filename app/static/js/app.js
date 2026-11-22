// Foco automático solo con mouse: en pantallas táctiles abriría el teclado
// o el selector nativo apenas carga la página y taparía el formulario.
(function () {
    if (!window.matchMedia("(pointer: fine)").matches) return;
    var field = document.querySelector("[data-autofocus]");
    if (field) field.focus();
})();

// Menú lateral deslizable para pantallas chicas.
(function () {
    var root = document.documentElement;
    var toggle = document.querySelector("[data-nav-toggle]");
    var scrim = document.querySelector(".scrim");
    var sidebar = document.getElementById("sidebar");
    if (!toggle || !sidebar) return;

    var mobile = window.matchMedia("(max-width: 960px)");

    function setOpen(open) {
        root.classList.toggle("nav-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
        scrim.hidden = !open;
        if (open) {
            var first = sidebar.querySelector(".menu a");
            if (first) first.focus({ preventScroll: true });
        }
    }

    toggle.addEventListener("click", function () {
        setOpen(!root.classList.contains("nav-open"));
    });

    document.querySelectorAll("[data-nav-close]").forEach(function (el) {
        el.addEventListener("click", function () {
            setOpen(false);
            toggle.focus({ preventScroll: true });
        });
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && root.classList.contains("nav-open")) {
            setOpen(false);
            toggle.focus({ preventScroll: true });
        }
    });

    // Al volver a escritorio, el menú se muestra siempre: se limpia el estado.
    mobile.addEventListener("change", function (e) {
        if (!e.matches) setOpen(false);
    });
})();
