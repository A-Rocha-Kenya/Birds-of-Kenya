const c = document.getElementById('table');
var res 

Papa.parse("main.csv", {
  encoding: "UTF-8",
  download: true,
  complete: function(results) {
    res = results
    console.log("Finished" );
    hot = new Handsontable(c, {
      data: results.data.slice(1),
      colHeaders: results.data[0],
      multiColumnSorting: true,
      dropdownMenu: true,
      filters: true,
      readOnly: true,
      manualColumnResize: true,
      manualColumnFreeze: true,
      dropdownMenu: ['filter_by_condition', 'filter_by_value','filter_action_bar'],
      //width: '100%',
      //height: '100%',
      licenseKey: 'non-commercial-and-evaluation',
      contextMenu: true,
      modifyColWidth: function(width, col){
        if(width > 300){
          return 300
        }
      },
      hiddenColumns: {
        columns: [6],
        indicators: true
      },
      contextMenu: ['freeze_column', 'unfreeze_column','---------','hidden_columns_hide','hidden_columns_show','---------','filter_by_value','filter_action_bar']
    });
    
  }
})

