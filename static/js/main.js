function applySavedTheme(){
    if(localStorage.getItem("supporthub-theme")==="dark"){
        document.body.classList.add("dark-mode");
    }
}

function toggleDarkMode(){
    document.body.classList.toggle("dark-mode");
    localStorage.setItem("supporthub-theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
}

function resetTheme(){
    localStorage.setItem("supporthub-theme","light");
    document.body.classList.remove("dark-mode");
}

applySavedTheme();
