
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector(".search-bar input");
    const tableRows = document.querySelectorAll("tbody tr");

    searchInput.addEventListener("keyup", function () {
        const query = searchInput.value.toLowerCase();

        tableRows.forEach(row => {
            const rowText = row.textContent.toLowerCase();
            if (rowText.includes(query)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
});


 document.getElementById("selectAll").addEventListener("change", function() {
    let checkboxes = document.querySelectorAll(".row-check");
    checkboxes.forEach(cb => cb.checked = this.checked);
  });





