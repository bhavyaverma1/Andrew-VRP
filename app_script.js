function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  // Add the 'VRP' menu
  ui.createMenu('VRP')
    .addItem('Generate Output', 'sendDataToCloudFunction')
    .addToUi();

  ui.createMenu('Route')
      .addItem('Show Map', 'showMap')
      .addToUi();
}

function showMap() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const range = sheet.getActiveRange();
  const values = range.getValues();
  
  // Set the starting point of the route.
  let url = 'https://www.google.com/maps/dir/-34.7817978,138.6462075/';

  // Add the rest of the points.
  for (let i = 0; i < values.length; i++) {
    url += values[i] + '/';
  }

  // Open the URL in a new tab.
  const htmlOutput = HtmlService.createHtmlOutput(`<a href="${url}" target="_blank">Open Map</a>`);
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'Open Map');
}

function sendDataToCloudFunction() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Input"); // Modify "Sheet1" with the actual sheet name

  var dataValues = sheet.getDataRange().getValues(); // Get all the data from the sheet
  var displayValues = sheet.getDataRange().getDisplayValues();
  var headers = dataValues[0];
  var jsonData = [];

  var settings = getSettings(ss);
  for (var i = 1; i < dataValues.length; i++) {
    var row = dataValues[i];
    var row_display = displayValues[i];
    var obj = {};

    for (var j = 0; j < headers.length; j++) {
      // est_installation_date
      if (headers[j] == 'est_installation_date' || headers[j] == 'pref_date'){
        obj[headers[j]] = row_display[j];
      }
      else{
        obj[headers[j]] = row[j];
      }
      
    }

    jsonData.push(obj);
  }

  var jsonStr = JSON.stringify(jsonData, null, 2);
  var payload = jsonStr;

  var payload = {
    settings: settings, // Add the settings variable to the payload
    data: jsonData // The existing data
  };
  var payloadStr = JSON.stringify(payload, null, 2);

  
  // Logger.log(payload);
  var url = "https://us-central1-sbos-install-ai.cloudfunctions.net/VRP-AE"; // Replace with the actual Cloud Function URL

  var options = {
    method: "post",
    contentType: "application/json",
    payload: payloadStr
  };

  var response = UrlFetchApp.fetch(url, options); // Send HTTP POST request

  // // Handle the response from the Cloud Function
  var output = JSON.parse(response.getContentText());
  var out_url = convertJSONToDataFrame(response.getContentText());
  Logger.log(out_url);
  // // Use the 'output' variable as needed

  // Logger.log(output);
}

function getSettings(ss) {
  var sheet = ss.getSheetByName("VRP Settings");
  var settingsData = sheet.getDataRange().getDisplayValues();


  // Create an object to hold the settings
  var settings = {};

  // Loop through the settings data and populate the settings object
  for (var i = 0; i < settingsData.length; i++) {
    var name = settingsData[i][0];
    var value = settingsData[i][1];
    settings[name] = value;
  }

  return settings
}







function convertJSONToDataFrame(jsonData) {
  // Parse the JSON data
  var data = JSON.parse(jsonData);

  // Create a new empty array to hold the data
  var dataArray = [];

  // Create a header row with column names
  var headerRow = [];
  for (var key in data[0]) {
    if (data[0].hasOwnProperty(key)) {
      headerRow.push(key);
    }
  }
  dataArray.push(headerRow);

  // Loop through each object in the JSON data
  for (var i = 0; i < data.length; i++) {
    var obj = data[i];
    var row = [];

    // Loop through each key in the object
    for (var key in obj) {
      if (obj.hasOwnProperty(key)) {
        row.push(obj[key]);
      }
    }

    // Add the row to the data array
    dataArray.push(row);
  }

  // Create a new spreadsheet and set the data
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet() || SpreadsheetApp.create("JSON to DataFrame");
  

  // NEW ADDITION
  // Check if the sheet already exists
  var sheetName = "Output";
  var existingSheet = spreadsheet.getSheetByName(sheetName);
  if (existingSheet) {
    // If the sheet exists, delete it
    spreadsheet.deleteSheet(existingSheet);
  }

  // Create a new sheet with the same name
  var newSheet = spreadsheet.insertSheet(sheetName);
  
  // Set the data in the new sheet
  newSheet.getRange(1, 1, dataArray.length, dataArray[0].length).setValues(dataArray);

  // Return the spreadsheet URL
  return spreadsheet.getUrl();
}
