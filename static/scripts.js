// Update displayed interval value as slider is changed.
function updateInterval() {
			var val = document.getElementById("interval-range").value;
			document.getElementById("interval-display").innerHTML = val;
		};


// Enable interval slider when radio button is selected and change scores value to Publication year.
function toggleInterval(flag) {
	if (flag) {
		document.getElementById("interval-range").removeAttribute("disabled");
		document.getElementById("value").value = "py";
	} else {
		document.getElementById("interval-range").setAttribute("disabled", "true");
	}
};


// Display list of selected filenames below upload button.
function showFileName(event) {
	var input = event.srcElement;
	var fileNames = input.files;
	var fileList = "<ul>"

	for (let i = 0; i < fileNames.length; i++) {
		fileList += "<li>" + fileNames[i].name + "</li>";
	};

	fileList += "</ul>";

	fileArea.innerHTML = fileList;
};

// Clear list of filenames when form is reset.
function clearFileName() {
	fileArea.innerHTML = "";
};

var fileInput = document.getElementById('input');
var fileArea = document.getElementById('file-list');
var formReset = document.getElementById('reset-form');

fileInput.addEventListener('change', showFileName);
formReset.addEventListener('click', clearFileName);


// Update list of scores values based on availability

var database = document.getElementById('db');
var scoresValues = document.getElementById('value');

function updateAvailability() {
	for (let i = 0; i < scoresValues.length; i++) {
		if (!scores_dict[this.value]) {
			scoresValues[i].removeAttribute('disabled');

		} else if (scores_dict[this.value].includes(scoresValues[i].value)) {
			scoresValues[i].removeAttribute('disabled');

		} else {
			scoresValues[i].setAttribute('disabled', 'disabled');
		};
	};
};

database.addEventListener('change', updateAvailability);
